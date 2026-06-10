"""Invoice and payment ledger repository - database access only."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import aliased
from sqlmodel import Session, col, func, or_, select

from app.models.lis import (
    Catalog,
    Doctor,
    DoctorCommissionEntry,
    InsuranceProvider,
    Invoice,
    InvoiceBalanceTransfer,
    InvoiceLine,
    Order,
    OrderItem,
    Patient,
    PatientInsurance,
    PaymentMethod,
    PaymentRefund,
    PaymentStatus,
    PaymentTransaction,
    SortOrder,
)
from app.models.user import User

SORT_COLUMNS = {
    "invoice_number": Invoice.invoice_number,
    "net_amount": Invoice.net_amount,
    "amount_paid": Invoice.amount_paid,
    "payment_status": Invoice.payment_status,
    "created_at": Invoice.created_at,
}


def _filters(
    *,
    search: str | None,
    payment_status: PaymentStatus | None,
    insurance_provider_id: uuid.UUID | None,
    payment_method_id: uuid.UUID | None,
    is_voided: bool | None,
    created_from: datetime | None,
    created_to: datetime | None,
    min_net_amount: Decimal | None,
    max_net_amount: Decimal | None,
):
    conditions = []
    if search:
        query = f"%{search.strip()}%"
        conditions.append(
            or_(
                col(Invoice.invoice_number).ilike(query),
                col(Order.accession_number).ilike(query),
                col(Patient.identifier).ilike(query),
                col(Patient.first_name).ilike(query),
                col(Patient.last_name).ilike(query),
            )
        )
    if payment_status is not None:
        conditions.append(Invoice.payment_status == payment_status)
    if insurance_provider_id is not None:
        conditions.append(InsuranceProvider.id == insurance_provider_id)
    if payment_method_id is not None:
        conditions.append(
            Invoice.id.in_(
                select(PaymentTransaction.invoice_id).where(
                    PaymentTransaction.payment_method_id == payment_method_id
                )
            )
        )
    if is_voided is not None:
        conditions.append(Invoice.is_voided == is_voided)
    if created_from is not None:
        conditions.append(Invoice.created_at >= created_from)
    if created_to is not None:
        conditions.append(Invoice.created_at <= created_to)
    if min_net_amount is not None:
        conditions.append(Invoice.net_amount >= min_net_amount)
    if max_net_amount is not None:
        conditions.append(Invoice.net_amount <= max_net_amount)
    return conditions


def _base():
    return (
        select(Invoice, Order, Patient, InsuranceProvider)
        .join(Order, Invoice.order_id == Order.id)
        .join(Patient, Order.patient_id == Patient.id)
        .join(
            PatientInsurance,
            Order.patient_insurance_id == PatientInsurance.id,
            isouter=True,
        )
        .join(
            InsuranceProvider,
            PatientInsurance.insurance_provider_id == InsuranceProvider.id,
            isouter=True,
        )
    )


def get_all(
    *,
    session: Session,
    skip: int,
    limit: int,
    search: str | None,
    payment_status: PaymentStatus | None,
    insurance_provider_id: uuid.UUID | None,
    payment_method_id: uuid.UUID | None,
    is_voided: bool | None,
    created_from: datetime | None,
    created_to: datetime | None,
    min_net_amount: Decimal | None,
    max_net_amount: Decimal | None,
    sort_by: str | None,
    sort_order: SortOrder,
):
    conditions = _filters(
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
    base = _base().where(*conditions)
    count_query = (
        select(func.count())
        .select_from(Invoice)
        .join(Order, Invoice.order_id == Order.id)
        .join(Patient, Order.patient_id == Patient.id)
        .join(
            PatientInsurance,
            Order.patient_insurance_id == PatientInsurance.id,
            isouter=True,
        )
        .join(
            InsuranceProvider,
            PatientInsurance.insurance_provider_id == InsuranceProvider.id,
            isouter=True,
        )
        .where(*conditions)
    )
    sort_column = SORT_COLUMNS.get(sort_by or "created_at", Invoice.created_at)
    order_expr = (
        col(sort_column).desc()
        if sort_order == SortOrder.desc
        else col(sort_column).asc()
    )
    rows = session.exec(
        base.order_by(order_expr, col(Invoice.invoice_number).desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return list(rows), session.exec(count_query).one()


def get_summary(
    *,
    session: Session,
    search: str | None,
    payment_status: PaymentStatus | None,
    insurance_provider_id: uuid.UUID | None,
    payment_method_id: uuid.UUID | None,
    is_voided: bool | None,
    created_from: datetime | None,
    created_to: datetime | None,
    min_net_amount: Decimal | None,
    max_net_amount: Decimal | None,
):
    conditions = _filters(
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
    return session.exec(
        select(
            func.count(Invoice.id),
            func.coalesce(func.sum(Invoice.net_amount), 0),
            func.coalesce(func.sum(Invoice.amount_paid), 0),
            func.coalesce(func.sum(Invoice.net_amount - Invoice.amount_paid), 0),
        )
        .select_from(Invoice)
        .join(Order, Invoice.order_id == Order.id)
        .join(Patient, Order.patient_id == Patient.id)
        .join(
            PatientInsurance,
            Order.patient_insurance_id == PatientInsurance.id,
            isouter=True,
        )
        .join(
            InsuranceProvider,
            PatientInsurance.insurance_provider_id == InsuranceProvider.id,
            isouter=True,
        )
        .where(*conditions)
    ).one()


def get_by_id(*, session: Session, invoice_id: uuid.UUID):
    creator = aliased(User)
    return session.exec(
        select(
            Invoice,
            Order,
            Patient,
            Doctor,
            PatientInsurance,
            InsuranceProvider,
            creator,
        )
        .join(Order, Invoice.order_id == Order.id)
        .join(Patient, Order.patient_id == Patient.id)
        .join(Doctor, Order.doctor_id == Doctor.id, isouter=True)
        .join(
            PatientInsurance,
            Order.patient_insurance_id == PatientInsurance.id,
            isouter=True,
        )
        .join(
            InsuranceProvider,
            PatientInsurance.insurance_provider_id == InsuranceProvider.id,
            isouter=True,
        )
        .join(creator, Invoice.created_by_id == creator.id, isouter=True)
        .where(Invoice.id == invoice_id)
    ).first()


def get_for_update(*, session: Session, invoice_id: uuid.UUID):
    return session.exec(
        select(Invoice).where(Invoice.id == invoice_id).with_for_update()
    ).first()


def get_lines(*, session: Session, invoice_id: uuid.UUID):
    return list(
        session.exec(
            select(InvoiceLine)
            .where(InvoiceLine.invoice_id == invoice_id)
            .order_by(col(InvoiceLine.sort_order).asc())
        ).all()
    )


def get_order_items(*, session: Session, order_id: uuid.UUID):
    return list(
        session.exec(
            select(OrderItem, Catalog)
            .join(Catalog, OrderItem.catalog_id == Catalog.id)
            .where(OrderItem.order_id == order_id, OrderItem.is_active == True)  # noqa: E712
            .order_by(col(OrderItem.sort_order).asc())
        ).all()
    )


def get_payments(*, session: Session, invoice_id: uuid.UUID):
    collector = aliased(User)
    refunded = (
        select(
            PaymentRefund.payment_id,
            func.coalesce(func.sum(PaymentRefund.amount), 0).label("refunded"),
        )
        .group_by(PaymentRefund.payment_id)
        .subquery()
    )
    return list(
        session.exec(
            select(
                PaymentTransaction,
                PaymentMethod,
                collector,
                func.coalesce(refunded.c.refunded, 0),
            )
            .join(
                PaymentMethod,
                PaymentTransaction.payment_method_id == PaymentMethod.id,
            )
            .join(
                collector,
                PaymentTransaction.collected_by_id == collector.id,
                isouter=True,
            )
            .join(
                refunded,
                refunded.c.payment_id == PaymentTransaction.id,
                isouter=True,
            )
            .where(PaymentTransaction.invoice_id == invoice_id)
            .order_by(col(PaymentTransaction.created_at).asc())
        ).all()
    )


def get_refunds(*, session: Session, invoice_id: uuid.UUID):
    method = aliased(PaymentMethod)
    operator = aliased(User)
    return list(
        session.exec(
            select(PaymentRefund, method, operator)
            .join(PaymentTransaction, PaymentRefund.payment_id == PaymentTransaction.id)
            .join(method, PaymentRefund.payment_method_id == method.id)
            .join(operator, PaymentRefund.refunded_by_id == operator.id, isouter=True)
            .where(PaymentTransaction.invoice_id == invoice_id)
            .order_by(col(PaymentRefund.created_at).asc())
        ).all()
    )


def get_transfers(*, session: Session, invoice_id: uuid.UUID):
    operator = aliased(User)
    return list(
        session.exec(
            select(InvoiceBalanceTransfer, operator)
            .join(
                operator,
                InvoiceBalanceTransfer.created_by_id == operator.id,
                isouter=True,
            )
            .where(
                or_(
                    InvoiceBalanceTransfer.source_invoice_id == invoice_id,
                    InvoiceBalanceTransfer.target_invoice_id == invoice_id,
                )
            )
            .order_by(col(InvoiceBalanceTransfer.created_at).asc())
        ).all()
    )


def get_versions(*, session: Session, invoice_number: str):
    return list(
        session.exec(
            select(Invoice)
            .where(Invoice.invoice_number == invoice_number)
            .order_by(col(Invoice.version).desc())
        ).all()
    )


def get_payment(*, session: Session, payment_id: uuid.UUID):
    return session.exec(
        select(PaymentTransaction)
        .where(PaymentTransaction.id == payment_id)
        .with_for_update()
    ).first()


def refunded_amount(*, session: Session, payment_id: uuid.UUID) -> Decimal:
    return session.exec(
        select(func.coalesce(func.sum(PaymentRefund.amount), 0)).where(
            PaymentRefund.payment_id == payment_id
        )
    ).one()


def total_refunds(*, session: Session, invoice_id: uuid.UUID) -> Decimal:
    return session.exec(
        select(func.coalesce(func.sum(PaymentRefund.amount), 0))
        .select_from(PaymentRefund)
        .join(PaymentTransaction, PaymentRefund.payment_id == PaymentTransaction.id)
        .where(PaymentTransaction.invoice_id == invoice_id)
    ).one()


def total_completed_payments(*, session: Session, invoice_id: uuid.UUID) -> Decimal:
    return session.exec(
        select(func.coalesce(func.sum(PaymentTransaction.amount), 0)).where(
            PaymentTransaction.invoice_id == invoice_id,
        )
    ).one()


def incoming_transfers(*, session: Session, invoice_id: uuid.UUID) -> Decimal:
    return session.exec(
        select(func.coalesce(func.sum(InvoiceBalanceTransfer.amount), 0)).where(
            InvoiceBalanceTransfer.target_invoice_id == invoice_id
        )
    ).one()


def get_commission(*, session: Session, order_id: uuid.UUID):
    return session.exec(
        select(DoctorCommissionEntry).where(DoctorCommissionEntry.order_id == order_id)
    ).first()


def create(*, session: Session, db_obj):
    session.add(db_obj)
    session.flush()
    return db_obj


def get_payment_methods(*, session: Session, search: str | None, skip: int, limit: int):
    conditions = [PaymentMethod.is_deleted == False]  # noqa: E712
    if search:
        conditions.append(col(PaymentMethod.name).ilike(f"%{search.strip()}%"))
    count = session.exec(
        select(func.count()).select_from(PaymentMethod).where(*conditions)
    ).one()
    rows = session.exec(
        select(PaymentMethod)
        .where(*conditions)
        .order_by(col(PaymentMethod.name).asc())
        .offset(skip)
        .limit(limit)
    ).all()
    return list(rows), count


def get_insurance_providers(
    *, session: Session, search: str | None, skip: int, limit: int
):
    conditions = [InsuranceProvider.is_deleted == False]  # noqa: E712
    if search:
        conditions.append(col(InsuranceProvider.name).ilike(f"%{search.strip()}%"))
    count = session.exec(
        select(func.count()).select_from(InsuranceProvider).where(*conditions)
    ).one()
    rows = session.exec(
        select(InsuranceProvider)
        .where(*conditions)
        .order_by(col(InsuranceProvider.name).asc())
        .offset(skip)
        .limit(limit)
    ).all()
    return list(rows), count
