"""Order registration, pricing, specimen planning, and payment workflows."""

import uuid
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from sqlmodel import Session, col, select

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.lis import (
    Analyte,
    AnalyteResult,
    AuditAction,
    AuditLog,
    Catalog,
    CatalogItemAnalyte,
    CatalogPanelItem,
    CatalogSpecimenRequirement,
    CatalogType,
    CustomerCredit,
    Doctor,
    DoctorCommissionAdjustment,
    DoctorCommissionConfig,
    DoctorCommissionEntry,
    InsurancePricing,
    InsuranceProvider,
    Invoice,
    InvoiceBalanceTransfer,
    Order,
    OrderAnalyteDetailPublic,
    OrderCancelRequest,
    OrderCatalogItemAnalyte,
    OrderCreate,
    OrderDetailPublic,
    OrderItem,
    OrderItemAnalyteCustomizeRequest,
    OrderItemDetailPublic,
    OrderItemSpecimen,
    OrderListItemPublic,
    OrderPreviewItemPublic,
    OrderPreviewPublic,
    OrderPreviewRequest,
    OrderPreviewSpecimenPublic,
    OrderRevision,
    OrderRevisionPublic,
    OrderRevisionsPublic,
    OrderSpecimen,
    OrderSpecimenDetailPublic,
    OrderStatus,
    OrderUpdate,
    Patient,
    PatientContext,
    PatientInsurance,
    PaymentCollect,
    PaymentMethod,
    PaymentRefund,
    PaymentStatus,
    PaymentTransaction,
    PaymentTransactionPublic,
    PaymentTransactionStatus,
    PayoutStatus,
    SortOrder,
    SpecimenStatus,
    SpecimenType,
    Unit,
)
from app.repositories import order as order_repo
from app.services import commission as commission_service
from app.services import finance_settings as finance_settings_service

MONEY = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _active(model, message: str):
    if model is None or getattr(model, "is_deleted", False):
        raise BusinessRuleError(message)
    return model


def _validate_context(
    *, session: Session, context_id: uuid.UUID | None
) -> PatientContext | None:
    if context_id is None:
        return None
    return _active(
        session.get(PatientContext, context_id),
        "Contexte patient non disponible",
    )


def _validate_header(
    *, session: Session, request: OrderPreviewRequest
) -> tuple[Patient, Doctor | None, PatientInsurance | None, InsuranceProvider | None]:
    patient = _active(
        session.get(Patient, request.patient_id),
        "Patient non disponible",
    )
    doctor = None
    if request.doctor_id is not None:
        doctor = _active(
            session.get(Doctor, request.doctor_id),
            "Médecin non disponible",
        )
    insurance = None
    provider = None
    if request.patient_insurance_id is not None:
        insurance = session.get(PatientInsurance, request.patient_insurance_id)
        if (
            insurance is None
            or insurance.is_deleted
            or insurance.patient_id != patient.id
        ):
            raise BusinessRuleError("Assurance non disponible pour ce patient")
        provider = _active(
            session.get(InsuranceProvider, insurance.insurance_provider_id),
            "Assureur non disponible",
        )
    _validate_context(session=session, context_id=request.patient_context_id)
    return patient, doctor, insurance, provider


def _expand_catalog(
    *,
    session: Session,
    catalog_ids: list[uuid.UUID],
    allowed_unavailable_ids: set[uuid.UUID] | None = None,
) -> tuple[dict[uuid.UUID, Catalog], dict[uuid.UUID, set[uuid.UUID]]]:
    allowed_unavailable_ids = allowed_unavailable_ids or set()
    selected: dict[uuid.UUID, Catalog] = {}
    sources: dict[uuid.UUID, set[uuid.UUID]] = {}
    for selected_id in dict.fromkeys(catalog_ids):
        catalog = session.get(Catalog, selected_id)
        if catalog is None or (
            (catalog.is_deleted or not catalog.is_orderable)
            and selected_id not in allowed_unavailable_ids
        ):
            raise BusinessRuleError(
                "Une entrée catalogue sélectionnée n'est pas disponible"
            )
        if catalog.type == CatalogType.item:
            selected[catalog.id] = catalog
            sources.setdefault(catalog.id, set()).add(catalog.id)
            continue
        panel_rows = session.exec(
            select(CatalogPanelItem, Catalog)
            .join(Catalog, CatalogPanelItem.test_id == Catalog.id)
            .where(CatalogPanelItem.panel_id == catalog.id)
            .order_by(col(CatalogPanelItem.sort_order).asc())
        ).all()
        if not panel_rows:
            raise BusinessRuleError(f"Le panel {catalog.name} ne contient aucun test")
        for _, test in panel_rows:
            if (
                test.is_deleted or not test.is_orderable
            ) and test.id not in allowed_unavailable_ids:
                raise BusinessRuleError(
                    f"Le test {test.name} du panel {catalog.name} n'est pas disponible"
                )
            selected[test.id] = test
            sources.setdefault(test.id, set()).add(catalog.id)
    return selected, sources


def preview_order(
    *,
    session: Session,
    request: OrderPreviewRequest,
    can_override_prices: bool,
    can_discount: bool,
    can_collect_payment: bool,
    allowed_unavailable_ids: set[uuid.UUID] | None = None,
) -> OrderPreviewPublic:
    _, _, _, provider = _validate_header(session=session, request=request)
    tests, sources = _expand_catalog(
        session=session,
        catalog_ids=request.catalog_ids,
        allowed_unavailable_ids=allowed_unavailable_ids,
    )
    overrides = {item.catalog_id: item for item in request.line_overrides}
    if overrides and not can_override_prices:
        raise BusinessRuleError("Vous ne pouvez pas modifier les prix")
    unknown_overrides = set(overrides) - set(tests)
    if unknown_overrides:
        raise BusinessRuleError(
            "Une modification de prix cible un test non sélectionné"
        )
    if request.discount > 0 and not can_discount:
        raise BusinessRuleError("Vous ne pouvez pas appliquer de remise")
    if request.discount > 0 and not (request.discount_reason or "").strip():
        raise BusinessRuleError("Le motif de remise est requis")
    if request.initial_payment is not None and not can_collect_payment:
        raise BusinessRuleError("Vous ne pouvez pas encaisser de paiement")

    requested_analytes = {
        item.catalog_id: item.analyte_ids for item in request.item_analytes
    }
    if set(requested_analytes) - set(tests):
        raise BusinessRuleError(
            "Une personnalisation d'analytes cible un test non sélectionné"
        )
    items: list[OrderPreviewItemPublic] = []
    for test in tests.values():
        charged = test.price
        insured = False
        provider_name = None
        if provider is not None:
            pricing = session.exec(
                select(InsurancePricing).where(
                    InsurancePricing.insurance_provider_id == provider.id,
                    InsurancePricing.catalog_id == test.id,
                )
            ).first()
            if pricing is not None:
                charged = pricing.insurance_price
                insured = True
                provider_name = provider.name
        override = overrides.get(test.id)
        if override is not None:
            charged = override.price_charged
        analytes = _resolve_analytes(
            session=session,
            catalog_id=test.id,
            analyte_ids=requested_analytes.get(test.id),
        )
        items.append(
            OrderPreviewItemPublic(
                catalog_id=test.id,
                catalog_code=test.code,
                catalog_name=test.name,
                catalog_price=_money(test.price),
                price_charged=_money(charged),
                is_covered_by_insurance=insured,
                insurance_provider_name=provider_name,
                price_override_reason=override.reason.strip() if override else None,
                source_catalog_ids=sorted(sources[test.id], key=str),
                analytes=[
                    _analyte_detail(analyte=analyte, sort_order=index)
                    for index, (_, analyte, _) in enumerate(analytes)
                ],
            )
        )

    specimen_map: dict[uuid.UUID, dict] = {}
    requirements = session.exec(
        select(CatalogSpecimenRequirement, SpecimenType)
        .join(
            SpecimenType,
            CatalogSpecimenRequirement.specimen_type_id == SpecimenType.id,
        )
        .where(CatalogSpecimenRequirement.catalog_id.in_(list(tests)))
    ).all()
    for requirement, specimen_type in requirements:
        entry = specimen_map.setdefault(
            specimen_type.id,
            {
                "type": specimen_type,
                "volume": None,
                "instructions": [],
                "catalog_ids": [],
            },
        )
        if requirement.volume_ml is not None:
            entry["volume"] = max(
                entry["volume"] or Decimal("0"), requirement.volume_ml
            )
        instruction = (requirement.instructions or "").strip()
        if instruction and instruction not in entry["instructions"]:
            entry["instructions"].append(instruction)
        entry["catalog_ids"].append(requirement.catalog_id)

    specimens = [
        OrderPreviewSpecimenPublic(
            specimen_type_id=specimen_id,
            specimen_type_name=data["type"].name,
            specimen_type_color=data["type"].color,
            required_volume_ml=data["volume"],
            collection_instructions="; ".join(data["instructions"]) or None,
            catalog_ids=data["catalog_ids"],
        )
        for specimen_id, data in specimen_map.items()
    ]
    total = _money(sum((item.price_charged for item in items), Decimal("0")))
    discount = _money(request.discount)
    if discount > total:
        raise BusinessRuleError("La remise ne peut pas dépasser le total")
    net = _money(total - discount)
    payment = (
        _money(request.initial_payment.amount)
        if request.initial_payment is not None
        else Decimal("0.00")
    )
    if payment > net:
        raise BusinessRuleError("Le paiement ne peut pas dépasser le montant net")
    if request.initial_payment is not None:
        method = session.get(PaymentMethod, request.initial_payment.payment_method_id)
        if method is None or method.is_deleted:
            raise BusinessRuleError("Méthode de paiement non disponible")

    return OrderPreviewPublic(
        items=items,
        specimens=specimens,
        total_amount=total,
        discount=discount,
        net_amount=net,
        initial_payment_amount=payment,
        balance_due=_money(net - payment),
    )


