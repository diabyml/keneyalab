"""Specimen collection repository - database access only."""

import uuid
from datetime import datetime

from sqlalchemy.orm import aliased
from sqlmodel import Session, col, exists, func, or_, select

from app.models.lis import (
    Invoice,
    Order,
    OrderItemSpecimen,
    OrderSpecimen,
    Patient,
    PaymentStatus,
    RejectionReason,
    SortOrder,
    SpecimenStatus,
    SpecimenType,
)
from app.models.user import User

SORT_COLUMNS = {
    "accession_number": Order.accession_number,
    "patient_name": Patient.last_name,
    "created_at": Order.created_at,
}


def _is_active(specimen_alias=OrderSpecimen):
    replacement = aliased(OrderSpecimen)
    return (
        specimen_alias.is_superseded == False  # noqa: E712
    ) & ~exists(
        select(replacement.id).where(
            replacement.replaces_specimen_id == specimen_alias.id,
            replacement.is_superseded == False,  # noqa: E712
        )
    )


def get_queue(
    *,
    session: Session,
    skip: int,
    limit: int,
    search: str | None,
    view: str,
    specimen_type_id: uuid.UUID | None,
    payment_status: PaymentStatus | None,
    created_from: datetime | None,
    created_to: datetime | None,
    sort_by: str | None,
    sort_order: SortOrder,
):
    specimen_match = [OrderSpecimen.order_id == Order.id]
    if view == "waiting":
        specimen_match.extend(
            [
                _is_active(),
                OrderSpecimen.status == SpecimenStatus.pending,
            ]
        )
    else:
        specimen_match.append(
            OrderSpecimen.status.in_(
                [SpecimenStatus.collected, SpecimenStatus.rejected]
            )
        )
    if specimen_type_id is not None:
        specimen_match.append(OrderSpecimen.specimen_type_id == specimen_type_id)

    conditions = [exists(select(OrderSpecimen.id).where(*specimen_match))]
    if search:
        query = f"%{search.strip()}%"
        conditions.append(
            or_(
                col(Order.accession_number).ilike(query),
                col(Patient.identifier).ilike(query),
                col(Patient.first_name).ilike(query),
                col(Patient.last_name).ilike(query),
            )
        )
    if payment_status is not None:
        conditions.append(Invoice.payment_status == payment_status)
    if created_from is not None:
        conditions.append(Order.created_at >= created_from)
    if created_to is not None:
        conditions.append(Order.created_at <= created_to)

    base = (
        select(Order, Patient, Invoice)
        .join(Patient, Order.patient_id == Patient.id)
        .join(Invoice, Invoice.order_id == Order.id)
        .where(Invoice.is_voided == False, *conditions)  # noqa: E712
    )
    count_query = (
        select(func.count())
        .select_from(Order)
        .join(Patient, Order.patient_id == Patient.id)
        .join(Invoice, Invoice.order_id == Order.id)
        .where(Invoice.is_voided == False, *conditions)  # noqa: E712
    )
    sort_column = SORT_COLUMNS.get(sort_by or "created_at", Order.created_at)
    order_expr = (
        col(sort_column).desc()
        if sort_order == SortOrder.desc
        else col(sort_column).asc()
    )
    rows = session.exec(
        base.order_by(order_expr, col(Order.accession_number).desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return list(rows), session.exec(count_query).one()


def get_order_specimens(*, session: Session, order_id: uuid.UUID):
    collector = aliased(User)
    rejector = aliased(User)
    replacement = aliased(OrderSpecimen)
    return list(
        session.exec(
            select(
                OrderSpecimen,
                SpecimenType,
                collector,
                rejector,
                RejectionReason,
                replacement.id,
            )
            .join(SpecimenType, OrderSpecimen.specimen_type_id == SpecimenType.id)
            .join(collector, OrderSpecimen.collected_by == collector.id, isouter=True)
            .join(rejector, OrderSpecimen.rejected_by == rejector.id, isouter=True)
            .join(
                RejectionReason,
                OrderSpecimen.rejection_reason_id == RejectionReason.id,
                isouter=True,
            )
            .join(
                replacement,
                replacement.replaces_specimen_id == OrderSpecimen.id,
                isouter=True,
            )
            .where(OrderSpecimen.order_id == order_id)
            .order_by(
                col(SpecimenType.name).asc(),
                col(OrderSpecimen.attempt_number).desc(),
            )
        ).all()
    )


def get_active_specimens(*, session: Session, order_id: uuid.UUID):
    return list(
        session.exec(
            select(OrderSpecimen).where(
                OrderSpecimen.order_id == order_id,
                _is_active(),
            )
        ).all()
    )


def get_by_ids(*, session: Session, specimen_ids: list[uuid.UUID]):
    return list(
        session.exec(
            select(OrderSpecimen).where(OrderSpecimen.id.in_(specimen_ids))
        ).all()
    )


def get_by_id(*, session: Session, specimen_id: uuid.UUID):
    return session.get(OrderSpecimen, specimen_id)


def get_order_item_ids(*, session: Session, specimen_id: uuid.UUID):
    return list(
        session.exec(
            select(OrderItemSpecimen.order_item_id).where(
                OrderItemSpecimen.order_specimen_id == specimen_id
            )
        ).all()
    )


def create(*, session: Session, db_obj):
    session.add(db_obj)
    session.flush()
    return db_obj


def get_rejection_reasons(
    *, session: Session, search: str | None, skip: int, limit: int
):
    conditions = [RejectionReason.is_deleted == False]  # noqa: E712
    if search:
        conditions.append(col(RejectionReason.name).ilike(f"%{search.strip()}%"))
    count = session.exec(
        select(func.count()).select_from(RejectionReason).where(*conditions)
    ).one()
    rows = session.exec(
        select(RejectionReason)
        .where(*conditions)
        .order_by(col(RejectionReason.name).asc())
        .offset(skip)
        .limit(limit)
    ).all()
    return list(rows), count


def get_rejection_reason(*, session: Session, reason_id: uuid.UUID):
    return session.get(RejectionReason, reason_id)


def get_specimen_types(
    *, session: Session, search: str | None, skip: int, limit: int
):
    conditions = [SpecimenType.is_deleted == False]  # noqa: E712
    if search:
        conditions.append(col(SpecimenType.name).ilike(f"%{search.strip()}%"))
    count = session.exec(
        select(func.count()).select_from(SpecimenType).where(*conditions)
    ).one()
    rows = session.exec(
        select(SpecimenType)
        .where(*conditions)
        .order_by(col(SpecimenType.name).asc())
        .offset(skip)
        .limit(limit)
    ).all()
    return list(rows), count
