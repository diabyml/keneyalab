"""Result workflow repository - pure database access only."""

import uuid
from datetime import datetime

from sqlmodel import Session, col, func, or_, select

from app.models import User
from app.models.lis import (
    Analyte,
    AnalyteResult,
    AnalyteResultComment,
    AuditLog,
    Catalog,
    Category,
    ConsistencyRule,
    ConsistencyRuleAnalyte,
    CriticalNotification,
    Order,
    OrderCatalogItemAnalyte,
    OrderItem,
    OrderItemSpecimen,
    OrderSpecimen,
    Patient,
    PatientContext,
    ReflexRule,
    Report,
    ResultStatus,
    SortOrder,
    SpecimenStatus,
    SpecimenType,
    Unit,
)
from app.models.rbac import Permission, Role, RolePermission, UserRole


def get_order_for_update(*, session: Session, order_id: uuid.UUID) -> Order | None:
    return session.exec(
        select(Order).where(Order.id == order_id).with_for_update()
    ).first()


def get_result_for_update(
    *, session: Session, result_id: uuid.UUID
) -> AnalyteResult | None:
    return session.exec(
        select(AnalyteResult)
        .where(AnalyteResult.id == result_id)
        .with_for_update()
    ).first()


def get_order_results_for_update(
    *, session: Session, order_id: uuid.UUID
) -> list[AnalyteResult]:
    return list(
        session.exec(
            select(AnalyteResult)
            .join(OrderItem, AnalyteResult.order_item_id == OrderItem.id)
            .where(
                OrderItem.order_id == order_id,
                OrderItem.is_active == True,  # noqa: E712
                AnalyteResult.is_superseded == False,  # noqa: E712
            )
            .with_for_update()
        ).all()
    )


def get_active_result(
    *,
    session: Session,
    order_item_id: uuid.UUID,
    analyte_id: uuid.UUID,
    specimen_id: uuid.UUID,
) -> AnalyteResult | None:
    return session.exec(
        select(AnalyteResult).where(
            AnalyteResult.order_item_id == order_item_id,
            AnalyteResult.analyte_id == analyte_id,
            AnalyteResult.specimen_id == specimen_id,
            AnalyteResult.is_superseded == False,  # noqa: E712
        )
    ).first()


def create(*, session: Session, db_obj):
    session.add(db_obj)
    session.flush()
    return db_obj


def get_order_header(*, session: Session, order_id: uuid.UUID):
    from app.models.lis import Doctor

    return session.exec(
        select(Order, Patient, PatientContext, Doctor)
        .join(Patient, Order.patient_id == Patient.id)
        .join(PatientContext, Order.patient_context_id == PatientContext.id, isouter=True)
        .join(Doctor, Order.doctor_id == Doctor.id, isouter=True)
        .where(Order.id == order_id)
    ).first()


def get_workspace_rows(*, session: Session, order_id: uuid.UUID):
    resulted_by = User.__table__.alias("resulted_by")
    verified_by = User.__table__.alias("verified_by")
    return list(
        session.exec(
            select(
                OrderItem,
                Catalog,
                Category,
                OrderCatalogItemAnalyte,
                Analyte,
                Unit,
                OrderSpecimen,
                SpecimenType,
                AnalyteResult,
                resulted_by.c.full_name,
                resulted_by.c.email,
                verified_by.c.full_name,
                verified_by.c.email,
            )
            .join(Catalog, OrderItem.catalog_id == Catalog.id)
            .join(Category, Catalog.category_id == Category.id, isouter=True)
            .join(
                OrderCatalogItemAnalyte,
                OrderCatalogItemAnalyte.order_item_id == OrderItem.id,
            )
            .join(Analyte, OrderCatalogItemAnalyte.analyte_id == Analyte.id)
            .join(Unit, Analyte.unit_id == Unit.id, isouter=True)
            .join(OrderItemSpecimen, OrderItemSpecimen.order_item_id == OrderItem.id)
            .join(
                OrderSpecimen,
                OrderItemSpecimen.order_specimen_id == OrderSpecimen.id,
            )
            .join(SpecimenType, OrderSpecimen.specimen_type_id == SpecimenType.id)
            .join(
                AnalyteResult,
                (AnalyteResult.order_item_id == OrderItem.id)
                & (AnalyteResult.analyte_id == Analyte.id)
                & (AnalyteResult.specimen_id == OrderSpecimen.id)
                & (AnalyteResult.is_superseded == False),  # noqa: E712
                isouter=True,
            )
            .join(
                resulted_by,
                AnalyteResult.resulted_by_id == resulted_by.c.id,
                isouter=True,
            )
            .join(
                verified_by,
                AnalyteResult.verified_by_id == verified_by.c.id,
                isouter=True,
            )
            .where(
                OrderItem.order_id == order_id,
                OrderItem.is_active == True,  # noqa: E712
                OrderCatalogItemAnalyte.is_active == True,  # noqa: E712
                OrderSpecimen.is_superseded == False,  # noqa: E712
                OrderSpecimen.status.in_(
                    [SpecimenStatus.collected, SpecimenStatus.processed]
                ),
            )
            .order_by(
                col(OrderItem.sort_order).asc(),
                col(OrderCatalogItemAnalyte.sort_order).asc(),
                col(SpecimenType.name).asc(),
            )
        ).all()
    )
