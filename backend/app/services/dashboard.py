"""Dashboard business logic and permission-aware response shaping."""

from datetime import datetime, time, timezone
from decimal import Decimal

from sqlmodel import Session

from app.models import User
from app.models.lis import (
    CriticalNotificationDetailPublic,
    DashboardActionPublic,
    DashboardCriticalPublic,
    DashboardFinancePublic,
    DashboardMetricPublic,
    DashboardOrdersPublic,
    DashboardPublic,
    DashboardResultsPublic,
    DashboardSpecimensPublic,
    DashboardStatusPointPublic,
    DashboardTrendPointPublic,
    OrderListItemPublic,
    OrderStatus,
    SpecimenQueueItemPublic,
)
from app.repositories import dashboard as dashboard_repo
from app.services import permission as permission_service

ORDER_STATUS_LABELS = {
    OrderStatus.registered: "Enregistrées",
    OrderStatus.collected: "Prélevées",
    OrderStatus.in_progress: "En cours",
    OrderStatus.partial_results: "Résultats partiels",
    OrderStatus.completed: "Terminées",
    OrderStatus.cancelled: "Annulées",
}


def _can(*, session: Session, user: User, resource: str, action: str) -> bool:
    return permission_service.check_permission(
        session=session, user=user, resource=resource, action=action
    )


def _date_range(
    *, created_from: datetime | None, created_to: datetime | None
) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    start = created_from or datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
    end = created_to or datetime.combine(now.date(), time.max, tzinfo=timezone.utc)
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    return start, end


def _metric(
    key: str, label: str, value: int | Decimal, unit: str | None = None
) -> DashboardMetricPublic:
    return DashboardMetricPublic(key=key, label=label, value=value, unit=unit)


def _display_name(full_name: str | None, email: str | None) -> str:
    return full_name or email or "-"


def _orders_section(
    *, session: Session, created_from: datetime, created_to: datetime
) -> DashboardOrdersPublic:
    rows = dashboard_repo.order_status_counts(
        session=session, created_from=created_from, created_to=created_to
    )
    counts = {status: int(count) for status, count in rows}
    total = sum(counts.values())
    breakdown = [
        DashboardStatusPointPublic(
            key=status.value,
            label=ORDER_STATUS_LABELS[status],
            count=counts.get(status, 0),
        )
        for status in OrderStatus
    ]
    recent = [
        OrderListItemPublic(
            id=order.id,
            accession_number=order.accession_number,
            patient_id=patient.id,
            patient_identifier=patient.identifier,
            patient_name=f"{patient.first_name} {patient.last_name}",
            doctor_id=doctor.id if doctor else None,
            doctor_name=f"{doctor.first_name} {doctor.last_name}" if doctor else None,
            status=order.status,
            net_amount=invoice.net_amount,
            payment_status=invoice.payment_status,
            created_at=order.created_at,
        )
        for order, patient, doctor, invoice in dashboard_repo.recent_orders(
            session=session,
            created_from=created_from,
            created_to=created_to,
            limit=6,
        )
    ]
    return DashboardOrdersPublic(
        metrics=[
            _metric("total", "Demandes", total),
            _metric("completed", "Terminées", counts.get(OrderStatus.completed, 0)),
            _metric("cancelled", "Annulées", counts.get(OrderStatus.cancelled, 0)),
        ],
        status_breakdown=breakdown,
        recent=recent,
    )


def _specimens_section(
    *, session: Session, created_from: datetime, created_to: datetime
) -> DashboardSpecimensPublic:
    pending, collected, rejected = dashboard_repo.specimen_counts(
        session=session, created_from=created_from, created_to=created_to
    )
    oldest_row = dashboard_repo.oldest_waiting_specimen_order(
        session=session, created_from=created_from, created_to=created_to
    )
    oldest = None
    if oldest_row is not None:
        (
            order,
            patient,
            invoice,
            pending_count,
            collected_count,
            rejected_count,
            specimen_count,
            specimen_summary,
        ) = oldest_row
        oldest = SpecimenQueueItemPublic(
            order_id=order.id,
            accession_number=order.accession_number,
            patient_id=patient.id,
            patient_identifier=patient.identifier,
            patient_name=f"{patient.first_name} {patient.last_name}",
            order_status=order.status,
            payment_status=invoice.payment_status,
            created_at=order.created_at,
            pending_count=int(pending_count),
            collected_count=int(collected_count),
            rejected_count=int(rejected_count),
            specimen_count=int(specimen_count),
            specimen_summary=specimen_summary,
        )
    return DashboardSpecimensPublic(
        metrics=[
            _metric("waiting", "À prélever", int(pending)),
            _metric("collected", "Prélevés", int(collected)),
            _metric("rejected", "Rejetés", int(rejected)),
        ],
        oldest_waiting=oldest,
    )


def _results_section(
    *, session: Session, created_from: datetime, created_to: datetime
) -> DashboardResultsPublic:
    entry, verification, abnormal, critical = dashboard_repo.result_summary(
        session=session, created_from=created_from, created_to=created_to
    )
    return DashboardResultsPublic(
        metrics=[
            _metric("entry_queue", "À saisir", int(entry)),
            _metric("verification_queue", "À vérifier", int(verification)),
            _metric("abnormal", "Anormaux", int(abnormal)),
            _metric("critical", "Critiques", int(critical)),
        ]
    )