def _next_accession(*, session: Session) -> str:
    today = datetime.now(timezone.utc).date()
    value = order_repo.next_daily_value(
        session=session, sequence_date=today, sequence_type="order"
    )
    return f"ORD-{today:%Y%m%d}-{value:04d}"


def suggest_patient_identifier(*, session: Session) -> str:
    today = datetime.now(timezone.utc).date()
    value = order_repo.next_daily_value(
        session=session, sequence_date=today, sequence_type="patient"
    )
    session.commit()
    return f"PAT-{today:%Y%m%d}-{value:04d}"


def create_order(
    *,
    session: Session,
    request: OrderCreate,
    created_by_id: uuid.UUID,
    can_override_prices: bool,
    can_discount: bool,
    can_collect_payment: bool,
) -> Order:
    preview = preview_order(
        session=session,
        request=request,
        can_override_prices=can_override_prices,
        can_discount=can_discount,
        can_collect_payment=can_collect_payment,
    )
    order = order_repo.create(
        session=session,
        db_obj=Order(
            accession_number=_next_accession(session=session),
            patient_id=request.patient_id,
            doctor_id=request.doctor_id,
            patient_insurance_id=request.patient_insurance_id,
            patient_context_id=request.patient_context_id,
            notes=(request.notes or "").strip() or None,
            created_by=created_by_id,
        ),
    )
    item_by_catalog: dict[uuid.UUID, OrderItem] = {}
    for index, item in enumerate(preview.items):
        order_item = order_repo.create(
            session=session,
            db_obj=OrderItem(
                order_id=order.id,
                catalog_id=item.catalog_id,
                catalog_price=item.catalog_price,
                price_charged=item.price_charged,
                price_override_reason=item.price_override_reason,
                is_covered_by_insurance=item.is_covered_by_insurance,
                insurance_provider_name=item.insurance_provider_name,
                sort_order=index,
                source_catalog_ids=[str(value) for value in item.source_catalog_ids],
            ),
        )
        item_by_catalog[item.catalog_id] = order_item
        for analyte_detail in item.analytes:
            attachment = session.exec(
                select(CatalogItemAnalyte).where(
                    CatalogItemAnalyte.catalog_item_id == item.catalog_id,
                    CatalogItemAnalyte.analyte_id == analyte_detail.analyte_id,
                )
            ).first()
            order_repo.create(
                session=session,
                db_obj=OrderCatalogItemAnalyte(
                    order_item_id=order_item.id,
                    analyte_id=analyte_detail.analyte_id,
                    catalog_item_analyte_id=attachment.id if attachment else None,
                    sort_order=analyte_detail.sort_order,
                ),
            )

    specimen_by_type: dict[uuid.UUID, OrderSpecimen] = {}
    for specimen in preview.specimens:
        specimen_by_type[specimen.specimen_type_id] = order_repo.create(
            session=session,
            db_obj=OrderSpecimen(
                order_id=order.id,
                specimen_type_id=specimen.specimen_type_id,
                status=SpecimenStatus.pending,
                required_volume_ml=specimen.required_volume_ml,
                collection_instructions=specimen.collection_instructions,
            ),
        )
    for specimen in preview.specimens:
        order_specimen = specimen_by_type[specimen.specimen_type_id]
        for catalog_id in specimen.catalog_ids:
            order_repo.create(
                session=session,
                db_obj=OrderItemSpecimen(
                    order_item_id=item_by_catalog[catalog_id].id,
                    order_specimen_id=order_specimen.id,
                ),
            )

    from app.services import billing as billing_service

    invoice = order_repo.create(
        session=session,
        db_obj=Invoice(
            order_id=order.id,
            invoice_number=billing_service.next_invoice_number(session=session),
            total_amount=preview.total_amount,
            discount=preview.discount,
            discount_reason=(request.discount_reason or "").strip() or None,
            net_amount=preview.net_amount,
            amount_paid=Decimal("0.00"),
            payment_status=PaymentStatus.unpaid,
            created_by_id=created_by_id,
        ),
    )
    billing_service.create_lines(session=session, invoice=invoice)
    if request.initial_payment is not None:
        order_repo.create(
            session=session,
            db_obj=PaymentTransaction(
                invoice_id=invoice.id,
                amount=preview.initial_payment_amount,
                payment_method_id=request.initial_payment.payment_method_id,
                collected_by_id=created_by_id,
            ),
        )
        order_repo.recalculate_invoice_payment(session=session, invoice=invoice)

    if request.doctor_id is not None:
        today = date.today()
        config = session.exec(
            select(DoctorCommissionConfig)
            .where(
                DoctorCommissionConfig.doctor_id == request.doctor_id,
                DoctorCommissionConfig.effective_from <= today,
                (
                    (DoctorCommissionConfig.effective_until == None)  # noqa: E711
                    | (DoctorCommissionConfig.effective_until >= today)
                ),
            )
            .order_by(col(DoctorCommissionConfig.effective_from).desc())
        ).first()
        finance_settings = finance_settings_service.get_settings(
            session=session
        )
        if config is not None:
            insured_rate = config.insurance_commission_rate
            non_insured_rate = config.commission_rate
        elif (
            finance_settings.default_commission_rate is not None
            and finance_settings.default_insurance_commission_rate is not None
        ):
            insured_rate = finance_settings.default_insurance_commission_rate
            non_insured_rate = finance_settings.default_commission_rate
        else:
            insured_rate = None
            non_insured_rate = None

        if insured_rate is not None and non_insured_rate is not None:
            policy = finance_settings.discount_allocation_policy
            snapshot = commission_service.calculate_commission(
                lines=[
                    (item.price_charged, item.is_covered_by_insurance)
                    for item in preview.items
                ],
                discount=preview.discount,
                insured_rate=insured_rate,
                non_insured_rate=non_insured_rate,
                policy=policy,
            )
            if snapshot.commission_amount > 0:
                order_repo.create(
                    session=session,
                    db_obj=commission_service.apply_snapshot(
                        entry=DoctorCommissionEntry(
                            order_id=order.id,
                            doctor_id=request.doctor_id,
                            order_net_amount=snapshot.order_net_amount,
                            insured_net_amount=snapshot.insured_net_amount,
                            insured_rate_applied=snapshot.insured_rate_applied,
                            insured_commission_amount=(
                                snapshot.insured_commission_amount
                            ),
                            non_insured_net_amount=snapshot.non_insured_net_amount,
                            non_insured_rate_applied=(
                                snapshot.non_insured_rate_applied
                            ),
                            non_insured_commission_amount=(
                                snapshot.non_insured_commission_amount
                            ),
                            discount_allocation_policy=(
                                snapshot.discount_allocation_policy
                            ),
                            commission_amount=snapshot.commission_amount,
                            payout_status=PayoutStatus.pending,
                        ),
                        snapshot=snapshot,
                    ),
                )
    session.commit()
    session.refresh(order)
    return order


