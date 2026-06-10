"""Order repository - pure database access only."""

import uuid
from datetime import date, datetime

from sqlalchemy import text
from sqlmodel import Session, col, func, or_, select

from app.models import User
from app.models.lis import (
    AnalyteResult,
    Catalog,
    Doctor,
    Invoice,
    Order,
    OrderItem,
    OrderItemSpecimen,
    OrderRevision,
    OrderSpecimen,
    Patient,
    PaymentStatus,
    PaymentTransaction,
    Report,
    SortOrder,
)

SORT_COLUMNS = {
    "accession_number": Order.accession_number,
    "status": Order.status,
    "created_at": Order.created_at,
}


def next_daily_value(
    *, session: Session, sequence_date: date, sequence_type: str
) -> int:
    result = session.execute(
        text(
            """
            INSERT INTO daily_sequences (
                id, sequence_date, sequence_type, current_value
            )
            VALUES (gen_random_uuid(), :sequence_date, :sequence_type, 1)
            ON CONFLICT (sequence_date, sequence_type)
            DO UPDATE SET current_value = daily_sequences.current_value + 1
            RETURNING current_value
            """
        ),
        {"sequence_date": sequence_date, "sequence_type": sequence_type},
    )
    return int(result.scalar_one())


def get_all(
    *,
    session: Session,
    skip: int,
    limit: int,
    search: str | None,
    status,
    patient_id: uuid.UUID | None,
    doctor_id: uuid.UUID | None,
    created_from: datetime | None,
    created_to: datetime | None,
    sort_by: str | None,
    sort_order: SortOrder,
):
    conditions = []
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
    if status is not None:
        conditions.append(Order.status == status)
    if patient_id is not None:
        conditions.append(Order.patient_id == patient_id)
    if doctor_id is not None:
        conditions.append(Order.doctor_id == doctor_id)
    if created_from is not None:
        conditions.append(Order.created_at >= created_from)
    if created_to is not None:
        conditions.append(Order.created_at <= created_to)

    base = (
        select(Order, Patient, Doctor, Invoice)
        .join(Patient, Order.patient_id == Patient.id)
        .join(Doctor, Order.doctor_id == Doctor.id, isouter=True)
        .join(Invoice, Invoice.order_id == Order.id)
        .where(Invoice.is_voided == False)  # noqa: E712
    )
    count_query = (
        select(func.count())
        .select_from(Order)
        .join(Patient, Order.patient_id == Patient.id)
    )
    if conditions:
        base = base.where(*conditions)
        count_query = count_query.where(*conditions)

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


def get_by_id(*, session: Session, order_id: uuid.UUID) -> Order | None:
    return session.get(Order, order_id)


def get_for_update(*, session: Session, order_id: uuid.UUID) -> Order | None:
    return session.exec(
        select(Order).where(Order.id == order_id).with_for_update()
    ).first()


def create(*, session: Session, db_obj):
    session.add(db_obj)
    session.flush()
    return db_obj


def get_items(*, session: Session, order_id: uuid.UUID):
    return list(
        session.exec(
            select(OrderItem, Catalog)
            .join(Catalog, OrderItem.catalog_id == Catalog.id)
            .where(OrderItem.order_id == order_id, OrderItem.is_active == True)  # noqa: E712
            .order_by(col(OrderItem.sort_order).asc(), col(Catalog.code).asc())
        ).all()
    )


def get_specimens(*, session: Session, order_id: uuid.UUID):
    from app.models.lis import SpecimenType

    return list(
        session.exec(
            select(OrderSpecimen, SpecimenType)
            .join(SpecimenType, OrderSpecimen.specimen_type_id == SpecimenType.id)
            .where(
                OrderSpecimen.order_id == order_id,
                OrderSpecimen.is_superseded == False,  # noqa: E712
            )
            .order_by(col(SpecimenType.name).asc())
        ).all()
    )


def get_item_specimen_ids(*, session: Session, order_id: uuid.UUID):
    rows = session.exec(
        select(OrderItemSpecimen.order_item_id, OrderItemSpecimen.order_specimen_id)
        .join(OrderItem, OrderItemSpecimen.order_item_id == OrderItem.id)
        .where(
            OrderItem.order_id == order_id,
            OrderItem.is_active == True,  # noqa: E712
        )
    ).all()
    result: dict[uuid.UUID, list[uuid.UUID]] = {}
    for item_id, specimen_id in rows:
        result.setdefault(item_id, []).append(specimen_id)
    return result


def get_invoice(*, session: Session, order_id: uuid.UUID) -> Invoice | None:
    return session.exec(
        select(Invoice).where(
            Invoice.order_id == order_id,
            Invoice.is_voided == False,  # noqa: E712
        )
    ).first()


def get_revisions(*, session: Session, order_id: uuid.UUID):
    from app.models import User

    return list(
        session.exec(
            select(OrderRevision, User)
            .join(User, OrderRevision.performed_by_id == User.id, isouter=True)
            .where(OrderRevision.order_id == order_id)
            .order_by(col(OrderRevision.revision_number).desc())
        ).all()
    )


def get_results_for_items(*, session: Session, item_ids: list[uuid.UUID]):
    if not item_ids:
        return []
    return list(
        session.exec(
            select(AnalyteResult).where(AnalyteResult.order_item_id.in_(item_ids))
        ).all()
    )


def get_active_reports(*, session: Session, order_id: uuid.UUID):
    return list(
        session.exec(
            select(Report).where(
                Report.order_id == order_id,
                Report.is_voided == False,  # noqa: E712
            )
        ).all()
    )


def get_payments(*, session: Session, invoice_id: uuid.UUID):
    from app.models.lis import PaymentMethod

    return list(
        session.exec(
            select(PaymentTransaction, PaymentMethod)
            .join(
                PaymentMethod,
                PaymentTransaction.payment_method_id == PaymentMethod.id,
            )
            .where(PaymentTransaction.invoice_id == invoice_id)
            .order_by(col(PaymentTransaction.created_at).asc())
        ).all()
    )


def get_order_header(*, session: Session, order_id: uuid.UUID):
    from app.models.lis import (
        InsuranceProvider,
        PatientContext,
        PatientInsurance,
    )

    return session.exec(
        select(
            Order,
            Patient,
            Doctor,
            PatientInsurance,
            InsuranceProvider,
            PatientContext,
            User,
        )
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
        .join(
            PatientContext,
            Order.patient_context_id == PatientContext.id,
            isouter=True,
        )
        .join(User, Order.created_by == User.id, isouter=True)
        .where(Order.id == order_id)
    ).first()


def recalculate_invoice_payment(*, session: Session, invoice: Invoice) -> None:
    from app.models.lis import PaymentTransactionStatus

    paid = session.exec(
        select(func.coalesce(func.sum(PaymentTransaction.amount), 0)).where(
            PaymentTransaction.invoice_id == invoice.id,
            PaymentTransaction.status == PaymentTransactionStatus.completed,
        )
    ).one()
    invoice.amount_paid = paid
    if paid <= 0:
        invoice.payment_status = PaymentStatus.unpaid
    elif paid >= invoice.net_amount:
        invoice.payment_status = PaymentStatus.paid
    else:
        invoice.payment_status = PaymentStatus.partial
    session.add(invoice)
