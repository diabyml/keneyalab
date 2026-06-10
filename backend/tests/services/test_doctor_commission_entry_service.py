import uuid
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import BusinessRuleError
from app.models.lis import (
    DiscountAllocationPolicy,
    DoctorCommissionAdjustmentCreate,
    DoctorCommissionEntry,
    PayoutStatus,
)
from app.services import doctor_commission_entry as entry_service


def _entry() -> DoctorCommissionEntry:
    return DoctorCommissionEntry(
        order_id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        order_net_amount=Decimal("1000.00"),
        insured_net_amount=Decimal("400.00"),
        insured_rate_applied=Decimal("0.0500"),
        insured_commission_amount=Decimal("20.00"),
        non_insured_net_amount=Decimal("600.00"),
        non_insured_rate_applied=Decimal("0.1000"),
        non_insured_commission_amount=Decimal("60.00"),
        discount_allocation_policy=DiscountAllocationPolicy.proportional,
        commission_amount=Decimal("80.00"),
        payout_status=PayoutStatus.paid,
        paid_at=datetime.now(timezone.utc),
    )


def _detail_row(entry: DoctorCommissionEntry):
    return SimpleNamespace(
        **entry.model_dump(),
        doctor_name="Awa Traoré",
        patient_id=uuid.uuid4(),
        patient_name="Mariam Diallo",
        accession_number="ORD-001",
        invoice_number="FAC-001",
        total_adjustments=Decimal("-5.00"),
        unsettled_adjustments=Decimal("-5.00"),
        outstanding_amount=Decimal("-5.00"),
        adjustment_count=1,
    )


def test_create_manual_adjustment_is_audited(monkeypatch: pytest.MonkeyPatch) -> None:
    session = MagicMock()
    entry = _entry()
    creator_id = uuid.uuid4()
    created_adjustment = SimpleNamespace(id=uuid.uuid4())

    monkeypatch.setattr(
        entry_service.entry_repo,
        "get_for_update",
        lambda **_: entry,
    )
    create_mock = MagicMock(return_value=created_adjustment)
    monkeypatch.setattr(
        entry_service.entry_repo,
        "create_adjustment",
        create_mock,
    )
    monkeypatch.setattr(
        entry_service.entry_repo,
        "get_detail",
        lambda **_: _detail_row(entry),
    )
    monkeypatch.setattr(
        entry_service.entry_repo,
        "get_adjustments",
        lambda **_: [],
    )

    result = entry_service.create_adjustment(
        session=session,
        entry_id=entry.id,
        request=DoctorCommissionAdjustmentCreate(
            amount=Decimal("-5.005"),
            reason="  Correction manuelle  ",
        ),
        created_by_id=creator_id,
    )

    adjustment = create_mock.call_args.kwargs["adjustment"]
    assert adjustment.amount == Decimal("-5.01")
    assert adjustment.reason == "Correction manuelle"
    assert adjustment.created_by_id == creator_id
    assert adjustment.order_revision_id is None
    assert result.outstanding_amount == Decimal("-5.00")
    session.add.assert_called_once()
    audit = session.add.call_args.args[0]
    assert audit.record_id == created_adjustment.id
    assert audit.new_values["amount"] == "-5.01"
    session.commit.assert_called_once()


def test_create_manual_adjustment_rejects_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        entry_service.entry_repo,
        "get_for_update",
        lambda **_: _entry(),
    )

    with pytest.raises(BusinessRuleError, match="différent de zéro"):
        entry_service.create_adjustment(
            session=MagicMock(),
            entry_id=uuid.uuid4(),
            request=DoctorCommissionAdjustmentCreate(
                amount=Decimal("0"),
                reason="Correction",
            ),
            created_by_id=uuid.uuid4(),
        )