def _snapshot_order(
    *, order: Order, items: list[tuple[OrderItem, Catalog]], invoice: Invoice
) -> dict:
    return {
        "patient_id": str(order.patient_id),
        "doctor_id": str(order.doctor_id) if order.doctor_id else None,
        "patient_insurance_id": (
            str(order.patient_insurance_id) if order.patient_insurance_id else None
        ),
        "patient_context_id": (
            str(order.patient_context_id) if order.patient_context_id else None
        ),
        "status": order.status.value,
        "notes": order.notes,
        "catalog_ids": [str(item.catalog_id) for item, _ in items],
        "items": [
            {
                "id": str(item.id),
                "catalog_id": str(item.catalog_id),
                "catalog_code": catalog.code,
                "catalog_name": catalog.name,
                "catalog_price": str(item.catalog_price),
                "price_charged": str(item.price_charged),
                "price_override_reason": item.price_override_reason,
                "is_covered_by_insurance": item.is_covered_by_insurance,
                "insurance_provider_name": item.insurance_provider_name,
            }
            for item, catalog in items
        ],
        "discount": str(invoice.discount),
        "net_amount": str(invoice.net_amount),
        "amount_paid": str(invoice.amount_paid),
        "payment_status": invoice.payment_status.value,
        "invoice_id": str(invoice.id),
        "invoice_version": invoice.version,
    }


def _analyte_detail(
    *,
    analyte: Analyte,
    sort_order: int,
    unit: Unit | None = None,
    has_result: bool = False,
    has_verified_result: bool = False,
) -> OrderAnalyteDetailPublic:
    return OrderAnalyteDetailPublic(
        analyte_id=analyte.id,
        analyte_code=analyte.code,
        analyte_name=analyte.name,
        analyte_data_type=analyte.data_type,
        unit_name=unit.name if unit else None,
        sort_order=sort_order,
        has_result=has_result,
        has_verified_result=has_verified_result,
    )


def _resolve_analytes(
    *,
    session: Session,
    catalog_id: uuid.UUID,
    analyte_ids: list[uuid.UUID] | None,
) -> list[tuple[CatalogItemAnalyte | None, Analyte, Unit | None]]:
    if analyte_ids is None:
        return list(
            session.exec(
                select(CatalogItemAnalyte, Analyte, Unit)
                .join(Analyte, CatalogItemAnalyte.analyte_id == Analyte.id)
                .join(Unit, Analyte.unit_id == Unit.id, isouter=True)
                .where(
                    CatalogItemAnalyte.catalog_item_id == catalog_id,
                    Analyte.is_deleted == False,  # noqa: E712
                )
                .order_by(col(CatalogItemAnalyte.sort_order).asc())
            ).all()
        )
    if len(analyte_ids) != len(set(analyte_ids)):
        raise BusinessRuleError("Un analyte ne peut être ajouté qu'une seule fois")
    if not analyte_ids:
        return []
    rows = list(
        session.exec(
            select(Analyte, Unit)
            .join(Unit, Analyte.unit_id == Unit.id, isouter=True)
            .where(
                Analyte.id.in_(analyte_ids),
                Analyte.is_deleted == False,  # noqa: E712
            )
        ).all()
    )
    by_id = {analyte.id: (analyte, unit) for analyte, unit in rows}
    if set(analyte_ids) != set(by_id):
        raise BusinessRuleError("Un analyte sélectionné n'est pas disponible")
    attachments = {
        attachment.analyte_id: attachment
        for attachment in session.exec(
            select(CatalogItemAnalyte).where(
                CatalogItemAnalyte.catalog_item_id == catalog_id,
                CatalogItemAnalyte.analyte_id.in_(analyte_ids),
            )
        ).all()
    }
    return [
        (attachments.get(analyte_id), *by_id[analyte_id])
        for analyte_id in analyte_ids
    ]


def _get_order_analytes(
    *, session: Session, item_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[OrderAnalyteDetailPublic]]:
    if not item_ids:
        return {}
    result_rows = list(
        session.exec(
            select(AnalyteResult).where(
                AnalyteResult.order_item_id.in_(item_ids),
                AnalyteResult.is_superseded == False,  # noqa: E712
            )
        ).all()
    )
    result_keys = {(result.order_item_id, result.analyte_id) for result in result_rows}
    verified_keys = {
        (result.order_item_id, result.analyte_id)
        for result in result_rows
        if result.status == "verified"
    }
    rows = session.exec(
        select(OrderCatalogItemAnalyte, Analyte, Unit)
        .join(Analyte, OrderCatalogItemAnalyte.analyte_id == Analyte.id)
        .join(Unit, Analyte.unit_id == Unit.id, isouter=True)
        .where(
            OrderCatalogItemAnalyte.order_item_id.in_(item_ids),
            OrderCatalogItemAnalyte.is_active == True,  # noqa: E712
        )
        .order_by(
            col(OrderCatalogItemAnalyte.order_item_id).asc(),
            col(OrderCatalogItemAnalyte.sort_order).asc(),
        )
    ).all()
    grouped: dict[uuid.UUID, list[OrderAnalyteDetailPublic]] = {}
    for snapshot, analyte, unit in rows:
        key = (snapshot.order_item_id, analyte.id)
        grouped.setdefault(snapshot.order_item_id, []).append(
            _analyte_detail(
                analyte=analyte,
                unit=unit,
                sort_order=snapshot.sort_order,
                has_result=key in result_keys,
                has_verified_result=key in verified_keys,
            )
        )
    return grouped


def _apply_item_analytes(
    *,
    session: Session,
    item: OrderItem,
    analyte_ids: list[uuid.UUID],
    revision: OrderRevision,
    reason: str,
) -> tuple[int, int, int]:
    resolved = _resolve_analytes(
        session=session,
        catalog_id=item.catalog_id,
        analyte_ids=analyte_ids,
    )
    existing = {
        snapshot.analyte_id: snapshot
        for snapshot in session.exec(
            select(OrderCatalogItemAnalyte).where(
                OrderCatalogItemAnalyte.order_item_id == item.id
            )
        ).all()
    }
    desired = set(analyte_ids)
    added = 0
    restored = 0
    removed = 0
    for snapshot in existing.values():
        if snapshot.analyte_id in desired:
            continue
        if snapshot.is_active:
            snapshot.is_active = False
            snapshot.removed_revision_id = revision.id
            snapshot.removal_reason = reason
            session.add(snapshot)
            removed += 1
            for result in session.exec(
                select(AnalyteResult).where(
                    AnalyteResult.order_item_id == item.id,
                    AnalyteResult.analyte_id == snapshot.analyte_id,
                    AnalyteResult.is_superseded == False,  # noqa: E712
                )
            ).all():
                result.is_superseded = True
                result.superseded_revision_id = revision.id
                session.add(result)
    for index, (attachment, analyte, _unit) in enumerate(resolved):
        snapshot = existing.get(analyte.id)
        if snapshot is None:
            order_repo.create(
                session=session,
                db_obj=OrderCatalogItemAnalyte(
                    order_item_id=item.id,
                    analyte_id=analyte.id,
                    catalog_item_analyte_id=attachment.id if attachment else None,
                    sort_order=index,
                ),
            )
            added += 1
            continue
        if not snapshot.is_active:
            restored += 1
        snapshot.is_active = True
        snapshot.sort_order = index
        snapshot.catalog_item_analyte_id = attachment.id if attachment else None
        snapshot.removed_revision_id = None
        snapshot.removal_reason = None
        session.add(snapshot)
    return added, restored, removed


