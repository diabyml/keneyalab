"""Doctor commission payment business workflow."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlmodel import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.lis import (
    DoctorCommissionPayableLinePublic,
    DoctorCommissionPayableLinesPublic,
    DoctorCommissionPayment,
    DoctorCommissionPaymentCreate,
    DoctorCommissionPaymentDetailPublic,
    DoctorCommissionPaymentEntry,
    DoctorCommissionPaymentLinePublic,
    DoctorCommissionPaymentListItemPublic,
    DoctorCommissionPaymentListPublic,
    DoctorCommissionPaymentPreviewPublic,
    PayoutStatus,
    SortOrder,
)
from app.repositories import doctor_commission_payment as payment_repo


def _parse_line_ids(line_ids: list[str]) -> tuple[list[uuid.UUID], list[uuid.UUID]]:
    if len(line_ids) != len(set(line_ids)):
        raise BusinessRuleError("Une même ligne ne peut pas être sélectionnée deux fois")
    entries: list[uuid.UUID] = []
    adjustments: list[uuid.UUID] = []
    for line_id in line_ids:
        try:
            line_type, raw_id = line_id.split(":", 1)
            source_id = uuid.UUID(raw_id)
        except (ValueError, AttributeError) as exc:
            raise BusinessRuleError("Identifiant de ligne de commission invalide") from exc
        if line_type == "entry":
            entries.append(source_id)
        elif line_type == "adjustment":
            adjustments.append(source_id)
        else:
            raise BusinessRuleError("Type de ligne de commission invalide")
    return entries, adjustments


def _public_line(row, *, detail: bool = False):
    model = (
        DoctorCommissionPaymentLinePublic
        if detail
        else DoctorCommissionPayableLinePublic
    )
    return model(
        id=f"{row.line_type}:{row.source_id}",
        line_type=row.line_type,
        source_id=row.source_id,
        doctor_id=row.doctor_id,
        doctor_name=row.doctor_name,
        order_id=row.order_id,
        accession_number=row.accession_number,
        invoice_number=row.invoice_number,
        order_date=row.order_date,
        patient_first_name=row.patient_first_name,
        patient_last_name=row.patient_last_name,
        description=row.description,
        insured_net_amount=row.insured_net_amount,
        non_insured_net_amount=row.non_insured_net_amount,
        insured_commission_amount=row.insured_commission_amount,
        non_insured_commission_amount=row.non_insured_commission_amount,
        amount=row.amount,
        created_at=row.created_at,
    )


def get_payable_lines(
    *,
    session: Session,
    skip: int,
    limit: int,
    doctor_id: uuid.UUID | None,
    search: str | None,
    sort_by: str | None,
    sort_order: SortOrder,
) -> DoctorCommissionPayableLinesPublic:
    rows, count = payment_repo.get_payable_lines(
        session=session,
        skip=skip,
        limit=limit,
        doctor_id=doctor_id,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return DoctorCommissionPayableLinesPublic(
        data=[_public_line(row) for row in rows], count=count
    )


def _validated_selection(
    *, session: Session, request: DoctorCommissionPaymentCreate, lock: bool
):
    entry_ids, adjustment_ids = _parse_line_ids(request.line_ids)
    method = payment_repo.get_payment_method(
        session=session, payment_method_id=request.payment_method_id
    )
    if not method:
        raise NotFoundError("Méthode de paiement introuvable")
    if lock:
        entries, adjustments = payment_repo.get_payable_sources_for_update(
            session=session,
            entry_ids=entry_ids,
            adjustment_ids=adjustment_ids,
        )
        if len(entries) != len(entry_ids) or len(adjustments) != len(adjustment_ids):
            raise ConflictError("Une ou plusieurs lignes ne sont plus disponibles")
        if any(entry.payout_status != PayoutStatus.pending for entry in entries):
            raise ConflictError("Une commission sélectionnée a déjà été payée")
        if any(adjustment.is_settled for adjustment in adjustments):
            raise ConflictError("Un ajustement sélectionné a déjà été soldé")
    rows = payment_repo.get_payable_lines_by_sources(
        session=session, entry_ids=entry_ids, adjustment_ids=adjustment_ids
    )
    if len(rows) != len(request.line_ids):
        raise ConflictError(
            "Une ou plusieurs lignes sont inéligibles ou ont déjà été réglées"
        )
    doctor_ids = {row.doctor_id for row in rows}
    if len(doctor_ids) != 1:
        raise BusinessRuleError(
            "Toutes les lignes d'un paiement doivent appartenir au même médecin"
        )
    total = sum((row.amount for row in rows), Decimal("0.00"))
    if total <= 0:
        raise BusinessRuleError("Le total du paiement doit être strictement positif")
    return rows, method, total, entry_ids, adjustment_ids


def preview_payment(
    *, session: Session, request: DoctorCommissionPaymentCreate
) -> DoctorCommissionPaymentPreviewPublic:
    rows, method, total, _, _ = _validated_selection(
        session=session, request=request, lock=False
    )
    first = rows[0]
    return DoctorCommissionPaymentPreviewPublic(
        doctor_id=first.doctor_id,
        doctor_name=first.doctor_name,
        payment_method_id=method.id,
        payment_method_name=method.name,
        reference=request.reference.strip() if request.reference else None,
        note=request.note.strip() if request.note else None,
        lines=[_public_line(row) for row in rows],
        total_commission_amount=total,
    )


def create_payment(
    *,
    session: Session,
    request: DoctorCommissionPaymentCreate,
    created_by: uuid.UUID,
) -> DoctorCommissionPaymentDetailPublic:
    rows, _, total, entry_ids, adjustment_ids = _validated_selection(
        session=session, request=request, lock=True
    )
    payment = payment_repo.create_payment(
        session=session,
        payment=DoctorCommissionPayment(
            doctor_id=rows[0].doctor_id,
            total_commission_amount=total,
            created_by=created_by,
            payment_method_id=request.payment_method_id,
            reference=request.reference.strip() if request.reference else None,
            note=request.note.strip() if request.note else None,
        ),
    )
    now = datetime.now().astimezone()
    entries, adjustments = payment_repo.get_payable_sources_for_update(
        session=session,
        entry_ids=entry_ids,
        adjustment_ids=adjustment_ids,
    )
    rows_by_id = {(row.line_type, row.source_id): row for row in rows}
    for entry in entries:
        row = rows_by_id[("entry", entry.id)]
        entry.payout_status = PayoutStatus.paid
        entry.paid_at = now
        session.add(entry)
        payment_repo.add_payment_line(
            session=session,
            line=DoctorCommissionPaymentEntry(
                commission_payment_id=payment.id,
                commission_entry_id=entry.id,
                order_id=row.order_id,
                accession_number=row.accession_number,
                invoice_number=row.invoice_number,
                order_date=row.order_date,
                patient_first_name=row.patient_first_name,
                patient_last_name=row.patient_last_name,
                line_type=row.line_type,
                description=row.description,
                insured_net_amount=row.insured_net_amount,
                non_insured_net_amount=row.non_insured_net_amount,
                insured_commission_amount=row.insured_commission_amount,
                non_insured_commission_amount=row.non_insured_commission_amount,
                amount=row.amount,
                source_created_at=row.created_at,
            ),
        )
    for adjustment in adjustments:
        row = rows_by_id[("adjustment", adjustment.id)]
        adjustment.is_settled = True
        session.add(adjustment)
        payment_repo.add_payment_line(
            session=session,
            line=DoctorCommissionPaymentEntry(
                commission_payment_id=payment.id,
                commission_adjustment_id=adjustment.id,
                order_id=row.order_id,
                accession_number=row.accession_number,
                invoice_number=row.invoice_number,
                order_date=row.order_date,
                patient_first_name=row.patient_first_name,
                patient_last_name=row.patient_last_name,
                line_type=row.line_type,
                description=row.description,
                insured_net_amount=row.insured_net_amount,
                non_insured_net_amount=row.non_insured_net_amount,
                insured_commission_amount=row.insured_commission_amount,
                non_insured_commission_amount=row.non_insured_commission_amount,
                amount=row.amount,
                source_created_at=row.created_at,
            ),
        )
    try:
        session.commit()
    except Exception as exc:
        session.rollback()
        raise ConflictError(
            "Le paiement n'a pas pu être créé car les lignes ont été modifiées"
        ) from exc
    return get_payment(session=session, payment_id=payment.id)


def _list_item(row) -> DoctorCommissionPaymentListItemPublic:
    payment, doctor, creator, method, line_count = row
    return DoctorCommissionPaymentListItemPublic(
        **payment.model_dump(),
        doctor_name=f"{doctor.first_name} {doctor.last_name}",
        created_by_name=creator.full_name or creator.email,
        payment_method_name=method.name,
        line_count=line_count,
    )


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
) -> DoctorCommissionPaymentListPublic:
    rows, count = payment_repo.get_payments(
        session=session,
        skip=skip,
        limit=limit,
        doctor_id=doctor_id,
        payment_method_id=payment_method_id,
        created_from=created_from,
        created_to=created_to,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return DoctorCommissionPaymentListPublic(
        data=[_list_item(row) for row in rows], count=count
    )


def get_payment(
    *, session: Session, payment_id: uuid.UUID
) -> DoctorCommissionPaymentDetailPublic:
    row = payment_repo.get_payment(session=session, payment_id=payment_id)
    if not row:
        raise NotFoundError("Paiement de commissions introuvable")
    payment, doctor, creator, method = row
    lines = payment_repo.get_payment_lines(session=session, payment_id=payment_id)
    return DoctorCommissionPaymentDetailPublic(
        **payment.model_dump(),
        doctor_name=f"{doctor.first_name} {doctor.last_name}",
        created_by_name=creator.full_name or creator.email,
        payment_method_name=method.name,
        line_count=len(lines),
        lines=[_public_line(line, detail=True) for line in lines],
    )
