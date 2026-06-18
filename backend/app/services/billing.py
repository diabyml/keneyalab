"""Invoice management, payment, refund, and reissue workflows."""

import uuid
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from sqlmodel import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.lis import (
    AuditAction,
    AuditLog,
    InsuranceProviderPublic,
    InsuranceProvidersPublic,
    Invoice,
    InvoiceBalanceTransfer,
    InvoiceBalanceTransferPublic,
    InvoiceDetailPublic,
    InvoiceLine,
    InvoiceLinePublic,
    InvoiceListItemPublic,
    InvoiceListPublic,
    InvoicePublic,
    InvoiceReissueRequest,
    InvoiceSummaryPublic,
    Order,
    OrderStatus,
    PaymentCollect,
    PaymentMethod,
    PaymentMethodPublic,
    PaymentMethodsPublic,
    PaymentRefund,
    PaymentRefundCreate,
    PaymentRefundPublic,
    PaymentStatus,
    PaymentTransaction,
    PaymentTransactionPublic,
    PaymentTransactionStatus,
    PayoutStatus,
    SortOrder,
)
from app.repositories import billing as billing_repo
from app.repositories import order as order_repo
from app.services import commission as commission_service
from app.services import finance_settings as finance_settings_service

MONEY = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _display_name(user) -> str | None:
    return (user.full_name or user.email) if user else None


def next_invoice_number(*, session: Session) -> str:
    today = datetime.now(timezone.utc).date()
    value = order_repo.next_daily_value(
        session=session, sequence_date=today, sequence_type="invoice"
    )
    return f"FAC-{today:%Y%m%d}-{value:04d}"


def create_lines(*, session: Session, invoice: Invoice) -> list[InvoiceLine]:
    lines = []
    for item, catalog in billing_repo.get_order_items(
        session=session, order_id=invoice.order_id
    ):
        lines.append(
            billing_repo.create(
                session=session,
                db_obj=InvoiceLine(
                    invoice_id=invoice.id,
                    order_item_id=item.id,
                    catalog_code=catalog.code,
                    catalog_name=catalog.name,
                    amount=item.price_charged,
                    is_covered_by_insurance=item.is_covered_by_insurance,
                    insurance_provider_name=item.insurance_provider_name,
                    sort_order=item.sort_order,
                ),
            )
        )
    return lines


def recalculate_payment(*, session: Session, invoice: Invoice) -> None:
    payments = billing_repo.total_completed_payments(
        session=session, invoice_id=invoice.id
    )
    refunds = billing_repo.total_refunds(session=session, invoice_id=invoice.id)
    transfers = billing_repo.incoming_transfers(session=session, invoice_id=invoice.id)
    effective = _money(payments - refunds + transfers)
    invoice.amount_paid = max(Decimal("0.00"), effective)
    if invoice.amount_paid <= 0:
        invoice.payment_status = (
            PaymentStatus.refunded if refunds > 0 else PaymentStatus.unpaid
        )
    elif invoice.amount_paid >= invoice.net_amount:
        invoice.payment_status = PaymentStatus.paid
    else:
        invoice.payment_status = PaymentStatus.partial
    session.add(invoice)


def _filter_args(**kwargs):
    return kwargs


def get_invoices(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 25,
    search: str | None = None,
    payment_status: PaymentStatus | None = None,
    insurance_provider_id: uuid.UUID | None = None,
    payment_method_id: uuid.UUID | None = None,
    is_voided: bool | None = False,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    min_net_amount: Decimal | None = None,
    max_net_amount: Decimal | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.desc,
) -> InvoiceListPublic:
    args = _filter_args(
        search=search,
        payment_status=payment_status,
        insurance_provider_id=insurance_provider_id,
        payment_method_id=payment_method_id,
        is_voided=is_voided,
        created_from=created_from,
        created_to=created_to,
        min_net_amount=min_net_amount,
        max_net_amount=max_net_amount,
    )
    rows, count = billing_repo.get_all(
        session=session,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        **args,
    )
    return InvoiceListPublic(
        data=[
            InvoiceListItemPublic(
                id=invoice.id,
                invoice_number=invoice.invoice_number,
                version=invoice.version,
                is_voided=invoice.is_voided,
                order_id=order.id,
                accession_number=order.accession_number,
                patient_id=patient.id,
                patient_identifier=patient.identifier,
                patient_name=f"{patient.first_name} {patient.last_name}",
                insurance_provider_name=provider.name if provider else None,
                total_amount=invoice.total_amount,
                discount=invoice.discount,
                net_amount=invoice.net_amount,
                amount_paid=invoice.amount_paid,
                balance_due=max(
                    Decimal("0.00"), invoice.net_amount - invoice.amount_paid
                ),
                payment_status=invoice.payment_status,
                created_at=invoice.created_at,
            )
            for invoice, order, patient, provider in rows
        ],
        count=count,
    )


