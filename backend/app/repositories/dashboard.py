# mypy: ignore-errors
# ty: ignore
"""Dashboard repository - aggregate database access only."""

from datetime import datetime

from sqlalchemy import case, distinct
from sqlalchemy.orm import aliased
from sqlmodel import Session, col, exists, func, select

from app.models.lis import (
    Analyte,
    AnalyteResult,
    CriticalNotification,
    Doctor,
    Invoice,
    Order,
    OrderItem,
    OrderItemSpecimen,
    OrderSpecimen,
    Patient,
    PaymentStatus,
    ResultStatus,
    SpecimenStatus,
    SpecimenType,
)
from app.models.user import User


def _active_specimen(specimen_alias=OrderSpecimen):
    replacement = aliased(OrderSpecimen)
    return (
        specimen_alias.is_superseded == False  # noqa: E712
    ) & ~exists(
        select(replacement.id).where(
            replacement.replaces_specimen_id == specimen_alias.id,
            replacement.is_superseded == False,  # noqa: E712
        )
    )


def order_status_counts(
    *, session: Session, created_from: datetime, created_to: datetime
):
    return list(
        session.exec(
            select(Order.status, func.count(Order.id))
            .where(Order.created_at >= created_from, Order.created_at <= created_to)
            .group_by(Order.status)
        ).all()
    )


def recent_orders(
    *, session: Session, created_from: datetime, created_to: datetime, limit: int
):
    return list(
        session.exec(
            select(Order, Patient, Doctor, Invoice)
            .join(Patient, Order.patient_id == Patient.id)
            .join(Doctor, Order.doctor_id == Doctor.id, isouter=True)
            .join(Invoice, Invoice.order_id == Order.id)
            .where(
                Order.created_at >= created_from,
                Order.created_at <= created_to,
                Invoice.is_voided == False,  # noqa: E712
            )
            .order_by(col(Order.created_at).desc(), col(Order.accession_number).desc())
            .limit(limit)
        ).all()
    )


def specimen_counts(
    *, session: Session, created_from: datetime, created_to: datetime
):
    return session.exec(
        select(
            func.coalesce(
                func.sum(case((OrderSpecimen.status == SpecimenStatus.pending, 1), else_=0)),
                0,
            ),
            func.coalesce(
                func.sum(case((OrderSpecimen.status == SpecimenStatus.collected, 1), else_=0)),
                0,
            ),
            func.coalesce(
                func.sum(case((OrderSpecimen.status == SpecimenStatus.rejected, 1), else_=0)),
                0,
            ),
        )
        .select_from(OrderSpecimen)
        .join(Order, OrderSpecimen.order_id == Order.id)
        .where(
            Order.created_at >= created_from,
            Order.created_at <= created_to,
            _active_specimen(),
        )
    ).one()


def oldest_waiting_specimen_order(
    *, session: Session, created_from: datetime, created_to: datetime
):
    pending_counts = (
        select(
            OrderSpecimen.order_id.label("order_id"),
            func.count(OrderSpecimen.id).label("pending_count"),
            func.min(OrderSpecimen.created_at).label("oldest_created_at"),
        )
        .where(
            OrderSpecimen.status == SpecimenStatus.pending,
            _active_specimen(),
        )
        .group_by(OrderSpecimen.order_id)
        .subquery()
    )
    collected_counts = (
        select(
            OrderSpecimen.order_id.label("order_id"),
            func.count(OrderSpecimen.id).label("collected_count"),
        )
        .where(
            OrderSpecimen.status == SpecimenStatus.collected,
            _active_specimen(),
        )
        .group_by(OrderSpecimen.order_id)
        .subquery()
    )
    rejected_counts = (
        select(
            OrderSpecimen.order_id.label("order_id"),
            func.count(OrderSpecimen.id).label("rejected_count"),
        )
        .where(OrderSpecimen.status == SpecimenStatus.rejected)
        .group_by(OrderSpecimen.order_id)
        .subquery()
    )
    type_summary = (
        select(
            OrderSpecimen.order_id.label("order_id"),
            func.string_agg(distinct(SpecimenType.name), ", ").label("summary"),
            func.count(OrderSpecimen.id).label("specimen_count"),
        )
        .join(SpecimenType, OrderSpecimen.specimen_type_id == SpecimenType.id)
        .where(_active_specimen())
        .group_by(OrderSpecimen.order_id)
        .subquery()
    )
    return session.exec(
        select(
            Order,
            Patient,
            Invoice,
            pending_counts.c.pending_count,
            func.coalesce(collected_counts.c.collected_count, 0),
            func.coalesce(rejected_counts.c.rejected_count, 0),
            func.coalesce(type_summary.c.specimen_count, 0),
            func.coalesce(type_summary.c.summary, ""),
        )
        .join(pending_counts, pending_counts.c.order_id == Order.id)
        .join(Patient, Order.patient_id == Patient.id)
        .join(Invoice, Invoice.order_id == Order.id)
        .join(collected_counts, collected_counts.c.order_id == Order.id, isouter=True)
        .join(rejected_counts, rejected_counts.c.order_id == Order.id, isouter=True)
        .join(type_summary, type_summary.c.order_id == Order.id, isouter=True)
        .where(
            Order.created_at >= created_from,
            Order.created_at <= created_to,
            Invoice.is_voided == False,  # noqa: E712
        )
        .order_by(pending_counts.c.oldest_created_at.asc())
        .limit(1)
    ).first()


