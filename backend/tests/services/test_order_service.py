import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from app.core.exceptions import ConflictError
from app.models import User
from app.models.lis import (
    AnalyteResult,
    Catalog,
    CatalogPanelItem,
    CatalogSpecimenRequirement,
    CatalogType,
    CustomerCredit,
    DiscountAllocationPolicy,
    Doctor,
    DoctorCommissionAdjustment,
    DoctorCommissionConfig,
    DoctorCommissionEntry,
    FinanceSettings,
    GenderType,
    InsurancePricing,
    InsuranceProvider,
    Invoice,
    InvoiceBalanceTransfer,
    InvoiceReissueRequest,
    Order,
    OrderCancelRequest,
    OrderCreate,
    OrderItem,
    OrderItemSpecimen,
    OrderRevision,
    OrderStatus,
    OrderUpdate,
    Patient,
    PatientInsurance,
    PaymentCollect,
    PaymentMethod,
    PaymentRefund,
    PaymentRefundCreate,
    PaymentStatus,
    PayoutStatus,
    RejectionReason,
    Report,
    ReportChannel,
    SpecimenRejectRequest,
    SpecimenStatus,
    SpecimenType,
)
from app.services.billing import (
    collect_payment,
    refund_payment,
    reissue_invoice,
)
from app.services.catalog import get_catalogs
from app.services.order import (
    cancel_order,
    create_order,
    get_order_detail,
    preview_order,
    update_order,
)
from app.services.specimen import collect_all, reject


def _cancellable_order(db: Session, *, doctor: Doctor | None = None):
    suffix = uuid.uuid4().hex[:8].upper()
    patient = Patient(
        identifier=f"PAT-CANCEL-{suffix}",
        first_name="Awa",
        last_name="Cancel",
        date_of_birth=date(1990, 1, 1),
        gender=GenderType.female,
    )
    specimen_type = SpecimenType(
        name=f"Sérum annulation {suffix}",
        color="#ef4444",
    )
    catalog = Catalog(
        type=CatalogType.item,
        code=f"CANCEL-{suffix}",
        name=f"Test annulation {suffix}",
        price=Decimal("1000.00"),
    )
    db.add_all([patient, specimen_type, catalog])
    db.flush()
    db.add(
        CatalogSpecimenRequirement(
            catalog_id=catalog.id,
            specimen_type_id=specimen_type.id,
            volume_ml=Decimal("2.00"),
        )
    )
    db.commit()
    user = db.exec(select(User)).first()
    assert user is not None
    order = create_order(
        session=db,
        request=OrderCreate(
            patient_id=patient.id,
            doctor_id=doctor.id if doctor else None,
            catalog_ids=[catalog.id],
        ),
        created_by_id=user.id,
        can_override_prices=True,
        can_discount=True,
        can_collect_payment=True,
    )
    return order, user, patient, specimen_type, catalog


