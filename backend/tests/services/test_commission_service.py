from decimal import Decimal

import pytest

from app.models.lis import DiscountAllocationPolicy
from app.services.commission import calculate_commission


@pytest.mark.parametrize(
    ("policy", "insured_net", "non_insured_net"),
    [
        (
            DiscountAllocationPolicy.non_insured_first,
            Decimal("300.00"),
            Decimal("100.00"),
        ),
        (
            DiscountAllocationPolicy.insured_first,
            Decimal("200.00"),
            Decimal("200.00"),
        ),
        (
            DiscountAllocationPolicy.proportional,
            Decimal("240.00"),
            Decimal("160.00"),
        ),
    ],
)
def test_calculate_mixed_commission_allocates_discount(
    policy: DiscountAllocationPolicy,
    insured_net: Decimal,
    non_insured_net: Decimal,
) -> None:
    snapshot = calculate_commission(
        lines=[
            (Decimal("300.00"), True),
            (Decimal("200.00"), False),
        ],
        discount=Decimal("100.00"),
        insured_rate=Decimal("0.0500"),
        non_insured_rate=Decimal("0.1000"),
        policy=policy,
    )

    assert snapshot.order_net_amount == Decimal("400.00")
    assert snapshot.insured_net_amount == insured_net
    assert snapshot.non_insured_net_amount == non_insured_net
    assert snapshot.insured_net_amount + snapshot.non_insured_net_amount == (
        snapshot.order_net_amount
    )
    assert snapshot.insured_commission_amount == (
        insured_net * Decimal("0.0500")
    )
    assert snapshot.non_insured_commission_amount == (
        non_insured_net * Decimal("0.1000")
    )
    assert snapshot.commission_amount == (
        snapshot.insured_commission_amount
        + snapshot.non_insured_commission_amount
    )


def test_priority_discount_spills_into_other_category() -> None:
    snapshot = calculate_commission(
        lines=[
            (Decimal("300.00"), True),
            (Decimal("50.00"), False),
        ],
        discount=Decimal("100.00"),
        insured_rate=Decimal("0.0500"),
        non_insured_rate=Decimal("0.1000"),
        policy=DiscountAllocationPolicy.non_insured_first,
    )

    assert snapshot.non_insured_net_amount == Decimal("0.00")
    assert snapshot.insured_net_amount == Decimal("250.00")


def test_proportional_rounding_reconciles_to_invoice_net() -> None:
    snapshot = calculate_commission(
        lines=[
            (Decimal("100.00"), True),
            (Decimal("200.00"), False),
        ],
        discount=Decimal("0.01"),
        insured_rate=Decimal("0.0500"),
        non_insured_rate=Decimal("0.1000"),
        policy=DiscountAllocationPolicy.proportional,
    )

    assert snapshot.insured_net_amount == Decimal("100.00")
    assert snapshot.non_insured_net_amount == Decimal("199.99")
    assert snapshot.insured_net_amount + snapshot.non_insured_net_amount == (
        Decimal("299.99")
    )