def result_summary(
    *, session: Session, created_from: datetime, created_to: datetime
):
    queue_conditions = [
        Order.created_at >= created_from,
        Order.created_at <= created_to,
        OrderItem.is_active == True,  # noqa: E712
        OrderSpecimen.is_superseded == False,  # noqa: E712
        OrderSpecimen.status.in_([SpecimenStatus.collected, SpecimenStatus.processed]),
    ]
    entry_count = session.exec(
        select(func.count())
        .select_from(
            select(Order.id)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(OrderItemSpecimen, OrderItemSpecimen.order_item_id == OrderItem.id)
            .join(OrderSpecimen, OrderItemSpecimen.order_specimen_id == OrderSpecimen.id)
            .where(
                *queue_conditions,
                Order.status.in_(["collected", "in_progress", "partial_results"]),
            )
            .distinct()
            .subquery()
        )
    ).one()
    verification_count = session.exec(
        select(func.count())
        .select_from(
            select(Order.id)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(OrderItemSpecimen, OrderItemSpecimen.order_item_id == OrderItem.id)
            .join(OrderSpecimen, OrderItemSpecimen.order_specimen_id == OrderSpecimen.id)
            .join(AnalyteResult, AnalyteResult.order_item_id == OrderItem.id)
            .where(*queue_conditions, AnalyteResult.status == ResultStatus.resulted)
            .distinct()
            .subquery()
        )
    ).one()
    flags = session.exec(
        select(
            func.coalesce(
                func.sum(case((AnalyteResult.is_abnormal == True, 1), else_=0)),  # noqa: E712
                0,
            ),
            func.coalesce(
                func.sum(case((AnalyteResult.is_critical == True, 1), else_=0)),  # noqa: E712
                0,
            ),
        )
        .select_from(AnalyteResult)
        .join(OrderItem, AnalyteResult.order_item_id == OrderItem.id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(
            Order.created_at >= created_from,
            Order.created_at <= created_to,
            AnalyteResult.is_superseded == False,  # noqa: E712
        )
    ).one()
    return entry_count, verification_count, flags[0], flags[1]


def critical_summary(*, session: Session, limit: int):
    notified_by = User.__table__.alias("notified_by")
    notified_to = User.__table__.alias("notified_to")
    acknowledged_by = User.__table__.alias("acknowledged_by")
    count = session.exec(
        select(func.count())
        .select_from(CriticalNotification)
        .where(CriticalNotification.acknowledged == False)  # noqa: E712
    ).one()
    latest = list(
        session.execute(
            select(
                CriticalNotification,
                Order.accession_number,
                Patient.first_name,
                Patient.last_name,
                Patient.identifier,
                Analyte.code,
                Analyte.name,
                AnalyteResult.result_value,
                notified_by.c.full_name,
                notified_by.c.email,
                notified_to.c.full_name,
                notified_to.c.email,
                acknowledged_by.c.full_name,
                acknowledged_by.c.email,
            )
            .join(AnalyteResult, CriticalNotification.analyte_result_id == AnalyteResult.id)
            .join(Analyte, AnalyteResult.analyte_id == Analyte.id)
            .join(OrderItem, AnalyteResult.order_item_id == OrderItem.id)
            .join(Order, OrderItem.order_id == Order.id)
            .join(Patient, Order.patient_id == Patient.id)
            .join(notified_by, CriticalNotification.notified_by_id == notified_by.c.id)
            .join(notified_to, CriticalNotification.notified_to_id == notified_to.c.id)
            .join(
                acknowledged_by,
                CriticalNotification.acknowledged_by_id == acknowledged_by.c.id,
                isouter=True,
            )
            .where(CriticalNotification.acknowledged == False)  # noqa: E712
            .order_by(col(CriticalNotification.created_at).desc())
            .limit(limit)
        ).all()
    )
    return count, latest


def finance_summary(
    *, session: Session, created_from: datetime, created_to: datetime
):
    return session.exec(
        select(
            func.count(Invoice.id),
            func.coalesce(func.sum(Invoice.net_amount), 0),
            func.coalesce(func.sum(Invoice.amount_paid), 0),
            func.coalesce(func.sum(Invoice.net_amount - Invoice.amount_paid), 0),
            func.coalesce(
                func.sum(case((Invoice.payment_status == PaymentStatus.unpaid, 1), else_=0)),
                0,
            ),
            func.coalesce(
                func.sum(case((Invoice.payment_status == PaymentStatus.partial, 1), else_=0)),
                0,
            ),
        )
        .where(
            Invoice.created_at >= created_from,
            Invoice.created_at <= created_to,
            Invoice.is_voided == False,  # noqa: E712
        )
    ).one()


def trend_rows(
    *, session: Session, created_from: datetime, created_to: datetime, granularity: str
):
    order_bucket = func.date_trunc(granularity, Order.created_at).label("bucket")
    order_rows = session.exec(
        select(
            order_bucket,
            func.count(Order.id).label("orders"),
            func.coalesce(func.sum(Invoice.net_amount), 0).label("revenue"),
        )
        .select_from(Order)
        .join(
            Invoice,
            (Invoice.order_id == Order.id) & (Invoice.is_voided == False),  # noqa: E712
            isouter=True,
        )
        .where(Order.created_at >= created_from, Order.created_at <= created_to)
        .group_by(order_bucket)
    ).all()

    specimen_bucket = func.date_trunc(granularity, OrderSpecimen.created_at).label("bucket")
    specimen_rows = session.exec(
        select(specimen_bucket, func.count(OrderSpecimen.id).label("specimens"))
        .select_from(OrderSpecimen)
        .where(
            OrderSpecimen.created_at >= created_from,
            OrderSpecimen.created_at <= created_to,
            _active_specimen(),
        )
        .group_by(specimen_bucket)
    ).all()

    result_bucket = func.date_trunc(granularity, AnalyteResult.created_at).label("bucket")
    result_rows = session.exec(
        select(result_bucket, func.count(AnalyteResult.id).label("results"))
        .select_from(AnalyteResult)
        .where(
            AnalyteResult.created_at >= created_from,
            AnalyteResult.created_at <= created_to,
            AnalyteResult.is_superseded == False,  # noqa: E712
        )
        .group_by(result_bucket)
    ).all()

    buckets = {}
    for bucket_value, orders, revenue in order_rows:
        buckets[bucket_value] = {
            "orders": orders,
            "specimens": 0,
            "results": 0,
            "revenue": revenue,
        }
    for bucket_value, specimens in specimen_rows:
        buckets.setdefault(
            bucket_value,
            {"orders": 0, "specimens": 0, "results": 0, "revenue": 0},
        )["specimens"] = specimens
    for bucket_value, results in result_rows:
        buckets.setdefault(
            bucket_value,
            {"orders": 0, "specimens": 0, "results": 0, "revenue": 0},
        )["results"] = results

    return [
        (
            bucket_value,
            values["orders"],
            values["specimens"],
            values["results"],
            values["revenue"],
        )
        for bucket_value, values in sorted(buckets.items())
    ]