def _create_order_item(
    *,
    session: Session,
    order_id: uuid.UUID,
    preview_item: OrderPreviewItemPublic,
    sort_order: int,
    revision_id: uuid.UUID | None,
) -> OrderItem:
    item = order_repo.create(
        session=session,
        db_obj=OrderItem(
            order_id=order_id,
            catalog_id=preview_item.catalog_id,
            catalog_price=preview_item.catalog_price,
            price_charged=preview_item.price_charged,
            price_override_reason=preview_item.price_override_reason,
            is_covered_by_insurance=preview_item.is_covered_by_insurance,
            insurance_provider_name=preview_item.insurance_provider_name,
            sort_order=sort_order,
            revision_id=revision_id,
            source_catalog_ids=[
                str(value) for value in preview_item.source_catalog_ids
            ],
        ),
    )
    for analyte_detail in preview_item.analytes:
        attachment = session.exec(
            select(CatalogItemAnalyte).where(
                CatalogItemAnalyte.catalog_item_id == preview_item.catalog_id,
                CatalogItemAnalyte.analyte_id == analyte_detail.analyte_id,
            )
        ).first()
        order_repo.create(
            session=session,
            db_obj=OrderCatalogItemAnalyte(
                order_item_id=item.id,
                analyte_id=analyte_detail.analyte_id,
                catalog_item_analyte_id=attachment.id if attachment else None,
                sort_order=analyte_detail.sort_order,
            ),
        )
    return item


def add_reflex_catalog(
    *,
    session: Session,
    order: Order,
    catalog_id: uuid.UUID,
    performed_by_id: uuid.UUID,
) -> set[uuid.UUID]:
    """Idempotently add a reflex catalog selection and reissue billing."""
    existing_rows = order_repo.get_items(session=session, order_id=order.id)
    existing_ids = {item.catalog_id for item, _ in existing_rows}
    tests, sources = _expand_catalog(session=session, catalog_ids=[catalog_id])
    missing = [test for test in tests.values() if test.id not in existing_ids]
    if not missing:
        return set()

    invoice = order_repo.get_invoice(session=session, order_id=order.id)
    if invoice is None:
        raise NotFoundError("Facture active non trouvée")
    provider = None
    if order.patient_insurance_id is not None:
        insurance = session.get(PatientInsurance, order.patient_insurance_id)
        if insurance is not None:
            provider = session.get(
                InsuranceProvider, insurance.insurance_provider_id
            )
    revision = order_repo.create(
        session=session,
        db_obj=OrderRevision(
            order_id=order.id,
            revision_number=order.revision_number + 1,
            correction_reason="Ajout automatique par règle réflexe",
            old_values=_snapshot_order(
                order=order, items=existing_rows, invoice=invoice
            ),
            new_values={},
            effects={"reflex_catalog_id": str(catalog_id)},
            performed_by_id=performed_by_id,
        ),
    )
    order.revision_number = revision.revision_number
    session.add(order)
    next_sort = max((item.sort_order for item, _ in existing_rows), default=-1) + 1
    added: dict[uuid.UUID, OrderItem] = {}
    for offset, test in enumerate(missing):
        charged = test.price
        insured = False
        provider_name = None
        if provider is not None:
            pricing = session.exec(
                select(InsurancePricing).where(
                    InsurancePricing.insurance_provider_id == provider.id,
                    InsurancePricing.catalog_id == test.id,
                )
            ).first()
            if pricing is not None:
                charged = pricing.insurance_price
                insured = True
                provider_name = provider.name
        added[test.id] = _create_order_item(
            session=session,
            order_id=order.id,
            preview_item=OrderPreviewItemPublic(
                catalog_id=test.id,
                catalog_code=test.code,
                catalog_name=test.name,
                catalog_price=_money(test.price),
                price_charged=_money(charged),
                is_covered_by_insurance=insured,
                insurance_provider_name=provider_name,
                source_catalog_ids=sorted(sources[test.id], key=str),
                analytes=[
                    _analyte_detail(analyte=analyte, unit=unit, sort_order=index)
                    for index, (_attachment, analyte, unit) in enumerate(
                        _resolve_analytes(
                            session=session,
                            catalog_id=test.id,
                            analyte_ids=None,
                        )
                    )
                ],
            ),
            sort_order=next_sort + offset,
            revision_id=revision.id,
        )
        added[test.id].is_reflex_added = True
        session.add(added[test.id])

    active_specimens = list(
        session.exec(
            select(OrderSpecimen).where(
                OrderSpecimen.order_id == order.id,
                OrderSpecimen.is_superseded == False,  # noqa: E712
            )
        ).all()
    )
    by_type = {specimen.specimen_type_id: specimen for specimen in active_specimens}
    requirements = session.exec(
        select(CatalogSpecimenRequirement).where(
            CatalogSpecimenRequirement.catalog_id.in_(list(added))
        )
    ).all()
    for requirement in requirements:
        specimen = by_type.get(requirement.specimen_type_id)
        if specimen is None:
            specimen = order_repo.create(
                session=session,
                db_obj=OrderSpecimen(
                    order_id=order.id,
                    specimen_type_id=requirement.specimen_type_id,
                    status=SpecimenStatus.pending,
                    required_volume_ml=requirement.volume_ml,
                    collection_instructions=requirement.instructions,
                ),
            )
            by_type[specimen.specimen_type_id] = specimen
        order_repo.create(
            session=session,
            db_obj=OrderItemSpecimen(
                order_item_id=added[requirement.catalog_id].id,
                order_specimen_id=specimen.id,
            ),
        )

    all_rows = order_repo.get_items(session=session, order_id=order.id)
    total = _money(
        sum((item.price_charged for item, _ in all_rows), Decimal("0"))
    )
    discount = min(invoice.discount, total)
    preview = OrderPreviewPublic(
        items=[
            OrderPreviewItemPublic(
                catalog_id=item.catalog_id,
                catalog_code=catalog.code,
                catalog_name=catalog.name,
                catalog_price=item.catalog_price,
                price_charged=item.price_charged,
                is_covered_by_insurance=item.is_covered_by_insurance,
                insurance_provider_name=item.insurance_provider_name,
                price_override_reason=item.price_override_reason,
                source_catalog_ids=[
                    uuid.UUID(value) for value in item.source_catalog_ids
                ],
            )
            for item, catalog in all_rows
        ],
        specimens=[],
        total_amount=total,
        discount=discount,
        net_amount=_money(total - discount),
        initial_payment_amount=Decimal("0"),
        balance_due=Decimal("0"),
    )
    replacement, _ = _reissue_for_revision(
        session=session,
        invoice=invoice,
        preview=preview,
        revision=revision,
        created_by_id=performed_by_id,
    )
    _update_commission_for_revision(
        session=session,
        order=order,
        old_doctor_id=order.doctor_id,
        preview=preview,
        revision=revision,
    )
    revision.new_values = _snapshot_order(
        order=order, items=all_rows, invoice=replacement
    )
    session.add(revision)
    return set(added)


