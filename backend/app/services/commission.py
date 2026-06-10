"""Doctor commission calculation and persistence helpers."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.models.lis import DiscountAllocationPolicy, DoctorCommissionEntry

MONEY = Decimal("0.01")


@dataclass(frozen=True)
class CommissionSnapshot:
    order_net_amount: Decimal
    insured_net_amount: Decimal
    insured_rate_applied: Decimal
    insured_commission_amount: Decimal
    non_insured_net_amount: Decimal
    non_insured_rate_applied: Decimal
    non_insured_commission_amount: Decimal
    discount_allocation_policy: DiscountAllocationPolicy
    commission_amount: Decimal


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def calculate_commission(
    *,
    lines: list[tuple[Decimal, bool]],
    discount: Decimal,
    insured_rate: Decimal,
    non_insured_rate: Decimal,
    policy: DiscountAllocationPolicy,
) -> CommissionSnapshot:
    insured_gross = _money(
        sum(
            (amount for amount, is_insured in lines if is_insured),
            Decimal("0"),
        )
    )
    non_insured_gross = _money(
        sum(
            (amount for amount, is_insured in lines if not is_insured),
            Decimal("0"),
        )
    )
    total = _money(insured_gross + non_insured_gross)
    discount = _money(discount)
    if discount < 0 or discount > total:
        raise ValueError("La remise doit être comprise entre zéro et le total")

    if policy == DiscountAllocationPolicy.non_insured_first:
        non_insured_discount = min(discount, non_insured_gross)
        insured_discount = discount - non_insured_discount
    elif policy == DiscountAllocationPolicy.insured_first:
        insured_discount = min(discount, insured_gross)
        non_insured_discount = discount - insured_discount
    else:
        insured_discount = (
            _money(discount * insured_gross / total) if total > 0 else Decimal("0")
        )
        insured_discount = min(
            max(insured_discount, discount - non_insured_gross, Decimal("0")),
            insured_gross,
            discount,
        )
        non_insured_discount = discount - insured_discount

    insured_net = _money(insured_gross - insured_discount)
    non_insured_net = _money(non_insured_gross - non_insured_discount)
    order_net = _money(total - discount)
    # Keep the category sum equal to the invoice net after proportional rounding.
    non_insured_net = _money(order_net - insured_net)

    insured_commission = _money(insured_net * insured_rate)
    non_insured_commission = _money(non_insured_net * non_insured_rate)
    return CommissionSnapshot(
        order_net_amount=order_net,
        insured_net_amount=insured_net,
        insured_rate_applied=insured_rate,
        insured_commission_amount=insured_commission,
        non_insured_net_amount=non_insured_net,
        non_insured_rate_applied=non_insured_rate,
        non_insured_commission_amount=non_insured_commission,
        discount_allocation_policy=policy,
        commission_amount=_money(insured_commission + non_insured_commission),
    )


def apply_snapshot(
    *, entry: DoctorCommissionEntry, snapshot: CommissionSnapshot
) -> DoctorCommissionEntry:
    entry.order_net_amount = snapshot.order_net_amount
    entry.insured_net_amount = snapshot.insured_net_amount
    entry.insured_rate_applied = snapshot.insured_rate_applied
    entry.insured_commission_amount = snapshot.insured_commission_amount
    entry.non_insured_net_amount = snapshot.non_insured_net_amount
    entry.non_insured_rate_applied = snapshot.non_insured_rate_applied
    entry.non_insured_commission_amount = snapshot.non_insured_commission_amount
    entry.discount_allocation_policy = snapshot.discount_allocation_policy
    entry.commission_amount = snapshot.commission_amount
    return entry
