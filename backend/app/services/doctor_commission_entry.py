"""Doctor commission entry management."""

import uuid
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlmodel import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.lis import (
    AuditAction,
    AuditLog,
    DoctorCommissionAdjustment,
    DoctorCommissionAdjustmentCreate,
    DoctorCommissionAdjustmentPublic,
    DoctorCommissionEntryDetailPublic,
    DoctorCommissionEntryListItemPublic,
    DoctorCommissionEntryListPublic,
    PayoutStatus,
    SortOrder,
)
from app.repositories import doctor_commission_entry as entry_repo


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _list_item(row) -> DoctorCommissionEntryListItemPublic:
    return DoctorCommissionEntryListItemPublic(
        id=row.id,
        order_id=row.order_id,
        doctor_id=row.doctor_id,
        order_net_amount=row.order_net_amount,
        insured_net_amount=row.insured_net_amount,
        insured_rate_applied=row.insured_rate_applied,
        insured_commission_amount=row.insured_commission_amount,
        non_insured_net_amount=row.non_insured_net_amount,
        non_insured_rate_applied=row.non_insured_rate_applied,
        non_insured_commission_amount=row.non_insured_commission_amount,
        discount_allocation_policy=row.discount_allocation_policy,
        commission_amount=row.commission_amount,
        payout_status=row.payout_status,
        paid_at=row.paid_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
        doctor_name=row.doctor_name,
        patient_id=row.patient_id,
        patient_name=row.patient_name,
        accession_number=row.accession_number,
        invoice_number=row.invoice_number,
        total_adjustments=row.total_adjustments,
        unsettled_adjustments=row.unsettled_adjustments,
        outstanding_amount=row.outstanding_amount,
        adjustment_count=row.adjustment_count,
    )


def get_entries(
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
) -> DoctorCommissionEntryListPublic:
    rows, count = entry_repo.get_all(
        session=session,
        skip=skip,
        limit=limit,
        search=search,
        doctor_id=doctor_id,
        payout_status=payout_status,
        created_from=created_from,
        created_to=created_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return DoctorCommissionEntryListPublic(
        data=[_list_item(row) for row in rows], count=count
    )


def _adjustment_public(row) -> DoctorCommissionAdjustmentPublic:
    adjustment, creator, _revision = row
    return DoctorCommissionAdjustmentPublic(
        id=adjustment.id,
        commission_entry_id=adjustment.commission_entry_id,
        order_revision_id=adjustment.order_revision_id,
        created_by_id=adjustment.created_by_id,
        created_by_name=(
            creator.full_name or creator.email if creator is not None else None
        ),
        source="manual" if adjustment.created_by_id is not None else "revision",
        amount=adjustment.amount,
        reason=adjustment.reason,
        is_settled=adjustment.is_settled,
        created_at=adjustment.created_at,
    )


def get_entry(
    *, session: Session, entry_id: uuid.UUID
) -> DoctorCommissionEntryDetailPublic:
    row = entry_repo.get_detail(session=session, entry_id=entry_id)
    if row is None:
        raise NotFoundError("Écriture de commission introuvable")
    adjustments = entry_repo.get_adjustments(session=session, entry_id=entry_id)
    return DoctorCommissionEntryDetailPublic(
        **_list_item(row).model_dump(),
        adjustments=[_adjustment_public(item) for item in adjustments],
    )


def create_adjustment(
    *,
    session: Session,
    entry_id: uuid.UUID,
    request: DoctorCommissionAdjustmentCreate,
    created_by_id: uuid.UUID,
) -> DoctorCommissionEntryDetailPublic:
    entry = entry_repo.get_for_update(session=session, entry_id=entry_id)
    if entry is None:
        raise NotFoundError("Écriture de commission introuvable")
    amount = _money(request.amount)
    reason = request.reason.strip()
    if amount == 0:
        raise BusinessRuleError(
            "Le montant de l'ajustement doit être différent de zéro"
        )
    if not reason:
        raise BusinessRuleError("Le motif de l'ajustement est requis")

    adjustment = entry_repo.create_adjustment(
        session=session,
        adjustment=DoctorCommissionAdjustment(
            commission_entry_id=entry.id,
            created_by_id=created_by_id,
            amount=amount,
            reason=reason,
        ),
    )
    session.add(
        AuditLog(
            table_name="doctor_commission_adjustments",
            record_id=adjustment.id,
            action=AuditAction.insert,
            new_values={
                "commission_entry_id": str(entry.id),
                "amount": str(amount),
                "reason": reason,
                "source": "manual",
            },
            performed_by_id=created_by_id,
        )
    )
    session.commit()
    return get_entry(session=session, entry_id=entry.id)
