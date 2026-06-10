"""Doctor commission entry repository - database access only."""

import uuid
from datetime import datetime

from sqlalchemy import case
from sqlalchemy.orm import aliased
from sqlmodel import Session, col, func, or_, select

from app.models.lis import (
    Doctor,
    DoctorCommissionAdjustment,
    DoctorCommissionEntry,
    Invoice,
    Order,
    OrderRevision,
    Patient,
    PayoutStatus,
    SortOrder,
)
from app.models.user import User


def _doctor_name():
    return func.concat(Doctor.first_name, " ", Doctor.last_name)


def _patient_name():
    return func.concat(Patient.first_name, " ", Patient.last_name)


def _adjustment_totals():
    return (
        select(
            DoctorCommissionAdjustment.commission_entry_id.label("entry_id"),
            func.coalesce(func.sum(DoctorCommissionAdjustment.amount), 0).label(
                "total_adjustments"
            ),
            func.coalesce(
                func.sum(
                    case(
                        (
                            col(DoctorCommissionAdjustment.is_settled).is_(False),
                            DoctorCommissionAdjustment.amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("unsettled_adjustments"),
            func.count(DoctorCommissionAdjustment.id).label("adjustment_count"),
        )
        .group_by(DoctorCommissionAdjustment.commission_entry_id)
        .subquery()
    )


def _entry_statement():
    adjustments = _adjustment_totals()
    total_adjustments = func.coalesce(adjustments.c.total_adjustments, 0)
    unsettled_adjustments = func.coalesce(adjustments.c.unsettled_adjustments, 0)
    base_outstanding = case(
        (
            DoctorCommissionEntry.payout_status == PayoutStatus.pending,
            DoctorCommissionEntry.commission_amount,
        ),
        else_=0,
    )
    return (
        select(
            DoctorCommissionEntry,
            _doctor_name().label("doctor_name"),
            Patient.id.label("patient_id"),
            _patient_name().label("patient_name"),
            Order.accession_number.label("accession_number"),
            Invoice.invoice_number.label("invoice_number"),
            total_adjustments.label("total_adjustments"),
            unsettled_adjustments.label("unsettled_adjustments"),
            (base_outstanding + unsettled_adjustments).label("outstanding_amount"),
            func.coalesce(adjustments.c.adjustment_count, 0).label("adjustment_count"),
        )
        .join(Doctor, DoctorCommissionEntry.doctor_id == Doctor.id)
        .join(Order, DoctorCommissionEntry.order_id == Order.id)
        .join(Patient, Order.patient_id == Patient.id)
        .join(
            Invoice,
            (Invoice.order_id == Order.id) & col(Invoice.is_voided).is_(False),
        )
        .join(
            adjustments,
            adjustments.c.entry_id == DoctorCommissionEntry.id,
            isouter=True,
        )
    )


def get_all(
    *,
    session: Session,
    skip: int,
    limit: int,
    search: str | None,
    doctor_id: uuid.UUID | None,
    payout_status: PayoutStatus | None,
    created_from: datetime | None,
    created_to: datetime | None,
    sort_by: str | None,
    sort_order: SortOrder,
):
    conditions = []
    if doctor_id is not None:
        conditions.append(DoctorCommissionEntry.doctor_id == doctor_id)
    if payout_status is not None:
        conditions.append(DoctorCommissionEntry.payout_status == payout_status)
    if created_from is not None:
        conditions.append(DoctorCommissionEntry.created_at >= created_from)
    if created_to is not None:
        conditions.append(DoctorCommissionEntry.created_at <= created_to)
    if search:
        query = f"%{search.strip()}%"
        conditions.append(
            or_(
                _doctor_name().ilike(query),
                _patient_name().ilike(query),
                col(Patient.identifier).ilike(query),
                col(Order.accession_number).ilike(query),
                col(Invoice.invoice_number).ilike(query),
            )
        )

    base = _entry_statement().where(*conditions)
    rows = base.subquery()
    sort_columns = {
        "created_at": rows.c.created_at,
        "doctor_name": rows.c.doctor_name,
        "accession_number": rows.c.accession_number,
        "commission_amount": rows.c.commission_amount,
        "outstanding_amount": rows.c.outstanding_amount,
    }
    sort_column = sort_columns.get(sort_by or "created_at", rows.c.created_at)
    order_expr = (
        sort_column.desc() if sort_order == SortOrder.desc else sort_column.asc()
    )
    statement = (
        select(*rows.c).order_by(order_expr, rows.c.id).offset(skip).limit(limit)
    )
    count = session.exec(select(func.count()).select_from(rows)).one()
    return list(session.exec(statement).all()), count


def get_detail(*, session: Session, entry_id: uuid.UUID):
    rows = _entry_statement().subquery()
    return session.exec(select(*rows.c).where(rows.c.id == entry_id)).first()


def get_for_update(*, session: Session, entry_id: uuid.UUID):
    return session.exec(
        select(DoctorCommissionEntry)
        .where(DoctorCommissionEntry.id == entry_id)
        .with_for_update()
    ).first()


def get_adjustments(*, session: Session, entry_id: uuid.UUID):
    creator = aliased(User)
    return list(
        session.exec(
            select(DoctorCommissionAdjustment, creator, OrderRevision)
            .join(
                creator,
                DoctorCommissionAdjustment.created_by_id == creator.id,
                isouter=True,
            )
            .join(
                OrderRevision,
                DoctorCommissionAdjustment.order_revision_id == OrderRevision.id,
                isouter=True,
            )
            .where(DoctorCommissionAdjustment.commission_entry_id == entry_id)
            .order_by(
                col(DoctorCommissionAdjustment.created_at).desc(),
                col(DoctorCommissionAdjustment.id).desc(),
            )
        ).all()
    )


def create_adjustment(
    *, session: Session, adjustment: DoctorCommissionAdjustment
) -> DoctorCommissionAdjustment:
    session.add(adjustment)
    session.flush()
    return adjustment
