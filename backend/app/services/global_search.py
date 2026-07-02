from sqlmodel import Session, col, or_, select

from app.models import User
from app.models.lis import (
    Catalog,
    Doctor,
    GlobalSearchResultPublic,
    GlobalSearchResultsPublic,
    Invoice,
    Order,
    Patient,
    Reagent,
)
from app.services import permission as permission_service


def _can(*, session: Session, user: User, resource: str, action: str) -> bool:
    return permission_service.check_permission(
        session=session,
        user=user,
        resource=resource,
        action=action,
    )


def _patient_name(patient: Patient) -> str:
    return f"{patient.first_name} {patient.last_name}".strip()


def _doctor_name(doctor: Doctor) -> str:
    return f"{doctor.first_name} {doctor.last_name}".strip()


def _pattern(query: str) -> str:
    return f"%{query.strip()}%"


def _order_results(
    *, session: Session, query: str, limit: int, kind: str, resource: str, href: str
) -> list[GlobalSearchResultPublic]:
    pattern = _pattern(query)
    rows = session.exec(
        select(Order, Patient, Doctor)
        .join(Patient, Order.patient_id == Patient.id)
        .join(Doctor, Order.doctor_id == Doctor.id, isouter=True)
        .where(
            or_(
                col(Order.accession_number).ilike(pattern),
                col(Patient.identifier).ilike(pattern),
                col(Patient.first_name).ilike(pattern),
                col(Patient.last_name).ilike(pattern),
                col(Doctor.first_name).ilike(pattern),
                col(Doctor.last_name).ilike(pattern),
            )
        )
        .order_by(col(Order.created_at).desc(), col(Order.accession_number).desc())
        .limit(limit)
    ).all()
    return [
        GlobalSearchResultPublic(
            kind=kind,
            title=order.accession_number,
            subtitle=f"{_patient_name(patient)} · {patient.identifier}",
            badge=order.status.value,
            href=href.format(order_id=order.id),
            resource=resource,
            record_id=order.id,
        )
        for order, patient, _doctor in rows
    ]


def _patients(
    *, session: Session, query: str, limit: int
) -> list[GlobalSearchResultPublic]:
    pattern = _pattern(query)
    rows = session.exec(
        select(Patient)
        .where(
            col(Patient.is_deleted).is_(False),
            or_(
                col(Patient.identifier).ilike(pattern),
                col(Patient.first_name).ilike(pattern),
                col(Patient.last_name).ilike(pattern),
                col(Patient.phone).ilike(pattern),
            ),
        )
        .order_by(col(Patient.last_name).asc(), col(Patient.first_name).asc())
        .limit(limit)
    ).all()
    return [
        GlobalSearchResultPublic(
            kind="patients",
            title=_patient_name(patient),
            subtitle=patient.identifier,
            badge="Patient",
            href=f"/patients/{patient.id}",
            resource="patients",
            record_id=patient.id,
        )
        for patient in rows
    ]


def _doctors(
    *, session: Session, query: str, limit: int
) -> list[GlobalSearchResultPublic]:
    pattern = _pattern(query)
    rows = session.exec(
        select(Doctor)
        .where(
            col(Doctor.is_deleted).is_(False),
            or_(
                col(Doctor.first_name).ilike(pattern),
                col(Doctor.last_name).ilike(pattern),
                col(Doctor.provenance).ilike(pattern),
                col(Doctor.phone).ilike(pattern),
            ),
        )
        .order_by(col(Doctor.last_name).asc(), col(Doctor.first_name).asc())
        .limit(limit)
    ).all()
    return [
        GlobalSearchResultPublic(
            kind="doctors",
            title=_doctor_name(doctor),
            subtitle=doctor.provenance,
            badge="Médecin",
            href=f"/doctors/{doctor.id}",
            resource="doctors",
            record_id=doctor.id,
        )
        for doctor in rows
    ]


