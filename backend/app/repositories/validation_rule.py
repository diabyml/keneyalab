"""Validation rule repository - pure database access only."""

import uuid

from sqlmodel import Session, col, func, or_, select

from app.models.lis import (
    Analyte,
    AnalyteDataType,
    PatientContext,
    SortOrder,
    TargetGenderType,
    Unit,
    ValidationRule,
)

SORT_COLUMNS = {
    "analyte_code": Analyte.code,
    "analyte_name": Analyte.name,
    "target_gender": ValidationRule.target_gender,
    "priority": ValidationRule.priority,
    "is_active": ValidationRule.is_active,
    "created_at": ValidationRule.created_at,
    "updated_at": ValidationRule.updated_at,
}


def get_by_id(*, session: Session, rule_id: uuid.UUID) -> ValidationRule | None:
    return session.get(ValidationRule, rule_id)


def get_all(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 25,
    search: str | None = None,
    analyte_id: uuid.UUID | None = None,
    data_type: AnalyteDataType | None = None,
    is_active: bool | None = None,
    target_gender: TargetGenderType | None = None,
    required_context_id: uuid.UUID | None = None,
    age_years: int | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.asc,
) -> tuple[list[tuple[ValidationRule, Analyte, Unit | None, PatientContext | None]], int]:
    conditions = []
    if search:
        query = f"%{search.strip()}%"
        conditions.append(or_(col(Analyte.code).ilike(query), col(Analyte.name).ilike(query)))
    if analyte_id is not None:
        conditions.append(ValidationRule.analyte_id == analyte_id)
    if data_type is not None:
        conditions.append(Analyte.data_type == data_type)
    if is_active is not None:
        conditions.append(ValidationRule.is_active == is_active)
    if target_gender is not None:
        conditions.append(ValidationRule.target_gender == target_gender)
    if required_context_id is not None:
        conditions.append(ValidationRule.required_context_id == required_context_id)
    if age_years is not None:
        conditions.append(
            or_(
                ValidationRule.min_age_years.is_(None),
                ValidationRule.min_age_years <= age_years,
            )
        )
        conditions.append(
            or_(
                ValidationRule.max_age_years.is_(None),
                ValidationRule.max_age_years >= age_years,
            )
        )

    base_query = (
        select(ValidationRule, Analyte, Unit, PatientContext)
        .join(Analyte, ValidationRule.analyte_id == Analyte.id)
        .join(Unit, Analyte.unit_id == Unit.id, isouter=True)
        .join(PatientContext, ValidationRule.required_context_id == PatientContext.id, isouter=True)
    )
    count_statement = (
        select(func.count())
        .select_from(ValidationRule)
        .join(Analyte, ValidationRule.analyte_id == Analyte.id)
        .join(PatientContext, ValidationRule.required_context_id == PatientContext.id, isouter=True)
    )
    if conditions:
        base_query = base_query.where(*conditions)
        count_statement = count_statement.where(*conditions)

    count = session.exec(count_statement).one()
    sort_column = SORT_COLUMNS.get(sort_by or "priority", ValidationRule.priority)
    order_expr = col(sort_column).desc() if sort_order == SortOrder.desc else col(sort_column).asc()
    statement = (
        base_query.order_by(order_expr, col(Analyte.code).asc(), col(ValidationRule.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all()), count


def get_detail(
    *,
    session: Session,
    rule_id: uuid.UUID,
) -> tuple[ValidationRule, Analyte, Unit | None, PatientContext | None] | None:
    statement = (
        select(ValidationRule, Analyte, Unit, PatientContext)
        .join(Analyte, ValidationRule.analyte_id == Analyte.id)
        .join(Unit, Analyte.unit_id == Unit.id, isouter=True)
        .join(PatientContext, ValidationRule.required_context_id == PatientContext.id, isouter=True)
        .where(ValidationRule.id == rule_id)
    )
    return session.exec(statement).first()


def get_match_candidates(
    *,
    session: Session,
    analyte_id: uuid.UUID,
) -> list[tuple[ValidationRule, Analyte, Unit | None, PatientContext | None]]:
    statement = (
        select(ValidationRule, Analyte, Unit, PatientContext)
        .join(Analyte, ValidationRule.analyte_id == Analyte.id)
        .join(Unit, Analyte.unit_id == Unit.id, isouter=True)
        .join(PatientContext, ValidationRule.required_context_id == PatientContext.id, isouter=True)
        .where(
            ValidationRule.analyte_id == analyte_id,
            ValidationRule.is_active.is_(True),
        )
        .order_by(
            col(ValidationRule.priority).desc(),
            col(ValidationRule.created_at).desc(),
        )
    )
    return list(session.exec(statement).all())


def create(*, session: Session, db_obj: ValidationRule) -> ValidationRule:
    session.add(db_obj)
    session.flush()
    return db_obj


def update(*, session: Session, db_rule: ValidationRule, update_data: dict) -> ValidationRule:
    db_rule.sqlmodel_update(update_data)
    session.add(db_rule)
    return db_rule