def _reissue_for_revision(
    *,
    session: Session,
    invoice: Invoice,
    preview: OrderPreviewPublic,
    revision: OrderRevision,
    created_by_id: uuid.UUID,
) -> tuple[Invoice, Decimal]:
    from app.services import billing as billing_service

    invoice.is_voided = True
    session.add(invoice)
    replacement = order_repo.create(
        session=session,
        db_obj=Invoice(
            order_id=invoice.order_id,
            invoice_number=invoice.invoice_number,
            version=invoice.version + 1,
            total_amount=preview.total_amount,
            discount=preview.discount,
            discount_reason=revision.correction_reason,
            net_amount=preview.net_amount,
            amount_paid=Decimal("0.00"),
            payment_status=PaymentStatus.unpaid,
            created_by_id=created_by_id,
        ),
    )
    billing_service.create_lines(session=session, invoice=replacement)
    transferred = min(_money(invoice.amount_paid), preview.net_amount)
    if transferred > 0:
        order_repo.create(
            session=session,
            db_obj=InvoiceBalanceTransfer(
                source_invoice_id=invoice.id,
                target_invoice_id=replacement.id,
                amount=transferred,
                created_by_id=created_by_id,
            ),
        )
    credit = _money(invoice.amount_paid - transferred)
    if credit > 0:
        order_repo.create(
            session=session,
            db_obj=CustomerCredit(
                order_id=invoice.order_id,
                source_invoice_id=invoice.id,
                order_revision_id=revision.id,
                amount=credit,
                reason=revision.correction_reason,
                created_by_id=created_by_id,
            ),
        )
    billing_service.recalculate_payment(session=session, invoice=replacement)
    return replacement, credit


def _update_commission_for_revision(
    *,
    session: Session,
    order: Order,
    old_doctor_id: uuid.UUID | None,
    preview: OrderPreviewPublic,
    revision: OrderRevision,
) -> Decimal:
    existing = session.exec(
        select(DoctorCommissionEntry).where(
            DoctorCommissionEntry.order_id == order.id,
            DoctorCommissionEntry.doctor_id == old_doctor_id,
        )
    ).first() if old_doctor_id else None
    adjustment = Decimal("0.00")
    if existing is not None and (
        order.doctor_id is None or existing.doctor_id != order.doctor_id
    ):
        if existing.payout_status == PayoutStatus.paid:
            adjustment = _money(-existing.commission_amount)
            order_repo.create(
                session=session,
                db_obj=DoctorCommissionAdjustment(
                    commission_entry_id=existing.id,
                    order_revision_id=revision.id,
                    amount=adjustment,
                    reason=revision.correction_reason,
                ),
            )
        else:
            existing.commission_amount = Decimal("0.00")
            existing.order_net_amount = preview.net_amount
            session.add(existing)
        existing = None
    if order.doctor_id is None:
        return adjustment

    target = session.exec(
        select(DoctorCommissionEntry).where(
            DoctorCommissionEntry.order_id == order.id,
            DoctorCommissionEntry.doctor_id == order.doctor_id,
        )
    ).first()
    today = date.today()
    config = session.exec(
        select(DoctorCommissionConfig)
        .where(
            DoctorCommissionConfig.doctor_id == order.doctor_id,
            DoctorCommissionConfig.effective_from <= today,
            (
                (DoctorCommissionConfig.effective_until == None)  # noqa: E711
                | (DoctorCommissionConfig.effective_until >= today)
            ),
        )
        .order_by(col(DoctorCommissionConfig.effective_from).desc())
    ).first()
    settings = finance_settings_service.get_settings(session=session)
    insured_rate = (
        config.insurance_commission_rate
        if config
        else settings.default_insurance_commission_rate
    )
    non_insured_rate = (
        config.commission_rate if config else settings.default_commission_rate
    )
    if insured_rate is None or non_insured_rate is None:
        return adjustment
    snapshot = commission_service.calculate_commission(
        lines=[
            (item.price_charged, item.is_covered_by_insurance)
            for item in preview.items
        ],
        discount=preview.discount,
        insured_rate=insured_rate,
        non_insured_rate=non_insured_rate,
        policy=settings.discount_allocation_policy,
    )
    if target is None:
        target = order_repo.create(
            session=session,
            db_obj=DoctorCommissionEntry(
                order_id=order.id,
                doctor_id=order.doctor_id,
                order_net_amount=snapshot.order_net_amount,
                insured_net_amount=snapshot.insured_net_amount,
                insured_rate_applied=snapshot.insured_rate_applied,
                insured_commission_amount=snapshot.insured_commission_amount,
                non_insured_net_amount=snapshot.non_insured_net_amount,
                non_insured_rate_applied=snapshot.non_insured_rate_applied,
                non_insured_commission_amount=snapshot.non_insured_commission_amount,
                discount_allocation_policy=snapshot.discount_allocation_policy,
                commission_amount=snapshot.commission_amount,
            ),
        )
    elif target.payout_status == PayoutStatus.paid:
        delta = _money(snapshot.commission_amount - target.commission_amount)
        if delta:
            order_repo.create(
                session=session,
                db_obj=DoctorCommissionAdjustment(
                    commission_entry_id=target.id,
                    order_revision_id=revision.id,
                    amount=delta,
                    reason=revision.correction_reason,
                ),
            )
            adjustment = _money(adjustment + delta)
    else:
        commission_service.apply_snapshot(entry=target, snapshot=snapshot)
        session.add(target)
    return adjustment


def _refunded_amount(*, session: Session, payment_id: uuid.UUID) -> Decimal:
    return _money(
        sum(
            (
                refund.amount
                for refund in session.exec(
                    select(PaymentRefund).where(
                        PaymentRefund.payment_id == payment_id
                    )
                ).all()
            ),
            Decimal("0.00"),
        )
    )


def _refund_invoice_for_cancellation(
    *,
    session: Session,
    invoice: Invoice,
    reason: str,
    refunded_by_id: uuid.UUID,
) -> tuple[int, Decimal]:
    from app.services import billing as billing_service

    refund_count = 0
    refund_total = Decimal("0.00")
    for payment, _method in order_repo.get_payments(
        session=session, invoice_id=invoice.id
    ):
        available = _money(
            payment.amount
            - _refunded_amount(session=session, payment_id=payment.id)
        )
        if available <= 0:
            continue
        refund = order_repo.create(
            session=session,
            db_obj=PaymentRefund(
                payment_id=payment.id,
                amount=available,
                payment_method_id=payment.payment_method_id,
                reason=reason,
                refunded_by_id=refunded_by_id,
            ),
        )
        payment.status = PaymentTransactionStatus.refunded
        session.add(payment)
        session.add(
            AuditLog(
                table_name="payment_refunds",
                record_id=refund.id,
                action=AuditAction.insert,
                new_values={
                    "amount": str(available),
                    "reason": reason,
                    "source": "order_cancellation",
                },
                performed_by_id=refunded_by_id,
            )
        )
        refund_count += 1
        refund_total = _money(refund_total + available)
    billing_service.recalculate_payment(session=session, invoice=invoice)
    return refund_count, refund_total


def _cancel_commission(
    *, session: Session, order: Order, revision: OrderRevision
) -> Decimal:
    adjustment = Decimal("0.00")
    entries = session.exec(
        select(DoctorCommissionEntry).where(DoctorCommissionEntry.order_id == order.id)
    ).all()
    for entry in entries:
        if entry.commission_amount == 0:
            continue
        if entry.payout_status == PayoutStatus.paid:
            amount = _money(-entry.commission_amount)
            order_repo.create(
                session=session,
                db_obj=DoctorCommissionAdjustment(
                    commission_entry_id=entry.id,
                    order_revision_id=revision.id,
                    amount=amount,
                    reason=revision.correction_reason,
                ),
            )
            adjustment = _money(adjustment + amount)
            continue
        entry.insured_commission_amount = Decimal("0.00")
        entry.non_insured_commission_amount = Decimal("0.00")
        entry.commission_amount = Decimal("0.00")
        session.add(entry)
    return adjustment


