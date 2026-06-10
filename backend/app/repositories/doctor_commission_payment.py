"""Doctor commission payment repository - database access only."""

import uuid
from datetime import datetime

from sqlalchemy import String, cast, literal
from sqlalchemy.orm import aliased
from sqlmodel import Session, col, func, or_, select

from app.models.lis import (
    Doctor,
    DoctorCommissionAdjustment,
    DoctorCommissionEntry,
    DoctorCommissionPayment,
    DoctorCommissionPaymentEntry,
    Invoice,
    Order,
    OrderStatus,
    Patient,
    PaymentMethod,
    PaymentStatus,
    PayoutStatus,
    SortOrder,
)
from app.models.user import User


def _doctor_name():
    return func.concat(Doctor.first_name, " ", Doctor.last_name)


def _line_statement(*, payable_only: bool = True):
    common = (
        DoctorCommissionEntry.doctor_id.label("doctor_id"),
        _doctor_name().label("doctor_name"),
        DoctorCommissionEntry.order_id.label("order_id"),
        Order.accession_number.label("accession_number"),
        Invoice.invoice_number.label("invoice_number"),
        Order.created_at.label("order_date"),
        Patient.first_name.label("patient_first_name"),
        Patient.last_name.label("patient_last_name"),
    )
    entries = (
        select(
            literal("entry").label("line_type"),
            DoctorCommissionEntry.id.label("source_id"),
            *common,
            literal("Commission").label("description"),
            DoctorCommissionEntry.insured_net_amount.label("insured_net_amount"),
            DoctorCommissionEntry.non_insured_net_amount.label(
                "non_insured_net_amount"
            ),
            DoctorCommissionEntry.insured_commission_amount.label(
                "insured_commission_amount"
            ),
            DoctorCommissionEntry.non_insured_commission_amount.label(
                "non_insured_commission_amount"
            ),
            DoctorCommissionEntry.commission_amount.label("amount"),
            DoctorCommissionEntry.created_at.label("created_at"),
        )
        .join(Doctor, DoctorCommissionEntry.doctor_id == Doctor.id)
        .join(Order, DoctorCommissionEntry.order_id == Order.id)
        .join(Patient, Order.patient_id == Patient.id)
        .join(Invoice, Invoice.order_id == DoctorCommissionEntry.order_id)
        .where(
            Order.status != OrderStatus.cancelled,
            col(Invoice.is_voided).is_(False),
            Invoice.payment_status == PaymentStatus.paid,
            DoctorCommissionEntry.commission_amount != 0,
        )
    )
    adjustments = (
        select(
            literal("adjustment").label("line_type"),
            DoctorCommissionAdjustment.id.label("source_id"),
            *common,
            DoctorCommissionAdjustment.reason.label("description"),
            literal(0).label("insured_net_amount"),
            literal(0).label("non_insured_net_amount"),
            literal(0).label("insured_commission_amount"),
            literal(0).label("non_insured_commission_amount"),
            DoctorCommissionAdjustment.amount.label("amount"),
            DoctorCommissionAdjustment.created_at.label("created_at"),
        )
        .join(
            DoctorCommissionEntry,
            DoctorCommissionAdjustment.commission_entry_id
            == DoctorCommissionEntry.id,
        )
        .join(Doctor, DoctorCommissionEntry.doctor_id == Doctor.id)
        .join(Order, DoctorCommissionEntry.order_id == Order.id)
        .join(Patient, Order.patient_id == Patient.id)
        .join(Invoice, Invoice.order_id == DoctorCommissionEntry.order_id)
        .where(
            Order.status != OrderStatus.cancelled,
            col(Invoice.is_voided).is_(False),
            Invoice.payment_status == PaymentStatus.paid,
        )
    )
    if payable_only:
        entries = entries.where(
            DoctorCommissionEntry.payout_status == PayoutStatus.pending
        )
        adjustments = adjustments.where(
            col(DoctorCommissionAdjustment.is_settled).is_(False)
        )
    return entries.union_all(adjustments).subquery()