def test_order_creation_expands_panel_and_deduplicates_specimens(db: Session) -> None:
    patient = Patient(
        identifier="PAT-ORDER-TEST",
        first_name="Awa",
        last_name="Traoré",
        date_of_birth=date(1990, 1, 1),
        gender=GenderType.female,
    )
    specimen_type = SpecimenType(
        name="Sérum test commande",
        description="Tube test",
        color="#ffff00",
    )
    test_one = Catalog(
        type=CatalogType.item,
        code="ORD-T1",
        name="Test commande 1",
        price=Decimal("1000.00"),
    )
    test_two = Catalog(
        type=CatalogType.item,
        code="ORD-T2",
        name="Test commande 2",
        price=Decimal("2000.00"),
    )
    panel = Catalog(
        type=CatalogType.panel,
        code="ORD-P1",
        name="Panel commande",
        price=Decimal("0.00"),
    )
    db.add_all([patient, specimen_type, test_one, test_two, panel])
    db.flush()
    db.add_all(
        [
            CatalogPanelItem(panel_id=panel.id, test_id=test_one.id, sort_order=0),
            CatalogPanelItem(panel_id=panel.id, test_id=test_two.id, sort_order=1),
            CatalogSpecimenRequirement(
                catalog_id=test_one.id,
                specimen_type_id=specimen_type.id,
                volume_ml=Decimal("2.00"),
                instructions="À jeun",
            ),
            CatalogSpecimenRequirement(
                catalog_id=test_two.id,
                specimen_type_id=specimen_type.id,
                volume_ml=Decimal("3.50"),
                instructions="Centrifuger",
            ),
        ]
    )
    db.commit()
    request = OrderCreate(
        patient_id=patient.id,
        catalog_ids=[panel.id, test_one.id],
    )
    preview = preview_order(
        session=db,
        request=request,
        can_override_prices=True,
        can_discount=True,
        can_collect_payment=True,
    )
    assert len(preview.items) == 2
    assert preview.total_amount == Decimal("3000.00")
    assert len(preview.specimens) == 1
    assert preview.specimens[0].required_volume_ml == Decimal("3.50")
    assert preview.specimens[0].collection_instructions == "À jeun; Centrifuger"

    user = db.exec(select(User)).first()
    assert user is not None
    order = create_order(
        session=db,
        request=request,
        created_by_id=user.id,
        can_override_prices=True,
        can_discount=True,
        can_collect_payment=True,
    )
    detail = get_order_detail(session=db, order_id=order.id)
    assert detail.created_by_name == (user.full_name or user.email)
    assert len(detail.items) == 2
    assert len(detail.specimens) == 1
    assert detail.specimens[0].status == SpecimenStatus.pending
    assert (
        len(
            db.exec(
                select(OrderItemSpecimen)
                .join(OrderItem, OrderItemSpecimen.order_item_id == OrderItem.id)
                .where(OrderItem.order_id == order.id)
            ).all()
        )
        == 2
    )
    workspace = collect_all(
        session=db,
        order_id=order.id,
        collected_by_id=user.id,
    )
    assert workspace.order_status.value == "collected"
    assert all(item.status == SpecimenStatus.collected for item in workspace.specimens)
    assert (
        db.exec(
            select(AnalyteResult).where(
                AnalyteResult.order_item_id.in_(
                    select(OrderItem.id).where(OrderItem.order_id == order.id)
                )
            )
        ).first()
        is None
    )

    added_test = Catalog(
        type=CatalogType.item,
        code="ORD-T3",
        name="Test ajouté après prélèvement",
        price=Decimal("500.00"),
    )
    db.add(added_test)
    db.flush()
    db.add(
        CatalogSpecimenRequirement(
            catalog_id=added_test.id,
            specimen_type_id=specimen_type.id,
            volume_ml=Decimal("1.00"),
        )
    )
    db.commit()
    updated = update_order(
        session=db,
        order_id=order.id,
        request=OrderUpdate(
            patient_id=patient.id,
            catalog_ids=[panel.id, added_test.id],
            correction_reason="Ajout demandé après prélèvement",
            expected_revision=1,
        ),
        performed_by_id=user.id,
        can_override_prices=True,
        can_discount=True,
    )
    assert updated.revision_number == 2
    assert len(updated.items) == 3
    assert len(updated.specimens) == 1
    assert updated.specimens[0].status == SpecimenStatus.collected
    revision = db.exec(
        select(OrderRevision).where(OrderRevision.order_id == order.id)
    ).one()
    assert revision.effects["reused_collected_specimen_count"] == 1
    assert revision.effects["created_pending_specimen_count"] == 0

    rejection_reason = RejectionReason(name="Tube non conforme test")
    db.add(rejection_reason)
    db.commit()
    db.refresh(rejection_reason)
    rejected_id = workspace.specimens[0].id
    workspace = reject(
        session=db,
        specimen_id=rejected_id,
        request=SpecimenRejectRequest(rejection_reason_id=rejection_reason.id),
        rejected_by_id=user.id,
    )
    assert workspace.order_status.value == "registered"
    assert any(item.status == SpecimenStatus.rejected for item in workspace.specimens)
    replacement = next(
        item for item in workspace.specimens if item.replaces_specimen_id == rejected_id
    )
    assert replacement.status == SpecimenStatus.pending
    assert replacement.attempt_number == 2

    invoice = db.exec(
        select(Invoice).where(
            Invoice.order_id == order.id,
            Invoice.is_voided == False,  # noqa: E712
        )
    ).one()
    payment_method = db.exec(
        select(PaymentMethod).where(PaymentMethod.is_deleted == False)  # noqa: E712
    ).first()
    assert payment_method is not None
    invoice_detail = collect_payment(
        session=db,
        invoice_id=invoice.id,
        payment_in=PaymentCollect(
            amount=Decimal("500.00"),
            payment_method_id=payment_method.id,
        ),
        collected_by_id=user.id,
    )
    assert invoice_detail.amount_paid == Decimal("500.00")
    payment = invoice_detail.payments[0]
    invoice_detail = refund_payment(
        session=db,
        invoice_id=invoice.id,
        payment_id=payment.id,
        request=PaymentRefundCreate(
            amount=Decimal("200.00"),
            payment_method_id=payment_method.id,
            reason="Correction test",
        ),
        refunded_by_id=user.id,
    )
    assert invoice_detail.amount_paid == Decimal("300.00")
    replacement = reissue_invoice(
        session=db,
        invoice_id=invoice.id,
        request=InvoiceReissueRequest(
            discount=Decimal("100.00"),
            reason="Remise corrigée",
        ),
        created_by_id=user.id,
    )
    assert replacement.version == 3
    assert replacement.amount_paid == Decimal("300.00")
    assert replacement.discount == Decimal("100.00")
    assert len(replacement.versions) == 3

    corrected = update_order(
        session=db,
        order_id=order.id,
        request=OrderUpdate(
            patient_id=patient.id,
            catalog_ids=[added_test.id],
            line_overrides=[
                {
                    "catalog_id": added_test.id,
                    "price_charged": Decimal("100.00"),
                    "reason": "Correction tarifaire",
                }
            ],
            correction_reason="Retrait des examens et correction tarifaire",
            expected_revision=2,
        ),
        performed_by_id=user.id,
        can_override_prices=True,
        can_discount=True,
    )
    assert corrected.revision_number == 3
    assert corrected.invoice.version == 4
    assert corrected.invoice.net_amount == Decimal("100.00")
    credit = db.exec(
        select(CustomerCredit).where(CustomerCredit.order_id == order.id)
    ).one()
    assert credit.amount == Decimal("200.00")

    order_invoices = list(
        db.exec(select(Invoice).where(Invoice.order_id == order.id)).all()
    )
    invoice_ids = [item.id for item in order_invoices]
    for transfer in db.exec(
        select(InvoiceBalanceTransfer).where(
            (InvoiceBalanceTransfer.source_invoice_id.in_(invoice_ids))
            | (InvoiceBalanceTransfer.target_invoice_id.in_(invoice_ids))
        )
    ).all():
        db.delete(transfer)
    for credit in db.exec(
        select(CustomerCredit).where(CustomerCredit.order_id == order.id)
    ).all():
        db.delete(credit)
    for order_invoice in order_invoices:
        db.delete(order_invoice)
    db.flush()
    db.delete(db.get(Order, order.id))
    db.delete(rejection_reason)
    db.commit()
    for obj in [added_test, panel, test_two, test_one, specimen_type, patient]:
        refreshed = db.get(type(obj), obj.id)
        if refreshed is not None:
            db.delete(refreshed)
    db.commit()