def cancel_order(
    *,
    session: Session,
    order_id: uuid.UUID,
    request: OrderCancelRequest,
    performed_by_id: uuid.UUID,
) -> OrderDetailPublic:
    order = order_repo.get_for_update(session=session, order_id=order_id)
    if order is None:
        raise NotFoundError("Demande non trouvée")
    if order.status == OrderStatus.cancelled:
        raise ConflictError("Cette demande est déjà annulée")
    if order.revision_number != request.expected_revision:
        raise ConflictError(
            "La demande a été modifiée par un autre utilisateur. Rechargez la page."
        )
    reason = request.reason.strip()
    if not reason:
        raise BusinessRuleError("Le motif d'annulation est requis")
    invoice = order_repo.get_invoice(session=session, order_id=order.id)
    if invoice is None:
        raise NotFoundError("Facture de la demande non trouvée")
    item_rows = order_repo.get_items(session=session, order_id=order.id)
    old_snapshot = _snapshot_order(order=order, items=item_rows, invoice=invoice)
    reports = order_repo.get_active_reports(session=session, order_id=order.id)
    revision = order_repo.create(
        session=session,
        db_obj=OrderRevision(
            order_id=order.id,
            revision_number=order.revision_number + 1,
            correction_reason=reason,
            old_values=old_snapshot,
            new_values={},
            effects={},
            performed_by_id=performed_by_id,
        ),
    )
    for report in reports:
        report.is_voided = True
        session.add(report)
    refund_count, refund_total = _refund_invoice_for_cancellation(
        session=session,
        invoice=invoice,
        reason=reason,
        refunded_by_id=performed_by_id,
    )
    commission_adjustment = _cancel_commission(
        session=session, order=order, revision=revision
    )
    order.status = OrderStatus.cancelled
    order.revision_number = revision.revision_number
    session.add(order)
    revision.new_values = _snapshot_order(
        order=order, items=item_rows, invoice=invoice
    )
    revision.effects = {
        "cancelled": True,
        "refund_count": refund_count,
        "refund_total": str(refund_total),
        "voided_report_count": len(reports),
        "invoice_reissued": False,
        "commission_adjustment": str(commission_adjustment),
    }
    session.add(revision)
    session.add(
        AuditLog(
            table_name="orders",
            record_id=order.id,
            action=AuditAction.update,
            old_values=revision.old_values,
            new_values={
                **revision.new_values,
                "revision_id": str(revision.id),
                "cancellation_reason": reason,
                "effects": revision.effects,
            },
            performed_by_id=performed_by_id,
        )
    )
    session.commit()
    return get_order_detail(session=session, order_id=order.id)