def get_payable_lines(
    *,
    session: Session,
    skip: int,
    limit: int,
    doctor_id: uuid.UUID | None,
    search: str | None,
    sort_by: str | None,
    sort_order: SortOrder,
):
    lines = _line_statement()
    conditions = []
    if doctor_id:
        conditions.append(lines.c.doctor_id == doctor_id)
    if search:
        query = f"%{search.strip()}%"
        conditions.append(
            or_(
                lines.c.doctor_name.ilike(query),
                lines.c.accession_number.ilike(query),
                lines.c.invoice_number.ilike(query),
                lines.c.description.ilike(query),
            )
        )
    sort_columns = {
        "doctor_name": lines.c.doctor_name,
        "accession_number": lines.c.accession_number,
        "invoice_number": lines.c.invoice_number,
        "amount": lines.c.amount,
        "created_at": lines.c.created_at,
    }
    sort_column = sort_columns.get(sort_by or "created_at", lines.c.created_at)
    order_expr = sort_column.desc() if sort_order == SortOrder.desc else sort_column.asc()
    statement = (
        select(*lines.c)
        .where(*conditions)
        .order_by(order_expr, lines.c.source_id)
        .offset(skip)
        .limit(limit)
    )
    count = session.exec(
        select(func.count()).select_from(lines).where(*conditions)
    ).one()
    return list(session.exec(statement).all()), count


def get_payable_lines_by_sources(
    *,
    session: Session,
    entry_ids: list[uuid.UUID],
    adjustment_ids: list[uuid.UUID],
):
    lines = _line_statement()
    return list(
        session.exec(
            select(*lines.c)
            .where(
                or_(
                    (lines.c.line_type == "entry")
                    & lines.c.source_id.in_(entry_ids or [uuid.uuid4()]),
                    (lines.c.line_type == "adjustment")
                    & lines.c.source_id.in_(adjustment_ids or [uuid.uuid4()]),
                )
            )
            .order_by(lines.c.created_at, lines.c.source_id)
        ).all()
    )


def get_payable_sources_for_update(
    *,
    session: Session,
    entry_ids: list[uuid.UUID],
    adjustment_ids: list[uuid.UUID],
):
    entries = list(
        session.exec(
            select(DoctorCommissionEntry)
            .where(DoctorCommissionEntry.id.in_(entry_ids))
            .with_for_update()
        ).all()
    )
    adjustments = list(
        session.exec(
            select(DoctorCommissionAdjustment)
            .where(DoctorCommissionAdjustment.id.in_(adjustment_ids))
            .with_for_update()
        ).all()
    )
    return entries, adjustments


def get_eligibility_rows(
    *, session: Session, entry_ids: list[uuid.UUID]
) -> list[tuple[uuid.UUID, bool]]:
    return list(
        session.exec(
            select(
                DoctorCommissionEntry.id,
                func.count(Invoice.id) > 0,
            )
            .join(Order, DoctorCommissionEntry.order_id == Order.id)
            .join(
                Invoice,
                (Invoice.order_id == Order.id)
                & col(Invoice.is_voided).is_(False)
                & (Invoice.payment_status == PaymentStatus.paid),
                isouter=True,
            )
            .where(
                DoctorCommissionEntry.id.in_(entry_ids),
                Order.status != OrderStatus.cancelled,
            )
            .group_by(DoctorCommissionEntry.id)
        ).all()
    )


def get_payment_method(*, session: Session, payment_method_id: uuid.UUID):
    return session.exec(
        select(PaymentMethod).where(
            PaymentMethod.id == payment_method_id,
            col(PaymentMethod.is_deleted).is_(False),
        )
    ).first()


def create_payment(*, session: Session, payment: DoctorCommissionPayment):
    session.add(payment)
    session.flush()
    return payment


def add_payment_line(*, session: Session, line: DoctorCommissionPaymentEntry):
    session.add(line)