def _invoices(
    *, session: Session, query: str, limit: int
) -> list[GlobalSearchResultPublic]:
    pattern = _pattern(query)
    rows = session.exec(
        select(Invoice, Order, Patient)
        .join(Order, Invoice.order_id == Order.id)
        .join(Patient, Order.patient_id == Patient.id)
        .where(
            or_(
                col(Invoice.invoice_number).ilike(pattern),
                col(Order.accession_number).ilike(pattern),
                col(Patient.identifier).ilike(pattern),
                col(Patient.first_name).ilike(pattern),
                col(Patient.last_name).ilike(pattern),
            )
        )
        .order_by(col(Invoice.created_at).desc(), col(Invoice.invoice_number).desc())
        .limit(limit)
    ).all()
    return [
        GlobalSearchResultPublic(
            kind="invoices",
            title=invoice.invoice_number,
            subtitle=f"{order.accession_number} · {_patient_name(patient)}",
            badge=invoice.payment_status.value,
            href=f"/invoices/{invoice.id}",
            resource="invoices",
            record_id=invoice.id,
        )
        for invoice, order, patient in rows
    ]


def _catalog(
    *, session: Session, query: str, limit: int
) -> list[GlobalSearchResultPublic]:
    pattern = _pattern(query)
    rows = session.exec(
        select(Catalog)
        .where(
            col(Catalog.is_deleted).is_(False),
            or_(col(Catalog.code).ilike(pattern), col(Catalog.name).ilike(pattern)),
        )
        .order_by(col(Catalog.code).asc(), col(Catalog.name).asc())
        .limit(limit)
    ).all()
    return [
        GlobalSearchResultPublic(
            kind="catalog",
            title=catalog.name,
            subtitle=catalog.code,
            badge=catalog.type.value,
            href="/configurations/catalogue",
            resource="catalog",
            record_id=catalog.id,
        )
        for catalog in rows
    ]


def _reagents(
    *, session: Session, query: str, limit: int
) -> list[GlobalSearchResultPublic]:
    pattern = _pattern(query)
    rows = session.exec(
        select(Reagent)
        .where(
            col(Reagent.is_deleted).is_(False),
            or_(col(Reagent.code).ilike(pattern), col(Reagent.name).ilike(pattern)),
        )
        .order_by(col(Reagent.name).asc())
        .limit(limit)
    ).all()
    return [
        GlobalSearchResultPublic(
            kind="reagents",
            title=reagent.name,
            subtitle=reagent.code,
            badge="Réactif",
            href="/reagents",
            resource="reagents",
            record_id=reagent.id,
        )
        for reagent in rows
    ]


def search(
    *,
    session: Session,
    user: User,
    query: str,
    limit: int,
) -> GlobalSearchResultsPublic:
    normalized_query = query.strip()
    if len(normalized_query) < 2:
        return GlobalSearchResultsPublic(data=[])

    per_group_limit = max(1, min(limit, 10))
    results: list[GlobalSearchResultPublic] = []

    if _can(session=session, user=user, resource="orders", action="view"):
        results.extend(
            _order_results(
                session=session,
                query=normalized_query,
                limit=per_group_limit,
                kind="orders",
                resource="orders",
                href="/orders/{order_id}",
            )
        )
    if _can(session=session, user=user, resource="patients", action="view"):
        results.extend(
            _patients(session=session, query=normalized_query, limit=per_group_limit)
        )
    if _can(session=session, user=user, resource="doctors", action="view"):
        results.extend(
            _doctors(session=session, query=normalized_query, limit=per_group_limit)
        )
    if _can(session=session, user=user, resource="invoices", action="view"):
        results.extend(
            _invoices(session=session, query=normalized_query, limit=per_group_limit)
        )
    if (
        _can(session=session, user=user, resource="catalog", action="view")
        or _can(session=session, user=user, resource="orders", action="create")
        or _can(session=session, user=user, resource="orders", action="edit")
    ):
        results.extend(
            _catalog(session=session, query=normalized_query, limit=per_group_limit)
        )
    if _can(session=session, user=user, resource="specimens", action="view"):
        results.extend(
            _order_results(
                session=session,
                query=normalized_query,
                limit=per_group_limit,
                kind="specimens",
                resource="specimens",
                href="/orders/{order_id}",
            )
        )
    if _can(session=session, user=user, resource="results", action="view"):
        results.extend(
            _order_results(
                session=session,
                query=normalized_query,
                limit=per_group_limit,
                kind="results",
                resource="results",
                href="/results/{order_id}",
            )
        )
    if _can(session=session, user=user, resource="reagents", action="view"):
        results.extend(
            _reagents(session=session, query=normalized_query, limit=per_group_limit)
        )

    return GlobalSearchResultsPublic(data=results)