def update_order(
    *,
    session: Session,
    order_id: uuid.UUID,
    request: OrderUpdate,
    performed_by_id: uuid.UUID,
    can_override_prices: bool,
    can_discount: bool,
) -> OrderDetailPublic:
    order = order_repo.get_for_update(session=session, order_id=order_id)
    if order is None:
        raise NotFoundError("Demande non trouvée")
    if order.status == OrderStatus.cancelled:
        raise ConflictError("Une demande annulée ne peut pas être modifiée")
    if order.revision_number != request.expected_revision:
        raise ConflictError(
            "La demande a été modifiée par un autre utilisateur. Rechargez la page."
        )
    if request.initial_payment is not None:
        raise BusinessRuleError(
            "Les paiements doivent être gérés depuis la facture"
        )
    reason = request.correction_reason.strip()
    existing_items = order_repo.get_items(session=session, order_id=order.id)
    existing_item_by_catalog = {item.catalog_id: item for item, _ in existing_items}
    existing_analyte_ids = {
        catalog_id: [
            snapshot.analyte_id
            for snapshot in session.exec(
                select(OrderCatalogItemAnalyte)
                .where(
                    OrderCatalogItemAnalyte.order_item_id == item.id,
                    OrderCatalogItemAnalyte.is_active == True,  # noqa: E712
                )
                .order_by(col(OrderCatalogItemAnalyte.sort_order).asc())
            ).all()
        ]
        for catalog_id, item in existing_item_by_catalog.items()
    }
    requested_analyte_ids = {
        selection.catalog_id: selection.analyte_ids
        for selection in request.item_analytes
    }
    analytes_changed = any(
        existing_analyte_ids.get(catalog_id) != analyte_ids
        for catalog_id, analyte_ids in requested_analyte_ids.items()
        if catalog_id in existing_item_by_catalog
    )
    allowed_unavailable_ids = {
        item.catalog_id for item, _ in existing_items
    } | {
        uuid.UUID(source_id)
        for item, _ in existing_items
        for source_id in item.source_catalog_ids
    }
    preview = preview_order(
        session=session,
        request=request,
        can_override_prices=can_override_prices,
        can_discount=can_discount,
        can_collect_payment=False,
        allowed_unavailable_ids=allowed_unavailable_ids,
    )
    invoice = order_repo.get_invoice(session=session, order_id=order.id)
    if invoice is None:
        raise NotFoundError("Facture de la demande non trouvée")
    old_items = existing_items
    old_line_signature = [
        (
            item.catalog_id,
            item.catalog_price,
            item.price_charged,
            item.price_override_reason,
            item.is_covered_by_insurance,
            item.insurance_provider_name,
        )
        for item, _ in old_items
    ]
    old_snapshot = _snapshot_order(order=order, items=old_items, invoice=invoice)
    revision = order_repo.create(
        session=session,
        db_obj=OrderRevision(
            order_id=order.id,
            revision_number=order.revision_number + 1,
            correction_reason=reason,
            old_values=old_snapshot,
            new_values={},
            effects={},
            performed_by_id=performed_by_id,
        ),
    )

    old_doctor_id = order.doctor_id
    order.patient_id = request.patient_id
    order.doctor_id = request.doctor_id
    order.patient_insurance_id = request.patient_insurance_id
    order.patient_context_id = request.patient_context_id
    order.notes = (request.notes or "").strip() or None
    order.revision_number = revision.revision_number
    session.add(order)

    old_by_catalog = {item.catalog_id: item for item, _ in old_items}
    current_items: dict[uuid.UUID, OrderItem] = {}
    superseded_item_ids: list[uuid.UUID] = []
    analyte_effects = [0, 0, 0]
    for index, preview_item in enumerate(preview.items):
        existing = old_by_catalog.pop(preview_item.catalog_id, None)
        if existing is not None:
            existing.sort_order = index
            existing.catalog_price = preview_item.catalog_price
            existing.price_charged = preview_item.price_charged
            existing.price_override_reason = preview_item.price_override_reason
            existing.is_covered_by_insurance = (
                preview_item.is_covered_by_insurance
            )
            existing.insurance_provider_name = (
                preview_item.insurance_provider_name
            )
            existing.source_catalog_ids = [
                str(value) for value in preview_item.source_catalog_ids
            ]
            session.add(existing)
            if any(
                selection.catalog_id == preview_item.catalog_id
                for selection in request.item_analytes
            ):
                effects = _apply_item_analytes(
                    session=session,
                    item=existing,
                    analyte_ids=[
                        analyte.analyte_id for analyte in preview_item.analytes
                    ],
                    revision=revision,
                    reason=reason,
                )
                analyte_effects = [
                    current + value
                    for current, value in zip(analyte_effects, effects, strict=True)
                ]
            current_items[preview_item.catalog_id] = existing
        else:
            current_items[preview_item.catalog_id] = _create_order_item(
                session=session,
                order_id=order.id,
                preview_item=preview_item,
                sort_order=index,
                revision_id=revision.id,
            )
    for removed in old_by_catalog.values():
        removed.is_active = False
        session.add(removed)
        superseded_item_ids.append(removed.id)
    for result in order_repo.get_results_for_items(
        session=session, item_ids=superseded_item_ids
    ):
        result.is_superseded = True
        result.superseded_revision_id = revision.id
        session.add(result)

    active_specimens = [
        specimen
        for specimen in session.exec(
            select(OrderSpecimen).where(
                OrderSpecimen.order_id == order.id,
                OrderSpecimen.is_superseded == False,  # noqa: E712
            )
        ).all()
        if not session.exec(
            select(OrderSpecimen.id).where(
                OrderSpecimen.replaces_specimen_id == specimen.id,
                OrderSpecimen.is_superseded == False,  # noqa: E712
            )
        ).first()
    ]
    specimens_by_type = {item.specimen_type_id: item for item in active_specimens}
    required_types = {item.specimen_type_id for item in preview.specimens}
    reused_collected = 0
    created_pending = 0
    for specimen_preview in preview.specimens:
        specimen = specimens_by_type.get(specimen_preview.specimen_type_id)
        if specimen is None:
            specimen = order_repo.create(
                session=session,
                db_obj=OrderSpecimen(
                    order_id=order.id,
                    specimen_type_id=specimen_preview.specimen_type_id,
                    status=SpecimenStatus.pending,
                    required_volume_ml=specimen_preview.required_volume_ml,
                    collection_instructions=specimen_preview.collection_instructions,
                ),
            )
            specimens_by_type[specimen.specimen_type_id] = specimen
            created_pending += 1
        elif specimen.status == SpecimenStatus.collected:
            reused_collected += 1
        else:
            specimen.required_volume_ml = specimen_preview.required_volume_ml
            specimen.collection_instructions = (
                specimen_preview.collection_instructions
            )
            session.add(specimen)
        for catalog_id in specimen_preview.catalog_ids:
            item = current_items[catalog_id]
            link = session.exec(
                select(OrderItemSpecimen).where(
                    OrderItemSpecimen.order_item_id == item.id,
                    OrderItemSpecimen.order_specimen_id == specimen.id,
                )
            ).first()
            if link is None:
                order_repo.create(
                    session=session,
                    db_obj=OrderItemSpecimen(
                        order_item_id=item.id,
                        order_specimen_id=specimen.id,
                    ),
                )
    for specimen in active_specimens:
        if (
            specimen.specimen_type_id not in required_types
            and specimen.status == SpecimenStatus.pending
        ):
            specimen.is_superseded = True
            specimen.superseded_revision_id = revision.id
            session.add(specimen)
    current_specimens = [
        item
        for item in specimens_by_type.values()
        if item.specimen_type_id in required_types and not item.is_superseded
    ]
    if current_specimens:
        order.status = (
            OrderStatus.registered
            if any(item.status == SpecimenStatus.pending for item in current_specimens)
            else OrderStatus.collected
        )
        session.add(order)

    reports = order_repo.get_active_reports(session=session, order_id=order.id)
    clinical_changed = (
        request.patient_id != uuid.UUID(old_snapshot["patient_id"])
        or set(old_snapshot["catalog_ids"])
        != {str(item.catalog_id) for item in preview.items}
        or analytes_changed
    )
    if clinical_changed:
        for report in reports:
            report.is_voided = True
            session.add(report)
    if analytes_changed:
        from app.services import result as result_service

        result_service._refresh_order_status(session=session, order=order)

    financial_changed = (
        invoice.total_amount != preview.total_amount
        or invoice.discount != preview.discount
        or old_line_signature
        != [
            (
                item.catalog_id,
                item.catalog_price,
                item.price_charged,
                item.price_override_reason,
                item.is_covered_by_insurance,
                item.insurance_provider_name,
            )
            for item in preview.items
        ]
    )
    credit = Decimal("0.00")
    if financial_changed:
        invoice, credit = _reissue_for_revision(
            session=session,
            invoice=invoice,
            preview=preview,
            revision=revision,
            created_by_id=performed_by_id,
        )
    commission_adjustment = _update_commission_for_revision(
        session=session,
        order=order,
        old_doctor_id=old_doctor_id,
        preview=preview,
        revision=revision,
    )
    new_items = order_repo.get_items(session=session, order_id=order.id)
    revision.new_values = _snapshot_order(
        order=order, items=new_items, invoice=invoice
    )
    revision.effects = {
        "superseded_item_count": len(superseded_item_ids),
        "reused_collected_specimen_count": reused_collected,
        "created_pending_specimen_count": created_pending,
        "voided_report_count": len(reports) if clinical_changed else 0,
        "added_analyte_count": analyte_effects[0],
        "restored_analyte_count": analyte_effects[1],
        "removed_analyte_count": analyte_effects[2],
        "invoice_reissued": financial_changed,
        "customer_credit": str(credit),
        "commission_adjustment": str(commission_adjustment),
    }
    session.add(revision)
    session.add(
        AuditLog(
            table_name="orders",
            record_id=order.id,
            action=AuditAction.update,
            old_values=revision.old_values,
            new_values={
                **revision.new_values,
                "revision_id": str(revision.id),
                "correction_reason": reason,
                "effects": revision.effects,
            },
            performed_by_id=performed_by_id,
        )
    )
    session.commit()
    return get_order_detail(session=session, order_id=order.id)


def get_order_revisions(
    *, session: Session, order_id: uuid.UUID
) -> OrderRevisionsPublic:
    if order_repo.get_by_id(session=session, order_id=order_id) is None:
        raise NotFoundError("Demande non trouvée")
    rows = order_repo.get_revisions(session=session, order_id=order_id)
    return OrderRevisionsPublic(
        data=[
            OrderRevisionPublic(
                **revision.model_dump(),
                performed_by_name=(
                    (operator.full_name or operator.email) if operator else None
                ),
            )
            for revision, operator in rows
        ],
        count=len(rows),
    )


def preview_order_update(
    *,
    session: Session,
    order_id: uuid.UUID,
    request: OrderPreviewRequest,
    can_override_prices: bool,
    can_discount: bool,
) -> OrderPreviewPublic:
    items = order_repo.get_items(session=session, order_id=order_id)
    if not items and order_repo.get_by_id(session=session, order_id=order_id) is None:
        raise NotFoundError("Demande non trouvée")
    allowed_unavailable_ids = {
        item.catalog_id for item, _ in items
    } | {
        uuid.UUID(source_id)
        for item, _ in items
        for source_id in item.source_catalog_ids
    }
    return preview_order(
        session=session,
        request=request,
        can_override_prices=can_override_prices,
        can_discount=can_discount,
        can_collect_payment=False,
        allowed_unavailable_ids=allowed_unavailable_ids,
    )


