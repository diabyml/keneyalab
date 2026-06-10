"""Automated validation rule repository - pure database access only."""

import uuid

from sqlmodel import Session, col, func, or_, select

from app.models.lis import (
    Analyte,
    Catalog,
    ConsistencyRule,
    ConsistencyRuleAnalyte,
    ReflexRule,
    RuleSeverity,
    SortOrder,
    TriggerOperator,
    Unit,
)

CONSISTENCY_SORT_COLUMNS = {
    "name": ConsistencyRule.name,
    "severity": ConsistencyRule.severity,
    "created_at": ConsistencyRule.created_at,
    "updated_at": ConsistencyRule.updated_at,
}
REFLEX_SORT_COLUMNS = {
    "trigger_analyte": Analyte.code,
    "trigger_operator": ReflexRule.trigger_operator,
    "action_catalog": Catalog.code,
    "created_at": ReflexRule.created_at,
    "updated_at": ReflexRule.updated_at,
}


def get_consistency_by_id(*, session: Session, rule_id: uuid.UUID) -> ConsistencyRule | None:
    return session.get(ConsistencyRule, rule_id)


def get_consistency_all(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 25,
    include_deleted: bool = False,
    is_deleted: bool | None = None,
    search: str | None = None,
    severity: RuleSeverity | None = None,
    analyte_id: uuid.UUID | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.asc,
) -> tuple[list[ConsistencyRule], int]:
    conditions = []
    joins_analyte = analyte_id is not None
    if is_deleted is not None:
        conditions.append(ConsistencyRule.is_deleted == is_deleted)
    elif not include_deleted:
        conditions.append(col(ConsistencyRule.is_deleted).is_(False))
    if search:
        q = f"%{search.strip()}%"
        conditions.append(
            or_(
                col(ConsistencyRule.name).ilike(q),
                col(ConsistencyRule.formula).ilike(q),
                col(ConsistencyRule.error_message).ilike(q),
            )
        )
    if severity is not None:
        conditions.append(ConsistencyRule.severity == severity)
    if analyte_id is not None:
        conditions.append(ConsistencyRuleAnalyte.analyte_id == analyte_id)

    base_query = select(ConsistencyRule)
    count_statement = select(func.count(func.distinct(ConsistencyRule.id))).select_from(ConsistencyRule)
    if joins_analyte:
        base_query = base_query.join(ConsistencyRuleAnalyte)
        count_statement = count_statement.join(ConsistencyRuleAnalyte)
    if conditions:
        base_query = base_query.where(*conditions)
        count_statement = count_statement.where(*conditions)

    count = session.exec(count_statement).one()
    sort_column = CONSISTENCY_SORT_COLUMNS.get(sort_by or "name", ConsistencyRule.name)
    order_expr = col(sort_column).desc() if sort_order == SortOrder.desc else col(sort_column).asc()
    statement = (
        base_query.distinct()
        .order_by(order_expr, col(ConsistencyRule.name).asc())
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all()), count


def get_consistency_analytes(
    *, session: Session, rule_id: uuid.UUID
) -> list[tuple[ConsistencyRuleAnalyte, Analyte, Unit | None]]:
    statement = (
        select(ConsistencyRuleAnalyte, Analyte, Unit)
        .join(Analyte, ConsistencyRuleAnalyte.analyte_id == Analyte.id)
        .join(Unit, Analyte.unit_id == Unit.id, isouter=True)
        .where(ConsistencyRuleAnalyte.rule_id == rule_id)
        .order_by(col(Analyte.code).asc())
    )
    return list(session.exec(statement).all())


def replace_consistency_analytes(
    *, session: Session, rule_id: uuid.UUID, analyte_ids: list[uuid.UUID]
) -> None:
    current = session.exec(
        select(ConsistencyRuleAnalyte).where(ConsistencyRuleAnalyte.rule_id == rule_id)
    ).all()
    for item in current:
        session.delete(item)
    session.flush()
    for analyte_id in analyte_ids:
        session.add(ConsistencyRuleAnalyte(rule_id=rule_id, analyte_id=analyte_id))
    session.flush()