def get_comments(*, session: Session, result_ids: list[uuid.UUID]):
    if not result_ids:
        return []
    return list(
        session.exec(
            select(AnalyteResultComment, User)
            .join(User, AnalyteResultComment.user_id == User.id)
            .where(AnalyteResultComment.analyte_result_id.in_(result_ids))
            .order_by(col(AnalyteResultComment.created_at).asc())
        ).all()
    )


def get_result_audits(*, session: Session, result_ids: list[uuid.UUID]):
    if not result_ids:
        return []
    return list(
        session.exec(
            select(AuditLog, User)
            .join(User, AuditLog.performed_by_id == User.id, isouter=True)
            .where(
                AuditLog.table_name == "analyte_results",
                AuditLog.record_id.in_(result_ids),
            )
            .order_by(col(AuditLog.performed_at).asc())
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


def get_notifications(*, session: Session, result_ids: list[uuid.UUID]):
    if not result_ids:
        return []
    notified_by = User.__table__.alias("notified_by")
    notified_to = User.__table__.alias("notified_to")
    acknowledged_by = User.__table__.alias("acknowledged_by")
    return list(
        session.execute(
            select(
                CriticalNotification,
                notified_by.c.full_name,
                notified_by.c.email,
                notified_to.c.full_name,
                notified_to.c.email,
                acknowledged_by.c.full_name,
                acknowledged_by.c.email,
            )
            .join(notified_by, CriticalNotification.notified_by_id == notified_by.c.id)
            .join(notified_to, CriticalNotification.notified_to_id == notified_to.c.id)
            .join(
                acknowledged_by,
                CriticalNotification.acknowledged_by_id == acknowledged_by.c.id,
                isouter=True,
            )
            .where(CriticalNotification.analyte_result_id.in_(result_ids))
            .order_by(col(CriticalNotification.created_at).desc())
        ).all()
    )


def get_previous_verified_value(
    *,
    session: Session,
    patient_id: uuid.UUID,
    analyte_id: uuid.UUID,
    exclude_result_id: uuid.UUID | None = None,
) -> str | None:
    statement = (
        select(AnalyteResult.result_value)
        .join(OrderItem, AnalyteResult.order_item_id == OrderItem.id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(
            Order.patient_id == patient_id,
            AnalyteResult.analyte_id == analyte_id,
            AnalyteResult.status == ResultStatus.verified,
            AnalyteResult.is_superseded == False,  # noqa: E712
        )
        .order_by(col(AnalyteResult.verified_at).desc())
    )
    if exclude_result_id is not None:
        statement = statement.where(AnalyteResult.id != exclude_result_id)
    return session.exec(statement.limit(1)).first()


def get_consistency_rules(
    *, session: Session, analyte_ids: list[uuid.UUID]
) -> list[tuple[ConsistencyRule, uuid.UUID]]:
    if not analyte_ids:
        return []
    return list(
        session.exec(
            select(ConsistencyRule, ConsistencyRuleAnalyte.analyte_id)
            .join(
                ConsistencyRuleAnalyte,
                ConsistencyRuleAnalyte.rule_id == ConsistencyRule.id,
            )
            .where(
                ConsistencyRule.is_deleted == False,  # noqa: E712
                ConsistencyRuleAnalyte.analyte_id.in_(analyte_ids),
            )
        ).all()
    )


def get_reflex_rules(
    *, session: Session, analyte_ids: list[uuid.UUID]
) -> list[ReflexRule]:
    if not analyte_ids:
        return []
    return list(
        session.exec(
            select(ReflexRule).where(
                ReflexRule.trigger_analyte_id.in_(analyte_ids),
                ReflexRule.is_deleted == False,  # noqa: E712
            )
        ).all()
    )


def get_queue(
    *,
    session: Session,
    mode: str,
    skip: int,
    limit: int,
    search: str | None,
    category_id: uuid.UUID | None,
    flagged: bool | None,
    created_from: datetime | None,
    created_to: datetime | None,
    sort_order: SortOrder,
):
    conditions = [
        OrderItem.is_active == True,  # noqa: E712
        OrderSpecimen.is_superseded == False,  # noqa: E712
        OrderSpecimen.status.in_([SpecimenStatus.collected, SpecimenStatus.processed]),
    ]
    if mode == "verification":
        conditions.append(AnalyteResult.status == ResultStatus.resulted)
    else:
        conditions.append(
            Order.status.in_(
                [
                    "collected",
                    "in_progress",
                    "partial_results",
                ]
            )
        )
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
    if category_id is not None:
        conditions.append(Catalog.category_id == category_id)
    if flagged is True:
        conditions.append(
            or_(
                AnalyteResult.is_abnormal == True,  # noqa: E712
                AnalyteResult.is_critical == True,  # noqa: E712
                AnalyteResult.delta_flag == True,  # noqa: E712
            )
        )
    if created_from is not None:
        conditions.append(Order.created_at >= created_from)
    if created_to is not None:
        conditions.append(Order.created_at <= created_to)

    base = (
        select(Order.id, Order.created_at)
        .join(Patient, Order.patient_id == Patient.id)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Catalog, OrderItem.catalog_id == Catalog.id)
        .join(OrderItemSpecimen, OrderItemSpecimen.order_item_id == OrderItem.id)
        .join(OrderSpecimen, OrderItemSpecimen.order_specimen_id == OrderSpecimen.id)
        .join(
            AnalyteResult,
            AnalyteResult.order_item_id == OrderItem.id,
            isouter=True,
        )
        .where(*conditions)
        .distinct()
    )
    count = session.exec(
        select(func.count()).select_from(base.subquery())
    ).one()
    order_expr = (
        col(Order.created_at).desc()
        if sort_order == SortOrder.desc
        else col(Order.created_at).asc()
    )
    ids = [
        order_id
        for order_id, _created_at in session.exec(
            base.order_by(order_expr).offset(skip).limit(limit)
        ).all()
    ]
    return ids, count


def get_recipient_users(
    *, session: Session, search: str | None, skip: int, limit: int
) -> tuple[list[User], int]:
    now = datetime.now().astimezone()
    permission_ids = select(Permission.id).where(
        Permission.resource == "critical_notifications",
        Permission.action.in_(["view", "acknowledge"]),
    )
    user_ids = (
        select(UserRole.user_id)
        .join(Role, UserRole.role_id == Role.id)
        .join(RolePermission, RolePermission.role_id == Role.id)
        .where(
            Role.is_deleted == False,  # noqa: E712
            RolePermission.permission_id.in_(permission_ids),
            or_(UserRole.expires_at.is_(None), UserRole.expires_at > now),
        )
    )
    conditions = [
        User.is_active == True,  # noqa: E712
        or_(User.is_superuser == True, User.id.in_(user_ids)),  # noqa: E712
    ]
    if search:
        query = f"%{search.strip()}%"
        conditions.append(
            or_(col(User.full_name).ilike(query), col(User.email).ilike(query))
        )
    count = session.exec(
        select(func.count()).select_from(User).where(*conditions)
    ).one()
    rows = list(
        session.exec(
            select(User)
            .where(*conditions)
            .order_by(col(User.full_name).asc(), col(User.email).asc())
            .offset(skip)
            .limit(limit)
        ).all()
    )
    return rows, count


def is_critical_recipient(*, session: Session, user_id: uuid.UUID) -> bool:
    users, _ = get_recipient_users(
        session=session,
        search=None,
        skip=0,
        limit=100_000,
    )
    return any(user.id == user_id for user in users)