def get_orders(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 25,
    search: str | None = None,
    status=None,
    patient_id: uuid.UUID | None = None,
    doctor_id: uuid.UUID | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.desc,
):
    rows, count = order_repo.get_all(
        session=session,
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        patient_id=patient_id,
        doctor_id=doctor_id,
        created_from=created_from,
        created_to=created_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return (
        [
            OrderListItemPublic(
                id=order.id,
                accession_number=order.accession_number,
                patient_id=patient.id,
                patient_identifier=patient.identifier,
                patient_name=f"{patient.first_name} {patient.last_name}",
                doctor_id=doctor.id if doctor else None,
                doctor_name=(
                    f"{doctor.first_name} {doctor.last_name}" if doctor else None
                ),
                status=order.status,
                net_amount=invoice.net_amount,
                payment_status=invoice.payment_status,
                created_at=order.created_at,
            )
            for order, patient, doctor, invoice in rows
        ],
        count,
    )


def get_order_detail(*, session: Session, order_id: uuid.UUID) -> OrderDetailPublic:
    header = order_repo.get_order_header(session=session, order_id=order_id)
    if header is None:
        raise NotFoundError("Demande non trouvée")
    order, patient, doctor, insurance, provider, context, creator = header
    invoice = order_repo.get_invoice(session=session, order_id=order_id)
    if invoice is None:
        raise NotFoundError("Facture de la demande non trouvée")
    specimen_ids = order_repo.get_item_specimen_ids(session=session, order_id=order_id)
    item_rows = order_repo.get_items(session=session, order_id=order_id)
    analytes_by_item = _get_order_analytes(
        session=session,
        item_ids=[item.id for item, _ in item_rows],
    )
    items = [
        OrderItemDetailPublic(
            **item.model_dump(),
            catalog_code=catalog.code,
            catalog_name=catalog.name,
            specimen_ids=specimen_ids.get(item.id, []),
            analytes=analytes_by_item.get(item.id, []),
        )
        for item, catalog in item_rows
    ]
    specimens = [
        OrderSpecimenDetailPublic(
            **specimen.model_dump(),
            specimen_type_name=specimen_type.name,
            specimen_type_color=specimen_type.color,
        )
        for specimen, specimen_type in order_repo.get_specimens(
            session=session, order_id=order_id
        )
    ]
    payments = [
        PaymentTransactionPublic(
            **payment.model_dump(),
            payment_method_name=method.name,
        )
        for payment, method in order_repo.get_payments(
            session=session, invoice_id=invoice.id
        )
    ]
    return OrderDetailPublic(
        **order.model_dump(),
        patient_identifier=patient.identifier,
        patient_name=f"{patient.first_name} {patient.last_name}",
        patient_date_of_birth=patient.date_of_birth,
        patient_gender=patient.gender,
        doctor_name=(f"{doctor.first_name} {doctor.last_name}" if doctor else None),
        patient_context_name=context.name if context else None,
        insurance_provider_name=provider.name if provider else None,
        insurance_policy_number=insurance.policy_number if insurance else None,
        created_by_name=(creator.full_name or creator.email) if creator else None,
        items=items,
        specimens=specimens,
        invoice=invoice,
        payments=payments,
    )


def customize_order_item_analytes(
    *,
    session: Session,
    order_id: uuid.UUID,
    item_id: uuid.UUID,
    request: OrderItemAnalyteCustomizeRequest,
    performed_by_id: uuid.UUID,
) -> OrderDetailPublic:
    order = order_repo.get_for_update(session=session, order_id=order_id)
    if order is None:
        raise NotFoundError("Demande non trouvée")
    if order.status == OrderStatus.cancelled:
        raise ConflictError("Une demande annulée ne peut pas être modifiée")
    if order.revision_number != request.expected_revision:
        raise ConflictError(
            "La demande a été modifiée par un autre utilisateur. Rechargez la page."
        )
    item = session.get(OrderItem, item_id)
    if item is None or item.order_id != order.id or not item.is_active:
        raise NotFoundError("Examen de la demande non trouvé")
    current = list(
        session.exec(
            select(OrderCatalogItemAnalyte)
            .where(
                OrderCatalogItemAnalyte.order_item_id == item.id,
                OrderCatalogItemAnalyte.is_active == True,  # noqa: E712
            )
            .order_by(col(OrderCatalogItemAnalyte.sort_order).asc())
        ).all()
    )
    current_ids = [snapshot.analyte_id for snapshot in current]
    if current_ids == request.analyte_ids:
        return get_order_detail(session=session, order_id=order.id)
    removed_ids = set(current_ids) - set(request.analyte_ids)
    removed_has_results = bool(
        removed_ids
        and session.exec(
            select(AnalyteResult.id).where(
                AnalyteResult.order_item_id == item.id,
                AnalyteResult.analyte_id.in_(removed_ids),
                AnalyteResult.is_superseded == False,  # noqa: E712
            )
        ).first()
    )
    reason = (request.reason or "").strip()
    if (order.status == OrderStatus.completed or removed_has_results) and not reason:
        raise BusinessRuleError(
            "Le motif est requis pour modifier des analytes avec des résultats"
        )
    reason = reason or "Personnalisation des analytes de la demande"
    invoice = order_repo.get_invoice(session=session, order_id=order.id)
    if invoice is None:
        raise NotFoundError("Facture de la demande non trouvée")
    item_rows = order_repo.get_items(session=session, order_id=order.id)
    old_snapshot = _snapshot_order(order=order, items=item_rows, invoice=invoice)
    old_snapshot["item_analytes"] = {
        str(item.id): [str(analyte_id) for analyte_id in current_ids]
    }
    revision = order_repo.create(
        session=session,
        db_obj=OrderRevision(
            order_id=order.id,
            revision_number=order.revision_number + 1,
            correction_reason=reason,
            old_values=old_snapshot,
            new_values={},
            effects={},
            performed_by_id=performed_by_id,
        ),
    )
    added, restored, removed = _apply_item_analytes(
        session=session,
        item=item,
        analyte_ids=request.analyte_ids,
        revision=revision,
        reason=reason,
    )
    reports = order_repo.get_active_reports(session=session, order_id=order.id)
    for report in reports:
        report.is_voided = True
        session.add(report)
    order.revision_number = revision.revision_number
    session.add(order)
    from app.services import result as result_service

    result_service._refresh_order_status(session=session, order=order)
    new_snapshot = _snapshot_order(order=order, items=item_rows, invoice=invoice)
    new_snapshot["item_analytes"] = {
        str(item.id): [str(analyte_id) for analyte_id in request.analyte_ids]
    }
    revision.new_values = new_snapshot
    revision.effects = {
        "order_item_id": str(item.id),
        "added_analyte_count": added,
        "restored_analyte_count": restored,
        "removed_analyte_count": removed,
        "voided_report_count": len(reports),
        "invoice_reissued": False,
        "commission_adjustment": "0.00",
    }
    session.add(revision)
    session.add(
        AuditLog(
            table_name="order_catalog_item_analytes",
            record_id=item.id,
            action=AuditAction.update,
            old_values={
                "analyte_ids": [str(analyte_id) for analyte_id in current_ids]
            },
            new_values={
                "analyte_ids": [
                    str(analyte_id) for analyte_id in request.analyte_ids
                ],
                "reason": reason,
                "revision_id": str(revision.id),
                "effects": revision.effects,
            },
            performed_by_id=performed_by_id,
        )
    )
    session.commit()
    return get_order_detail(session=session, order_id=order.id)


def collect_payment(
    *,
    session: Session,
    invoice_id: uuid.UUID,
    payment_in: PaymentCollect,
    collected_by_id: uuid.UUID,
) -> PaymentTransactionPublic:
    invoice = session.get(Invoice, invoice_id)
    if invoice is None or invoice.is_voided:
        raise NotFoundError("Facture non trouvée")
    order = session.get(Order, invoice.order_id)
    if order is not None and order.status == OrderStatus.cancelled:
        raise ConflictError(
            "Un paiement ne peut pas être enregistré sur une demande annulée"
        )
    method = session.get(PaymentMethod, payment_in.payment_method_id)
    if method is None or method.is_deleted:
        raise BusinessRuleError("Méthode de paiement non disponible")
    remaining = _money(invoice.net_amount - invoice.amount_paid)
    if payment_in.amount > remaining:
        raise BusinessRuleError("Le paiement dépasse le solde restant")
    payment = order_repo.create(
        session=session,
        db_obj=PaymentTransaction(
            invoice_id=invoice.id,
            amount=_money(payment_in.amount),
            payment_method_id=method.id,
            collected_by_id=collected_by_id,
        ),
    )
    order_repo.recalculate_invoice_payment(session=session, invoice=invoice)
    session.commit()
    session.refresh(payment)
    return PaymentTransactionPublic(
        **payment.model_dump(), payment_method_name=method.name
    )