def test_order_catalog_options_exclude_empty_panels(db: Session) -> None:
    empty_panel = Catalog(
        type=CatalogType.panel,
        code="ORD-EMPTY",
        name="Panel vide commande",
        price=Decimal("0.00"),
    )
    db.add(empty_panel)
    db.commit()
    db.refresh(empty_panel)

    items, _ = get_catalogs(
        session=db,
        search=empty_panel.code,
        is_orderable=True,
        is_deleted=False,
        exclude_empty_panels=True,
    )

    assert empty_panel.id not in {item.id for item in items}
    db.delete(empty_panel)
    db.commit()


def test_cancel_order_refunds_payments_and_voids_reports(db: Session) -> None:
    order, user, _patient, _specimen_type, _catalog = _cancellable_order(db)
    invoice = db.exec(
        select(Invoice).where(
            Invoice.order_id == order.id,
            Invoice.is_voided == False,  # noqa: E712
        )
    ).one()
    method = db.exec(
        select(PaymentMethod).where(PaymentMethod.is_deleted == False)  # noqa: E712
    ).first()
    assert method is not None
    invoice_detail = collect_payment(
        session=db,
        invoice_id=invoice.id,
        payment_in=PaymentCollect(
            amount=Decimal("1000.00"),
            payment_method_id=method.id,
        ),
        collected_by_id=user.id,
    )
    payment = invoice_detail.payments[0]
    db.add(
        Report(
            order_id=order.id,
            channel=ReportChannel.print,
            released_by_id=user.id,
        )
    )
    db.commit()

    cancelled = cancel_order(
        session=db,
        order_id=order.id,
        request=OrderCancelRequest(
            reason="Demande créée par erreur",
            expected_revision=order.revision_number,
        ),
        performed_by_id=user.id,
    )

    assert cancelled.status == OrderStatus.cancelled
    assert cancelled.revision_number == 2
    assert cancelled.invoice.is_voided is False
    assert cancelled.invoice.payment_status == PaymentStatus.refunded
    assert cancelled.invoice.amount_paid == Decimal("0.00")
    refund = db.exec(
        select(PaymentRefund).where(PaymentRefund.payment_id == payment.id)
    ).one()
    assert refund.amount == Decimal("1000.00")
    assert refund.payment_method_id == method.id
    report = db.exec(select(Report).where(Report.order_id == order.id)).one()
    assert report.is_voided is True
    revision = db.exec(
        select(OrderRevision).where(OrderRevision.order_id == order.id)
    ).one()
    assert revision.effects["refund_total"] == "1000.00"
    assert revision.effects["voided_report_count"] == 1


