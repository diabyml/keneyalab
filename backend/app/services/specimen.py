"""Specimen collection, rejection, and recollection workflows."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlmodel import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.lis import (
    OrderItemSpecimen,
    OrderSpecimen,
    OrderSpecimenDetailPublic,
    OrderStatus,
    PaymentStatus,
    RejectionReasonPublic,
    RejectionReasonsPublic,
    SpecimenCollectRequest,
    SpecimenQueueItemPublic,
    SpecimenQueuePublic,
    SpecimenRejectRequest,
    SpecimenStatus,
    SpecimenTypePublic,
    SpecimenTypesPublic,
    SpecimenWorkspacePublic,
)
from app.repositories import order as order_repo
from app.repositories import specimen as specimen_repo


def _display_name(user) -> str | None:
    return (user.full_name or user.email) if user else None


def _specimen_detail(row) -> OrderSpecimenDetailPublic:
    specimen, specimen_type, collector, rejector, reason, replacement_id = row
    return OrderSpecimenDetailPublic(
        **specimen.model_dump(),
        specimen_type_name=specimen_type.name,
        specimen_type_color=specimen_type.color,
        collected_by_name=_display_name(collector),
        rejected_by_name=_display_name(rejector),
        rejection_reason_name=reason.name if reason else None,
        is_active_attempt=replacement_id is None and not specimen.is_superseded,
    )


def get_workspace(
    *, session: Session, order_id: uuid.UUID
) -> SpecimenWorkspacePublic:
    header = order_repo.get_order_header(session=session, order_id=order_id)
    if header is None:
        raise NotFoundError("Demande non trouvée")
    order, patient, _, _, _, _, _ = header
    invoice = order_repo.get_invoice(session=session, order_id=order_id)
    if invoice is None:
        raise NotFoundError("Facture de la demande non trouvée")
    return SpecimenWorkspacePublic(
        order_id=order.id,
        accession_number=order.accession_number,
        patient_identifier=patient.identifier,
        patient_name=f"{patient.first_name} {patient.last_name}",
        order_status=order.status,
        payment_status=invoice.payment_status,
        balance_due=max(
            Decimal("0.00"), invoice.net_amount - (invoice.amount_paid or Decimal("0"))
        ),
        specimens=[
            _specimen_detail(row)
            for row in specimen_repo.get_order_specimens(
                session=session, order_id=order_id
            )
        ],
    )


def get_queue(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 25,
    search: str | None = None,
    view: str = "waiting",
    specimen_type_id: uuid.UUID | None = None,
    payment_status: PaymentStatus | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    sort_by: str | None = None,
    sort_order="desc",
) -> SpecimenQueuePublic:
    rows, count = specimen_repo.get_queue(
        session=session,
        skip=skip,
        limit=limit,
        search=search,
        view=view,
        specimen_type_id=specimen_type_id,
        payment_status=payment_status,
        created_from=created_from,
        created_to=created_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    data: list[SpecimenQueueItemPublic] = []
    for order, patient, invoice in rows:
        details = [
            _specimen_detail(row)
            for row in specimen_repo.get_order_specimens(
                session=session, order_id=order.id
            )
        ]
        active = [item for item in details if item.is_active_attempt]
        names = list(dict.fromkeys(item.specimen_type_name for item in active))
        data.append(
            SpecimenQueueItemPublic(
                order_id=order.id,
                accession_number=order.accession_number,
                patient_id=patient.id,
                patient_identifier=patient.identifier,
                patient_name=f"{patient.first_name} {patient.last_name}",
                order_status=order.status,
                payment_status=invoice.payment_status,
                created_at=order.created_at,
                pending_count=sum(
                    item.status == SpecimenStatus.pending for item in active
                ),
                collected_count=sum(
                    item.status == SpecimenStatus.collected for item in active
                ),
                rejected_count=sum(
                    item.status == SpecimenStatus.rejected for item in details
                ),
                specimen_count=len(active),
                specimen_summary=", ".join(names),
            )
        )
    return SpecimenQueuePublic(data=data, count=count)


def _ensure_mutable_order(order) -> None:
    if order.status not in {OrderStatus.registered, OrderStatus.collected}:
        raise ConflictError(
            "Les prélèvements ne peuvent plus être modifiés pour cette demande"
        )


def _refresh_order_status(*, session: Session, order_id: uuid.UUID) -> None:
    order = order_repo.get_by_id(session=session, order_id=order_id)
    if order is None:
        raise NotFoundError("Demande non trouvée")
    active = specimen_repo.get_active_specimens(session=session, order_id=order_id)
    order.status = (
        OrderStatus.collected
        if active and all(item.status == SpecimenStatus.collected for item in active)
        else OrderStatus.registered
    )
    session.add(order)


def collect(
    *,
    session: Session,
    request: SpecimenCollectRequest,
    collected_by_id: uuid.UUID,
) -> SpecimenWorkspacePublic:
    specimens = specimen_repo.get_by_ids(
        session=session, specimen_ids=request.specimen_ids
    )
    if len(specimens) != len(set(request.specimen_ids)):
        raise NotFoundError("Un ou plusieurs prélèvements sont introuvables")
    order_ids = {item.order_id for item in specimens}
    if len(order_ids) != 1:
        raise BusinessRuleError(
            "Les prélèvements sélectionnés doivent appartenir à la même demande"
        )
    order_id = order_ids.pop()
    order = order_repo.get_by_id(session=session, order_id=order_id)
    if order is None:
        raise NotFoundError("Demande non trouvée")
    _ensure_mutable_order(order)
    active_ids = {
        item.id
        for item in specimen_repo.get_active_specimens(
            session=session, order_id=order_id
        )
    }
    if any(
        item.id not in active_ids or item.status != SpecimenStatus.pending
        for item in specimens
    ):
        raise ConflictError(
            "Un prélèvement sélectionné a déjà été traité ou remplacé"
        )
    collected_at = request.collection_time or datetime.now(timezone.utc)
    for specimen in specimens:
        specimen.status = SpecimenStatus.collected
        specimen.collection_time = collected_at
        specimen.collected_by = collected_by_id
        session.add(specimen)
    _refresh_order_status(session=session, order_id=order_id)
    session.commit()
    return get_workspace(session=session, order_id=order_id)


def collect_all(
    *, session: Session, order_id: uuid.UUID, collected_by_id: uuid.UUID
) -> SpecimenWorkspacePublic:
    order = order_repo.get_by_id(session=session, order_id=order_id)
    if order is None:
        raise NotFoundError("Demande non trouvée")
    _ensure_mutable_order(order)
    pending = [
        item
        for item in specimen_repo.get_active_specimens(
            session=session, order_id=order_id
        )
        if item.status == SpecimenStatus.pending
    ]
    if not pending:
        raise ConflictError("Aucun prélèvement en attente")
    collected_at = datetime.now(timezone.utc)
    for specimen in pending:
        specimen.status = SpecimenStatus.collected
        specimen.collection_time = collected_at
        specimen.collected_by = collected_by_id
        session.add(specimen)
    _refresh_order_status(session=session, order_id=order_id)
    session.commit()
    return get_workspace(session=session, order_id=order_id)


def reject(
    *,
    session: Session,
    specimen_id: uuid.UUID,
    request: SpecimenRejectRequest,
    rejected_by_id: uuid.UUID,
) -> SpecimenWorkspacePublic:
    specimen = specimen_repo.get_by_id(session=session, specimen_id=specimen_id)
    if specimen is None:
        raise NotFoundError("Prélèvement non trouvé")
    order = order_repo.get_by_id(session=session, order_id=specimen.order_id)
    if order is None:
        raise NotFoundError("Demande non trouvée")
    _ensure_mutable_order(order)
    active_ids = {
        item.id
        for item in specimen_repo.get_active_specimens(
            session=session, order_id=order.id
        )
    }
    if (
        specimen.id not in active_ids
        or specimen.status
        not in {SpecimenStatus.pending, SpecimenStatus.collected}
    ):
        raise ConflictError("Ce prélèvement a déjà été traité ou remplacé")
    reason = specimen_repo.get_rejection_reason(
        session=session, reason_id=request.rejection_reason_id
    )
    if reason is None or reason.is_deleted:
        raise BusinessRuleError("Motif de rejet non disponible")

    specimen.status = SpecimenStatus.rejected
    specimen.rejection_reason_id = request.rejection_reason_id
    specimen.notes = (request.notes or "").strip() or None
    specimen.rejected_at = datetime.now(timezone.utc)
    specimen.rejected_by = rejected_by_id
    session.add(specimen)

    replacement = specimen_repo.create(
        session=session,
        db_obj=OrderSpecimen(
            order_id=specimen.order_id,
            specimen_type_id=specimen.specimen_type_id,
            status=SpecimenStatus.pending,
            required_volume_ml=specimen.required_volume_ml,
            collection_instructions=specimen.collection_instructions,
            replaces_specimen_id=specimen.id,
            attempt_number=specimen.attempt_number + 1,
        ),
    )
    for order_item_id in specimen_repo.get_order_item_ids(
        session=session, specimen_id=specimen.id
    ):
        specimen_repo.create(
            session=session,
            db_obj=OrderItemSpecimen(
                order_item_id=order_item_id,
                order_specimen_id=replacement.id,
            ),
        )
    _refresh_order_status(session=session, order_id=order.id)
    session.commit()
    return get_workspace(session=session, order_id=order.id)


def get_rejection_reason_options(
    *, session: Session, search: str | None, skip: int, limit: int
) -> RejectionReasonsPublic:
    rows, count = specimen_repo.get_rejection_reasons(
        session=session, search=search, skip=skip, limit=limit
    )
    return RejectionReasonsPublic(
        data=[RejectionReasonPublic.model_validate(item) for item in rows],
        count=count,
    )


def get_specimen_type_options(
    *, session: Session, search: str | None, skip: int, limit: int
) -> SpecimenTypesPublic:
    rows, count = specimen_repo.get_specimen_types(
        session=session, search=search, skip=skip, limit=limit
    )
    return SpecimenTypesPublic(
        data=[SpecimenTypePublic.model_validate(item) for item in rows],
        count=count,
    )