def create_consistency(*, session: Session, db_obj: ConsistencyRule) -> ConsistencyRule:
    session.add(db_obj)
    session.flush()
    return db_obj


def update_consistency(
    *, session: Session, db_rule: ConsistencyRule, update_data: dict
) -> ConsistencyRule:
    db_rule.sqlmodel_update(update_data)
    session.add(db_rule)
    return db_rule


def get_reflex_by_id(*, session: Session, rule_id: uuid.UUID) -> ReflexRule | None:
    return session.get(ReflexRule, rule_id)


def get_reflex_all(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 25,
    include_deleted: bool = False,
    is_deleted: bool | None = None,
    search: str | None = None,
    trigger_analyte_id: uuid.UUID | None = None,
    trigger_operator: TriggerOperator | None = None,
    action_catalog_id: uuid.UUID | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.asc,
) -> tuple[list[tuple[ReflexRule, Analyte, Unit | None, Catalog]], int]:
    conditions = []
    if is_deleted is not None:
        conditions.append(ReflexRule.is_deleted == is_deleted)
    elif not include_deleted:
        conditions.append(col(ReflexRule.is_deleted).is_(False))
    if search:
        q = f"%{search.strip()}%"
        conditions.append(
            or_(
                col(Analyte.code).ilike(q),
                col(Analyte.name).ilike(q),
                col(Catalog.code).ilike(q),
                col(Catalog.name).ilike(q),
                col(ReflexRule.trigger_value).ilike(q),
            )
        )
    if trigger_analyte_id is not None:
        conditions.append(ReflexRule.trigger_analyte_id == trigger_analyte_id)
    if trigger_operator is not None:
        conditions.append(ReflexRule.trigger_operator == trigger_operator)
    if action_catalog_id is not None:
        conditions.append(ReflexRule.action_catalog_id == action_catalog_id)

    base_query = (
        select(ReflexRule, Analyte, Unit, Catalog)
        .join(Analyte, ReflexRule.trigger_analyte_id == Analyte.id)
        .join(Unit, Analyte.unit_id == Unit.id, isouter=True)
        .join(Catalog, ReflexRule.action_catalog_id == Catalog.id)
    )
    count_statement = (
        select(func.count())
        .select_from(ReflexRule)
        .join(Analyte, ReflexRule.trigger_analyte_id == Analyte.id)
        .join(Catalog, ReflexRule.action_catalog_id == Catalog.id)
    )
    if conditions:
        base_query = base_query.where(*conditions)
        count_statement = count_statement.where(*conditions)

    count = session.exec(count_statement).one()
    sort_column = REFLEX_SORT_COLUMNS.get(sort_by or "trigger_analyte", Analyte.code)
    order_expr = col(sort_column).desc() if sort_order == SortOrder.desc else col(sort_column).asc()
    statement = base_query.order_by(order_expr, col(Catalog.code).asc()).offset(skip).limit(limit)
    return list(session.exec(statement).all()), count


def get_reflex_detail(
    *, session: Session, rule_id: uuid.UUID
) -> tuple[ReflexRule, Analyte, Unit | None, Catalog] | None:
    statement = (
        select(ReflexRule, Analyte, Unit, Catalog)
        .join(Analyte, ReflexRule.trigger_analyte_id == Analyte.id)
        .join(Unit, Analyte.unit_id == Unit.id, isouter=True)
        .join(Catalog, ReflexRule.action_catalog_id == Catalog.id)
        .where(ReflexRule.id == rule_id)
    )
    return session.exec(statement).first()


def create_reflex(*, session: Session, db_obj: ReflexRule) -> ReflexRule:
    session.add(db_obj)
    session.flush()
    return db_obj


def update_reflex(*, session: Session, db_rule: ReflexRule, update_data: dict) -> ReflexRule:
    db_rule.sqlmodel_update(update_data)
    session.add(db_rule)
    return db_rule