def get_summary(
    *,
    session: Session,
    search: str | None = None,
    payment_status: PaymentStatus | None = None,
    insurance_provider_id: uuid.UUID | None = None,
    payment_method_id: uuid.UUID | None = None,
    is_voided: bool | None = False,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    min_net_amount: Decimal | None = None,
    max_net_amount: Decimal | None = None,
) -> InvoiceSummaryPublic:
    values = billing_repo.get_summary(
        session=session,
        search=search,
        payment_status=payment_status,
        insurance_provider_id=insurance_provider_id,
        payment_method_id=payment_method_id,
        is_voided=is_voided,
        created_from=created_from,
        created_to=created_to,
        min_net_amount=min_net_amount,
        max_net_amount=max_net_amount,
    )
    return InvoiceSummaryPublic(
        count=values[0],
        net_billed=_money(values[1]),
        collected=_money(values[2]),
        outstanding=_money(values[3]),
    )


def get_invoice_detail(
    *, session: Session, invoice_id: uuid.UUID
) -> InvoiceDetailPublic:
    row = billing_repo.get_by_id(session=session, invoice_id=invoice_id)
    if row is None:
        raise NotFoundError("Facture non trouvée")
    invoice, order, patient, doctor, insurance, provider, creator = row
    payments = []
    for payment, method, collector, refunded in billing_repo.get_payments(
        session=session, invoice_id=invoice.id
    ):
        payments.append(
            PaymentTransactionPublic(
                **payment.model_dump(),
                payment_method_name=method.name,
                collected_by_name=_display_name(collector),
                refunded_amount=_money(refunded),
                refundable_amount=max(
                    Decimal("0.00"), _money(payment.amount - refunded)
                ),
            )
        )
    refunds = [
        PaymentRefundPublic(
            **refund.model_dump(),
            payment_method_name=method.name,
            refunded_by_name=_display_name(operator),
        )
        for refund, method, operator in billing_repo.get_refunds(
            session=session, invoice_id=invoice.id
        )
    ]
    transfers = [
        InvoiceBalanceTransferPublic(
            **transfer.model_dump(),
            created_by_name=_display_name(operator),
        )
        for transfer, operator in billing_repo.get_transfers(
            session=session, invoice_id=invoice.id
        )
    ]
    return InvoiceDetailPublic(
        **invoice.model_dump(),
        accession_number=order.accession_number,
        patient_id=patient.id,
        patient_identifier=patient.identifier,
        patient_name=f"{patient.first_name} {patient.last_name}",
        doctor_name=(f"{doctor.first_name} {doctor.last_name}" if doctor else None),
        insurance_provider_name=provider.name if provider else None,
        insurance_policy_number=insurance.policy_number if insurance else None,
        created_by_name=_display_name(creator),
        balance_due=max(Decimal("0.00"), invoice.net_amount - invoice.amount_paid),
        lines=[
            InvoiceLinePublic.model_validate(item)
            for item in billing_repo.get_lines(session=session, invoice_id=invoice.id)
        ],
        payments=payments,
        refunds=refunds,
        transfers=transfers,
        versions=[
            InvoicePublic.model_validate(item)
            for item in billing_repo.get_versions(
                session=session, invoice_number=invoice.invoice_number
            )
        ],
    )


def collect_payment(
    *,
    session: Session,
    invoice_id: uuid.UUID,
    payment_in: PaymentCollect,
    collected_by_id: uuid.UUID,
) -> InvoiceDetailPublic:
    invoice = billing_repo.get_for_update(session=session, invoice_id=invoice_id)
    if invoice is None or invoice.is_voided:
        raise NotFoundError("Facture active non trouvée")
    order = session.get(Order, invoice.order_id)
    if order is not None and order.status == OrderStatus.cancelled:
        raise ConflictError(
            "Un paiement ne peut pas être enregistré sur une demande annulée"
        )
    payment_method = session.get(PaymentMethod, payment_in.payment_method_id)
    if payment_method is None or payment_method.is_deleted:
        raise BusinessRuleError("Méthode de paiement non disponible")
    remaining = _money(invoice.net_amount - invoice.amount_paid)
    if payment_in.amount > remaining:
        raise BusinessRuleError("Le paiement dépasse le solde restant")
    billing_repo.create(
        session=session,
        db_obj=PaymentTransaction(
            invoice_id=invoice.id,
            amount=_money(payment_in.amount),
            payment_method_id=payment_method.id,
            collected_by_id=collected_by_id,
        ),
    )
    recalculate_payment(session=session, invoice=invoice)
    session.commit()
    return get_invoice_detail(session=session, invoice_id=invoice.id)


