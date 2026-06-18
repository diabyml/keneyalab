from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, col, delete, select

from app.core.config import settings
from app.models import User
from app.models.lis import (
    GenderType,
    Invoice,
    Order,
    OrderStatus,
    Patient,
    PaymentStatus,
)
from app.models.rbac import Permission, Role, RolePermission, UserRole
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email, random_lower_string

PREFIX = f"{settings.API_V1_STR}/dashboard"


def _short_code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


@pytest.fixture(autouse=True)
def cleanup_dashboard_records(db: Session):
    _delete_dashboard_records(db)
    yield
    _delete_dashboard_records(db)


def _delete_dashboard_records(db: Session) -> None:
    db.exec(delete(Invoice).where(col(Invoice.invoice_number).like("FAC-DASH-%")))
    db.exec(delete(Order).where(col(Order.accession_number).like("ORD-DASH-%")))
    db.exec(delete(Patient).where(col(Patient.identifier).like("PAT-DASH-%")))
    db.commit()


def _superuser(db: Session) -> User:
    user = db.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).one()
    return user


def _create_order_with_invoice(
    db: Session,
    *,
    accession_number: str,
    invoice_number: str,
    created_at: datetime,
    net_amount: Decimal = Decimal("1000.00"),
    amount_paid: Decimal = Decimal("0.00"),
    status: OrderStatus = OrderStatus.registered,
) -> Order:
    patient = Patient(
        identifier=_short_code("PAT-DASH"),
        first_name="Awa",
        last_name="Traoré",
        date_of_birth=date(1990, 1, 1),
        gender=GenderType.female,
        created_at=created_at,
        updated_at=created_at,
    )
    db.add(patient)
    db.flush()
    order = Order(
        accession_number=accession_number,
        patient_id=patient.id,
        status=status,
        created_by=_superuser(db).id,
        created_at=created_at,
        updated_at=created_at,
    )
    db.add(order)
    db.flush()
    db.add(
        Invoice(
            order_id=order.id,
            invoice_number=invoice_number,
            total_amount=net_amount,
            net_amount=net_amount,
            amount_paid=amount_paid,
            payment_status=(
                PaymentStatus.paid if amount_paid >= net_amount else PaymentStatus.partial
            ),
            created_by_id=_superuser(db).id,
            created_at=created_at,
            updated_at=created_at,
        )
    )
    db.commit()
    db.refresh(order)
    return order


def _headers_with_only_orders_view(
    *, client: TestClient, db: Session
) -> dict[str, str]:
    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=db)
    user = db.exec(select(User).where(User.email == email)).one()
    permission = db.exec(
        select(Permission).where(
            Permission.resource == "orders",
            Permission.action == "view",
        )
    ).one()
    role = Role(name=f"dashboard-orders-{random_lower_string()}")
    db.add(role)
    db.flush()
    db.add(RolePermission(role_id=role.id, permission_id=permission.id))
    db.add(UserRole(user_id=user.id, role_id=role.id, assigned_by_id=_superuser(db).id))
    db.commit()
    return headers


def test_dashboard_superuser_receives_sections(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(f"{PREFIX}/", headers=superuser_token_headers)

    assert response.status_code == 200
    content = response.json()
    assert content["orders"] is not None
    assert content["specimens"] is not None
    assert content["results"] is not None
    assert content["critical"] is not None
    assert content["finance"] is not None
    assert isinstance(content["quick_actions"], list)


def test_dashboard_is_permission_gated(
    client: TestClient, db: Session
) -> None:
    headers = _headers_with_only_orders_view(client=client, db=db)

    response = client.get(f"{PREFIX}/", headers=headers)

    assert response.status_code == 200
    content = response.json()
    assert content["orders"] is not None
    assert content["finance"] is None
    assert content["results"] is None
    assert content["critical"] is None


def test_dashboard_date_range_filters_counts_and_sums(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    inside = datetime(2026, 6, 15, 10, 0, tzinfo=timezone.utc)
    outside = datetime(2026, 6, 14, 10, 0, tzinfo=timezone.utc)
    outside_accession = _short_code("ORD-DASH")
    _create_order_with_invoice(
        db,
        accession_number=_short_code("ORD-DASH"),
        invoice_number=_short_code("FAC-DASH"),
        created_at=inside,
        net_amount=Decimal("2500.00"),
        amount_paid=Decimal("1500.00"),
    )
    _create_order_with_invoice(
        db,
        accession_number=outside_accession,
        invoice_number=_short_code("FAC-DASH"),
        created_at=outside,
        net_amount=Decimal("9000.00"),
        amount_paid=Decimal("9000.00"),
    )

    response = client.get(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        params={
            "created_from": "2026-06-15T00:00:00Z",
            "created_to": "2026-06-15T23:59:59Z",
        },
    )

    assert response.status_code == 200
    content = response.json()
    order_total = next(
        item for item in content["orders"]["metrics"] if item["key"] == "total"
    )
    net_billed = next(
        item for item in content["finance"]["metrics"] if item["key"] == "net_billed"
    )
    assert order_total["value"] >= 1
    assert Decimal(net_billed["value"]) >= Decimal("2500.00")
    assert all(
        item["accession_number"] != outside_accession
        for item in content["orders"]["recent"]
    )


def test_dashboard_requires_authentication(client: TestClient) -> None:
    response = client.get(f"{PREFIX}/")

    assert response.status_code == 401