def _critical_section(*, session: Session) -> DashboardCriticalPublic:
    count, latest_rows = dashboard_repo.critical_summary(session=session, limit=5)
    latest = []
    for row in latest_rows:
        (
            notification,
            accession_number,
            first_name,
            last_name,
            _identifier,
            analyte_code,
            analyte_name,
            result_value,
            notified_by_name,
            notified_by_email,
            notified_to_name,
            notified_to_email,
            acknowledged_by_name,
            acknowledged_by_email,
        ) = row
        latest.append(
            CriticalNotificationDetailPublic(
                **notification.model_dump(),
                accession_number=accession_number,
                patient_name=f"{first_name} {last_name}",
                analyte_code=analyte_code,
                analyte_name=analyte_name,
                result_value=result_value,
                notified_by_name=_display_name(notified_by_name, notified_by_email),
                notified_to_name=_display_name(notified_to_name, notified_to_email),
                acknowledged_by_name=(
                    _display_name(acknowledged_by_name, acknowledged_by_email)
                    if acknowledged_by_name or acknowledged_by_email
                    else None
                ),
            )
        )
    return DashboardCriticalPublic(
        metrics=[_metric("unacknowledged", "Critiques à acquitter", int(count))],
        latest=latest,
    )


def _finance_section(
    *, session: Session, created_from: datetime, created_to: datetime
) -> DashboardFinancePublic:
    count, net_billed, collected, outstanding, unpaid, partial = (
        dashboard_repo.finance_summary(
            session=session, created_from=created_from, created_to=created_to
        )
    )
    return DashboardFinancePublic(
        metrics=[
            _metric("invoice_count", "Factures", int(count)),
            _metric("net_billed", "Net facturé", net_billed, "money"),
            _metric("collected", "Encaissé", collected, "money"),
            _metric("outstanding", "À encaisser", outstanding, "money"),
            _metric("unpaid", "Impayées", int(unpaid)),
            _metric("partial", "Partielles", int(partial)),
        ]
    )


def _trends(
    *, session: Session, created_from: datetime, created_to: datetime
) -> list[DashboardTrendPointPublic]:
    granularity = "hour" if (created_to - created_from).days <= 1 else "day"
    rows = dashboard_repo.trend_rows(
        session=session,
        created_from=created_from,
        created_to=created_to,
        granularity=granularity,
    )
    return [
        DashboardTrendPointPublic(
            label=(
                bucket.strftime("%H:%M")
                if granularity == "hour"
                else bucket.strftime("%d/%m")
            ),
            orders=int(orders),
            specimens=int(specimens),
            results=int(results),
            revenue=revenue,
        )
        for bucket, orders, specimens, results, revenue in rows
    ]


def _quick_actions(*, session: Session, user: User) -> list[DashboardActionPublic]:
    actions: list[DashboardActionPublic] = []
    if _can(session=session, user=user, resource="orders", action="create"):
        actions.append(
            DashboardActionPublic(
                key="new_order",
                label="Nouvelle demande",
                description="Enregistrer un patient, les examens et le paiement.",
                href="/orders/new",
                priority=10,
            )
        )
    if _can(session=session, user=user, resource="specimens", action="view"):
        actions.append(
            DashboardActionPublic(
                key="specimens",
                label="File de prélèvement",
                description="Voir les demandes en attente de prélèvement.",
                href="/specimens",
                priority=20,
            )
        )
    if _can(session=session, user=user, resource="results", action="view"):
        actions.append(
            DashboardActionPublic(
                key="results",
                label="Saisie résultats",
                description="Ouvrir les demandes prêtes pour la paillasse.",
                href="/results",
                priority=30,
            )
        )
    if _can(session=session, user=user, resource="results", action="verify"):
        actions.append(
            DashboardActionPublic(
                key="verification",
                label="Vérification",
                description="Contrôler les résultats saisis avant validation.",
                href="/results",
                priority=40,
            )
        )
    if _can(session=session, user=user, resource="invoices", action="view"):
        actions.append(
            DashboardActionPublic(
                key="invoices",
                label="Factures",
                description="Suivre les encaissements et les soldes.",
                href="/invoices",
                priority=50,
            )
        )
    return sorted(actions, key=lambda item: item.priority)


def get_dashboard(
    *,
    session: Session,
    user: User,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> DashboardPublic:
    start, end = _date_range(created_from=created_from, created_to=created_to)
    can_view_orders = _can(
        session=session, user=user, resource="orders", action="view"
    )
    can_view_specimens = _can(
        session=session, user=user, resource="specimens", action="view"
    )
    can_view_results = _can(
        session=session, user=user, resource="results", action="view"
    )
    can_view_critical = _can(
        session=session,
        user=user,
        resource="critical_notifications",
        action="view",
    )
    can_view_finance = _can(
        session=session, user=user, resource="invoices", action="view"
    )
    return DashboardPublic(
        generated_at=datetime.now(timezone.utc),
        created_from=start,
        created_to=end,
        orders=(
            _orders_section(session=session, created_from=start, created_to=end)
            if can_view_orders
            else None
        ),
        specimens=(
            _specimens_section(session=session, created_from=start, created_to=end)
            if can_view_specimens
            else None
        ),
        results=(
            _results_section(session=session, created_from=start, created_to=end)
            if can_view_results
            else None
        ),
        critical=_critical_section(session=session) if can_view_critical else None,
        finance=(
            _finance_section(session=session, created_from=start, created_to=end)
            if can_view_finance
            else None
        ),
        trends=(
            _trends(session=session, created_from=start, created_to=end)
            if can_view_orders
            else []
        ),
        quick_actions=_quick_actions(session=session, user=user),
    )