def test_cancel_order_rejects_repeated_and_stale_requests(db: Session) -> None:
    order, user, _patient, _specimen_type, _catalog = _cancellable_order(db)

    with pytest.raises(ConflictError):
        cancel_order(
            session=db,
            order_id=order.id,
            request=OrderCancelRequest(
                reason="Révision obsolète",
                expected_revision=order.revision_number + 1,
            ),
            performed_by_id=user.id,
        )
    db.rollback()

    cancel_order(
        session=db,
        order_id=order.id,
        request=OrderCancelRequest(
            reason="Demande créée par erreur",
            expected_revision=order.revision_number,
        ),
        performed_by_id=user.id,
    )
    with pytest.raises(ConflictError):
        cancel_order(
            session=db,
            order_id=order.id,
            request=OrderCancelRequest(
                reason="Nouvelle tentative",
                expected_revision=order.revision_number + 1,
            ),
            performed_by_id=user.id,
        )


def test_cancel_order_creates_negative_paid_commission_adjustment(
    db: Session,
) -> None:
    doctor = Doctor(first_name="Moussa", last_name="Commission")
    config = DoctorCommissionConfig(
        doctor_id=doctor.id,
        commission_rate=Decimal("0.1000"),
        insurance_commission_rate=Decimal("0.0500"),
        effective_from=date.today(),
    )
    db.add(doctor)
    db.flush()
    config.doctor_id = doctor.id
    db.add(config)
    db.commit()
    order, user, _patient, _specimen_type, _catalog = _cancellable_order(
        db, doctor=doctor
    )
    entry = db.exec(
        select(DoctorCommissionEntry).where(
            DoctorCommissionEntry.order_id == order.id
        )
    ).one()
    entry.payout_status = PayoutStatus.paid
    db.add(entry)
    db.commit()

    cancel_order(
        session=db,
        order_id=order.id,
        request=OrderCancelRequest(
            reason="Annulation avec commission payée",
            expected_revision=order.revision_number,
        ),
        performed_by_id=user.id,
    )

    adjustment = db.exec(
        select(DoctorCommissionAdjustment).where(
            DoctorCommissionAdjustment.commission_entry_id == entry.id
        )
    ).one()
    assert adjustment.amount == -entry.commission_amount
    assert adjustment.is_settled is False