def refund_payment(
    *,
    session: Session,
    invoice_id: uuid.UUID,
    payment_id: uuid.UUID,
    request: PaymentRefundCreate,
    refunded_by_id: uuid.UUID,
) -> InvoiceDetailPublic:
    invoice = billing_repo.get_for_update(session=session, invoice_id=invoice_id)
    payment = billing_repo.get_payment(session=session, payment_id=payment_id)
    if invoice is None or payment is None or payment.invoice_id != invoice.id:
        raise NotFoundError("Paiement non trouvé")
    if invoice.is_voided:
        raise ConflictError("Une facture annulée ne peut pas être remboursée")
    method = session.get(PaymentMethod, request.payment_method_id)
    if method is None or method.is_deleted:
        raise BusinessRuleError("Méthode de remboursement non disponible")
    refunded = billing_repo.refunded_amount(session=session, payment_id=payment.id)
    available = _money(payment.amount - refunded)
    if request.amount > available:
        raise BusinessRuleError("Le remboursement dépasse le montant remboursable")
    refund = billing_repo.create(
        session=session,
        db_obj=PaymentRefund(
            payment_id=payment.id,
            amount=_money(request.amount),
            payment_method_id=method.id,
            reason=request.reason.strip(),
            refunded_by_id=refunded_by_id,
        ),
    )
    if _money(refunded + request.amount) >= payment.amount:
        payment.status = PaymentTransactionStatus.refunded
        session.add(payment)
    recalculate_payment(session=session, invoice=invoice)
    session.add(
        AuditLog(
            table_name="payment_refunds",
            record_id=refund.id,
            action=AuditAction.insert,
            new_values={
                "amount": str(_money(request.amount)),
                "reason": request.reason.strip(),
            },
            performed_by_id=refunded_by_id,
        )
    )
    session.commit()
    return get_invoice_detail(session=session, invoice_id=invoice.id)


def reissue_invoice(
    *,
    session: Session,
    invoice_id: uuid.UUID,
    request: InvoiceReissueRequest,
    created_by_id: uuid.UUID,
) -> InvoiceDetailPublic:
    invoice = billing_repo.get_for_update(session=session, invoice_id=invoice_id)
    if invoice is None or invoice.is_voided:
        raise NotFoundError("Facture active non trouvée")
    order = session.get(Order, invoice.order_id)
    if order is not None and order.status == OrderStatus.cancelled:
        raise ConflictError(
            "Une facture liée à une demande annulée ne peut pas être réémise"
        )
    items = billing_repo.get_order_items(session=session, order_id=invoice.order_id)
    total = _money(sum((item.price_charged for item, _ in items), Decimal("0")))
    discount = _money(request.discount)
    if discount > total:
        raise BusinessRuleError("La remise dépasse le montant total")
    net = _money(total - discount)
    transferable = _money(invoice.amount_paid)
    if transferable > net:
        excess = _money(transferable - net)
        raise BusinessRuleError(
            f"Remboursez d'abord {excess:.2f} avant de réémettre la facture"
        )
    commission = billing_repo.get_commission(session=session, order_id=invoice.order_id)
    if commission is not None and commission.payout_status == PayoutStatus.paid:
        raise ConflictError(
            "La commission liée est déjà payée; une résolution manuelle est requise"
        )
    invoice.is_voided = True
    session.add(invoice)
    replacement = billing_repo.create(
        session=session,
        db_obj=Invoice(
            order_id=invoice.order_id,
            invoice_number=invoice.invoice_number,
            version=invoice.version + 1,
            total_amount=total,
            discount=discount,
            discount_reason=request.reason.strip(),
            net_amount=net,
            amount_paid=Decimal("0.00"),
            payment_status=PaymentStatus.unpaid,
            created_by_id=created_by_id,
        ),
    )
    create_lines(session=session, invoice=replacement)
    if transferable > 0:
        billing_repo.create(
            session=session,
            db_obj=InvoiceBalanceTransfer(
                source_invoice_id=invoice.id,
                target_invoice_id=replacement.id,
                amount=transferable,
                created_by_id=created_by_id,
            ),
        )
    recalculate_payment(session=session, invoice=replacement)
    if commission is not None:
        policy = finance_settings_service.get_settings(
            session=session
        ).discount_allocation_policy
        snapshot = commission_service.calculate_commission(
            lines=[
                (item.price_charged, item.is_covered_by_insurance)
                for item, _ in items
            ],
            discount=discount,
            insured_rate=commission.insured_rate_applied,
            non_insured_rate=commission.non_insured_rate_applied,
            policy=policy,
        )
        session.add(
            commission_service.apply_snapshot(
                entry=commission,
                snapshot=snapshot,
            )
        )
    session.add(
        AuditLog(
            table_name="invoices",
            record_id=invoice.id,
            action=AuditAction.update,
            old_values={"version": invoice.version, "is_voided": False},
            new_values={
                "is_voided": True,
                "replacement_id": str(replacement.id),
                "reason": request.reason.strip(),
            },
            performed_by_id=created_by_id,
        )
    )
    session.commit()
    return get_invoice_detail(session=session, invoice_id=replacement.id)


def get_payment_method_options(
    *, session: Session, search: str | None, skip: int, limit: int
) -> PaymentMethodsPublic:
    rows, count = billing_repo.get_payment_methods(
        session=session, search=search, skip=skip, limit=limit
    )
    return PaymentMethodsPublic(
        data=[PaymentMethodPublic.model_validate(item) for item in rows],
        count=count,
    )


def get_insurance_provider_options(
    *, session: Session, search: str | None, skip: int, limit: int
) -> InsuranceProvidersPublic:
    rows, count = billing_repo.get_insurance_providers(
        session=session, search=search, skip=skip, limit=limit
    )
    return InsuranceProvidersPublic(
        data=[InsuranceProviderPublic.model_validate(item) for item in rows],
        count=count,
    )