def get_payments(
    *,
    session: Session,
    skip: int,
    limit: int,
    doctor_id: uuid.UUID | None,
    payment_method_id: uuid.UUID | None,
    created_from: datetime | None,
    created_to: datetime | None,
    search: str | None,
    sort_by: str | None,
    sort_order: SortOrder,
):
    creator = aliased(User)
    line_count = func.count(DoctorCommissionPaymentEntry.id)
    conditions = []
    if doctor_id:
        conditions.append(DoctorCommissionPayment.doctor_id == doctor_id)
    if payment_method_id:
        conditions.append(
            DoctorCommissionPayment.payment_method_id == payment_method_id
        )
    if created_from:
        conditions.append(DoctorCommissionPayment.created_at >= created_from)
    if created_to:
        conditions.append(DoctorCommissionPayment.created_at <= created_to)
    if search:
        query = f"%{search.strip()}%"
        conditions.append(
            or_(
                _doctor_name().ilike(query),
                col(DoctorCommissionPayment.reference).ilike(query),
                cast(DoctorCommissionPayment.id, String).ilike(query),
            )
        )
    base = (
        select(
            DoctorCommissionPayment,
            Doctor,
            creator,
            PaymentMethod,
            line_count.label("line_count"),
        )
        .join(Doctor, DoctorCommissionPayment.doctor_id == Doctor.id)
        .join(creator, DoctorCommissionPayment.created_by == creator.id)
        .join(
            PaymentMethod,
            DoctorCommissionPayment.payment_method_id == PaymentMethod.id,
        )
        .join(
            DoctorCommissionPaymentEntry,
            DoctorCommissionPaymentEntry.commission_payment_id
            == DoctorCommissionPayment.id,
        )
        .where(*conditions)
        .group_by(DoctorCommissionPayment, Doctor, creator, PaymentMethod)
    )
    count = session.exec(
        select(func.count())
        .select_from(DoctorCommissionPayment)
        .join(Doctor, DoctorCommissionPayment.doctor_id == Doctor.id)
        .where(*conditions)
    ).one()
    sort_columns = {
        "doctor_name": Doctor.last_name,
        "total_commission_amount": DoctorCommissionPayment.total_commission_amount,
        "created_at": DoctorCommissionPayment.created_at,
    }
    sort_column = sort_columns.get(
        sort_by or "created_at", DoctorCommissionPayment.created_at
    )
    order_expr = col(sort_column).desc() if sort_order == SortOrder.desc else col(sort_column).asc()
    return list(session.exec(base.order_by(order_expr).offset(skip).limit(limit)).all()), count


def get_payment(*, session: Session, payment_id: uuid.UUID):
    creator = aliased(User)
    return session.exec(
        select(DoctorCommissionPayment, Doctor, creator, PaymentMethod)
        .join(Doctor, DoctorCommissionPayment.doctor_id == Doctor.id)
        .join(creator, DoctorCommissionPayment.created_by == creator.id)
        .join(
            PaymentMethod,
            DoctorCommissionPayment.payment_method_id == PaymentMethod.id,
        )
        .where(DoctorCommissionPayment.id == payment_id)
    ).first()


def get_payment_lines(*, session: Session, payment_id: uuid.UUID):
    links = DoctorCommissionPaymentEntry
    return list(
        session.exec(
            select(
                links.line_type,
                func.coalesce(
                    links.commission_entry_id, links.commission_adjustment_id
                ).label("source_id"),
                DoctorCommissionPayment.doctor_id.label("doctor_id"),
                _doctor_name().label("doctor_name"),
                links.order_id,
                links.accession_number,
                links.invoice_number,
                links.order_date,
                links.patient_first_name,
                links.patient_last_name,
                links.description,
                links.insured_net_amount,
                links.non_insured_net_amount,
                links.insured_commission_amount,
                links.non_insured_commission_amount,
                links.amount,
                links.source_created_at.label("created_at"),
            )
            .join(
                DoctorCommissionPayment,
                links.commission_payment_id == DoctorCommissionPayment.id,
            )
            .join(Doctor, DoctorCommissionPayment.doctor_id == Doctor.id)
            .where(links.commission_payment_id == payment_id)
            .order_by(links.source_created_at, links.id)
        ).all()
    )