def test_order_creation_splits_mixed_doctor_commission(db: Session) -> None:
    patient = Patient(
        identifier="PAT-MIXED-COMMISSION",
        first_name="Mariam",
        last_name="Diallo",
        date_of_birth=date(1988, 6, 15),
        gender=GenderType.female,
    )
    doctor = Doctor(first_name="Fanta", last_name="Keita")
    provider = InsuranceProvider(name="Assurance commission mixte")
    insured_test = Catalog(
        type=CatalogType.item,
        code="COMM-INS",
        name="Test assuré commission",
        price=Decimal("400.00"),
    )
    non_insured_test = Catalog(
        type=CatalogType.item,
        code="COMM-DIRECT",
        name="Test direct commission",
        price=Decimal("200.00"),
    )
    db.add_all([patient, doctor, provider, insured_test, non_insured_test])
    db.flush()
    insurance = PatientInsurance(
        patient_id=patient.id,
        insurance_provider_id=provider.id,
        policy_number="POL-COMMISSION",
    )
    pricing = InsurancePricing(
        insurance_provider_id=provider.id,
        catalog_id=insured_test.id,
        insurance_price=Decimal("300.00"),
    )
    config = DoctorCommissionConfig(
        doctor_id=doctor.id,
        commission_rate=Decimal("0.1000"),
        insurance_commission_rate=Decimal("0.0500"),
        effective_from=date.today(),
    )
    settings = db.get(FinanceSettings, 1)
    assert settings is not None
    settings.discount_allocation_policy = (
        DiscountAllocationPolicy.non_insured_first
    )
    db.add_all([insurance, pricing, config, settings])
    db.commit()

    user = db.exec(select(User)).first()
    assert user is not None
    order = create_order(
        session=db,
        request=OrderCreate(
            patient_id=patient.id,
            doctor_id=doctor.id,
            patient_insurance_id=insurance.id,
            catalog_ids=[insured_test.id, non_insured_test.id],
            discount=Decimal("100.00"),
            discount_reason="Test de répartition",
        ),
        created_by_id=user.id,
        can_override_prices=True,
        can_discount=True,
        can_collect_payment=True,
    )

    entry = db.exec(
        select(DoctorCommissionEntry).where(
            DoctorCommissionEntry.order_id == order.id
        )
    ).one()
    assert entry.order_net_amount == Decimal("400.00")
    assert entry.insured_net_amount == Decimal("300.00")
    assert entry.insured_rate_applied == Decimal("0.0500")
    assert entry.insured_commission_amount == Decimal("15.00")
    assert entry.non_insured_net_amount == Decimal("100.00")
    assert entry.non_insured_rate_applied == Decimal("0.1000")
    assert entry.non_insured_commission_amount == Decimal("10.00")
    assert entry.commission_amount == Decimal("25.00")
    assert (
        entry.discount_allocation_policy
        == DiscountAllocationPolicy.non_insured_first
    )

    settings.discount_allocation_policy = DiscountAllocationPolicy.insured_first
    db.add(settings)
    db.commit()
    invoice = db.exec(
        select(Invoice).where(
            Invoice.order_id == order.id,
            Invoice.is_voided == False,  # noqa: E712
        )
    ).one()
    reissue_invoice(
        session=db,
        invoice_id=invoice.id,
        request=InvoiceReissueRequest(
            discount=Decimal("100.00"),
            reason="Test nouvelle politique",
        ),
        created_by_id=user.id,
    )
    db.refresh(entry)
    assert entry.insured_net_amount == Decimal("200.00")
    assert entry.non_insured_net_amount == Decimal("200.00")
    assert entry.insured_rate_applied == Decimal("0.0500")
    assert entry.non_insured_rate_applied == Decimal("0.1000")
    assert entry.commission_amount == Decimal("30.00")
    assert (
        entry.discount_allocation_policy
        == DiscountAllocationPolicy.insured_first
    )

    settings.discount_allocation_policy = (
        DiscountAllocationPolicy.non_insured_first
    )
    db.add(settings)
    db.delete(entry)
    for order_invoice in db.exec(
        select(Invoice).where(Invoice.order_id == order.id)
    ).all():
        db.delete(order_invoice)
    db.delete(order)
    db.commit()

    db.delete(config)
    db.delete(pricing)
    db.delete(insurance)
    db.commit()

    db.delete(non_insured_test)
    db.delete(insured_test)
    db.delete(provider)
    db.delete(doctor)
    db.delete(patient)
    db.commit()
