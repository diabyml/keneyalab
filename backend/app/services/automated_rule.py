"""Automated validation rules business logic."""

import uuid
from decimal import Decimal

from sqlmodel import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.lis import (
    Analyte,
    Catalog,
    ConsistencyRule,
    ConsistencyRuleCreate,
    ConsistencyRuleDetailPublic,
    ConsistencyRulePreviewRequest,
    ConsistencyRuleUpdate,
    FormulaPreviewResponse,
    FormulaReferencePublic,
    FormulaResultType,
    ReflexRule,
    ReflexRuleCreate,
    ReflexRuleDetailPublic,
    ReflexRulePreviewRequest,
    ReflexRulePreviewResponse,
    ReflexRuleUpdate,
    RuleSeverity,
    SortOrder,
    TriggerOperator,
    Unit,
)
from app.repositories import automated_rule as rule_repo
from app.services import formula as formula_service
from app.services.formula_engine import parse_decimal


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _required_text(value: str | None, message: str) -> str:
    cleaned = _clean_text(value)
    if not cleaned:
        raise BusinessRuleError(message)
    return cleaned


def _ensure_analyte_active(*, session: Session, analyte_id: uuid.UUID) -> Analyte:
    analyte = session.get(Analyte, analyte_id)
    if analyte is None or analyte.is_deleted:
        raise BusinessRuleError("Analyte non disponible")
    return analyte


def _ensure_catalog_active(*, session: Session, catalog_id: uuid.UUID) -> Catalog:
    catalog = session.get(Catalog, catalog_id)
    if catalog is None or catalog.is_deleted:
        raise BusinessRuleError("Entrée catalogue non disponible")
    return catalog


def _normalize_analyte_ids(*, session: Session, analyte_ids: list[uuid.UUID] | None) -> list[uuid.UUID]:
    normalized = list(dict.fromkeys(analyte_ids or []))
    if not normalized:
        raise BusinessRuleError("Au moins un analyte est requis")
    for analyte_id in normalized:
        _ensure_analyte_active(session=session, analyte_id=analyte_id)
    return normalized


def _validate_consistency_payload(
    *, session: Session, data: dict, current_analyte_ids: list[uuid.UUID] | None = None
) -> tuple[dict, list[uuid.UUID] | None]:
    if "name" in data:
        data["name"] = _required_text(data["name"], "Le nom de la règle est requis")
    if "formula" in data:
        data["formula"] = _required_text(data["formula"], "La formule est requise")
    if "formula_description" in data:
        data["formula_description"] = _clean_text(data["formula_description"])
    if "error_message" in data:
        data["error_message"] = _required_text(data["error_message"], "Le message d'erreur est requis")

    analyte_ids = None
    if "analyte_ids" in data:
        analyte_ids = _normalize_analyte_ids(session=session, analyte_ids=data.pop("analyte_ids"))
    elif current_analyte_ids is not None:
        analyte_ids = current_analyte_ids

    if "formula" in data or analyte_ids is not None:
        formula_service.validate_formula(
            session=session,
            formula=data.get("formula") or "",
            expected_result_type=FormulaResultType.boolean,
            allowed_analyte_ids=analyte_ids,
        )
    return data, analyte_ids


def _consistency_public(*, session: Session, rule: ConsistencyRule) -> ConsistencyRuleDetailPublic:
    analytes = [
        FormulaReferencePublic(
            id=analyte.id,
            code=analyte.code,
            name=analyte.name,
            data_type=analyte.data_type,
            unit_name=unit.name if unit else None,
        )
        for _attachment, analyte, unit in rule_repo.get_consistency_analytes(
            session=session, rule_id=rule.id
        )
    ]
    return ConsistencyRuleDetailPublic(**rule.model_dump(), analytes=analytes)


def get_consistency_rules(
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
) -> tuple[list[ConsistencyRuleDetailPublic], int]:
    rules, count = rule_repo.get_consistency_all(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        is_deleted=is_deleted,
        search=_clean_text(search),
        severity=severity,
        analyte_id=analyte_id,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return [_consistency_public(session=session, rule=rule) for rule in rules], count


def get_consistency_rule(*, session: Session, rule_id: uuid.UUID) -> ConsistencyRuleDetailPublic:
    rule = rule_repo.get_consistency_by_id(session=session, rule_id=rule_id)
    if rule is None:
        raise NotFoundError("Règle de cohérence non trouvée")
    return _consistency_public(session=session, rule=rule)


def create_consistency_rule(
    *, session: Session, rule_in: ConsistencyRuleCreate
) -> ConsistencyRuleDetailPublic:
    data, analyte_ids = _validate_consistency_payload(session=session, data=rule_in.model_dump())
    db_rule = ConsistencyRule.model_validate(data)
    rule_repo.create_consistency(session=session, db_obj=db_rule)
    rule_repo.replace_consistency_analytes(
        session=session,
        rule_id=db_rule.id,
        analyte_ids=analyte_ids or [],
    )
    session.commit()
    return get_consistency_rule(session=session, rule_id=db_rule.id)


def update_consistency_rule(
    *, session: Session, rule_id: uuid.UUID, rule_in: ConsistencyRuleUpdate
) -> ConsistencyRuleDetailPublic:
    db_rule = rule_repo.get_consistency_by_id(session=session, rule_id=rule_id)
    if db_rule is None:
        raise NotFoundError("Règle de cohérence non trouvée")
    current_analyte_ids = [
        analyte.id
        for _attachment, analyte, _unit in rule_repo.get_consistency_analytes(
            session=session, rule_id=rule_id
        )
    ]
    data = rule_in.model_dump(exclude_unset=True)
    formula_for_validation = data.get("formula", db_rule.formula)
    data_with_formula = {**data, "formula": formula_for_validation}
    update_data, analyte_ids = _validate_consistency_payload(
        session=session,
        data=data_with_formula,
        current_analyte_ids=current_analyte_ids,
    )
    if "formula" not in data:
        update_data.pop("formula", None)
    rule_repo.update_consistency(session=session, db_rule=db_rule, update_data=update_data)
    if "analyte_ids" in data:
        rule_repo.replace_consistency_analytes(
            session=session,
            rule_id=db_rule.id,
            analyte_ids=analyte_ids or [],
        )
    session.commit()
    return get_consistency_rule(session=session, rule_id=db_rule.id)


def delete_consistency_rule(*, session: Session, rule_id: uuid.UUID) -> None:
    db_rule = rule_repo.get_consistency_by_id(session=session, rule_id=rule_id)
    if db_rule is None:
        raise NotFoundError("Règle de cohérence non trouvée")
    rule_repo.update_consistency(session=session, db_rule=db_rule, update_data={"is_deleted": True})
    session.commit()


def restore_consistency_rule(*, session: Session, rule_id: uuid.UUID) -> ConsistencyRuleDetailPublic:
    db_rule = rule_repo.get_consistency_by_id(session=session, rule_id=rule_id)
    if db_rule is None:
        raise NotFoundError("Règle de cohérence non trouvée")
    rule_repo.update_consistency(session=session, db_rule=db_rule, update_data={"is_deleted": False})
    session.commit()
    return get_consistency_rule(session=session, rule_id=rule_id)


def preview_consistency_rule(
    *, session: Session, preview_in: ConsistencyRulePreviewRequest
) -> FormulaPreviewResponse:
    analyte_ids = _normalize_analyte_ids(session=session, analyte_ids=preview_in.analyte_ids)
    return formula_service.preview_formula(
        session=session,
        formula=preview_in.formula,
        expected_result_type=FormulaResultType.boolean,
        values=preview_in.values,
        allowed_analyte_ids=analyte_ids,
    )


def _reflex_public(row: tuple[ReflexRule, Analyte, Unit | None, Catalog]) -> ReflexRuleDetailPublic:
    rule, analyte, unit, catalog = row
    return ReflexRuleDetailPublic(
        **rule.model_dump(),
        trigger_analyte_code=analyte.code,
        trigger_analyte_name=analyte.name,
        trigger_analyte_data_type=analyte.data_type,
        trigger_unit_name=unit.name if unit else None,
        action_catalog_code=catalog.code,
        action_catalog_name=catalog.name,
        action_catalog_type=catalog.type,
    )


def _validate_reflex_payload(*, session: Session, data: dict, current: ReflexRule | None = None) -> dict:
    trigger_analyte_id = data.get("trigger_analyte_id") or (current.trigger_analyte_id if current else None)
    action_catalog_id = data.get("action_catalog_id") or (current.action_catalog_id if current else None)
    if trigger_analyte_id is None:
        raise BusinessRuleError("Analyte déclencheur requis")
    if action_catalog_id is None:
        raise BusinessRuleError("Action catalogue requise")
    _ensure_analyte_active(session=session, analyte_id=trigger_analyte_id)
    _ensure_catalog_active(session=session, catalog_id=action_catalog_id)
    data["trigger_analyte_id"] = trigger_analyte_id
    data["action_catalog_id"] = action_catalog_id
    if "trigger_value" in data:
        data["trigger_value"] = _required_text(data["trigger_value"], "La valeur de déclenchement est requise")
    operator_value = data.get("trigger_operator") or (current.trigger_operator if current else None)
    trigger_value = data.get("trigger_value") or (current.trigger_value if current else None)
    if operator_value in {TriggerOperator.gt, TriggerOperator.gte, TriggerOperator.lt, TriggerOperator.lte}:
        parse_decimal(trigger_value, label="déclenchement")
    return data


def get_reflex_rules(
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
) -> tuple[list[ReflexRuleDetailPublic], int]:
    rows, count = rule_repo.get_reflex_all(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        is_deleted=is_deleted,
        search=_clean_text(search),
        trigger_analyte_id=trigger_analyte_id,
        trigger_operator=trigger_operator,
        action_catalog_id=action_catalog_id,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return [_reflex_public(row) for row in rows], count


def get_reflex_rule(*, session: Session, rule_id: uuid.UUID) -> ReflexRuleDetailPublic:
    row = rule_repo.get_reflex_detail(session=session, rule_id=rule_id)
    if row is None:
        raise NotFoundError("Règle réflexe non trouvée")
    return _reflex_public(row)


def create_reflex_rule(*, session: Session, rule_in: ReflexRuleCreate) -> ReflexRuleDetailPublic:
    data = _validate_reflex_payload(session=session, data=rule_in.model_dump())
    db_rule = ReflexRule.model_validate(data)
    rule_repo.create_reflex(session=session, db_obj=db_rule)
    session.commit()
    return get_reflex_rule(session=session, rule_id=db_rule.id)


def update_reflex_rule(
    *, session: Session, rule_id: uuid.UUID, rule_in: ReflexRuleUpdate
) -> ReflexRuleDetailPublic:
    db_rule = rule_repo.get_reflex_by_id(session=session, rule_id=rule_id)
    if db_rule is None:
        raise NotFoundError("Règle réflexe non trouvée")
    data = _validate_reflex_payload(
        session=session,
        data=rule_in.model_dump(exclude_unset=True),
        current=db_rule,
    )
    rule_repo.update_reflex(session=session, db_rule=db_rule, update_data=data)
    session.commit()
    return get_reflex_rule(session=session, rule_id=db_rule.id)


def delete_reflex_rule(*, session: Session, rule_id: uuid.UUID) -> None:
    db_rule = rule_repo.get_reflex_by_id(session=session, rule_id=rule_id)
    if db_rule is None:
        raise NotFoundError("Règle réflexe non trouvée")
    rule_repo.update_reflex(session=session, db_rule=db_rule, update_data={"is_deleted": True})
    session.commit()


def restore_reflex_rule(*, session: Session, rule_id: uuid.UUID) -> ReflexRuleDetailPublic:
    db_rule = rule_repo.get_reflex_by_id(session=session, rule_id=rule_id)
    if db_rule is None:
        raise NotFoundError("Règle réflexe non trouvée")
    rule_repo.update_reflex(session=session, db_rule=db_rule, update_data={"is_deleted": False})
    session.commit()
    return get_reflex_rule(session=session, rule_id=rule_id)


def preview_reflex_rule(preview_in: ReflexRulePreviewRequest) -> ReflexRulePreviewResponse:
    triggered = _evaluate_reflex(
        operator_value=preview_in.trigger_operator,
        trigger_value=preview_in.trigger_value,
        sample_value=preview_in.sample_value,
    )
    return ReflexRulePreviewResponse(
        is_triggered=triggered,
        message="Règle déclenchée" if triggered else "Règle non déclenchée",
    )


def _evaluate_reflex(*, operator_value: TriggerOperator, trigger_value: str, sample_value: str) -> bool:
    if operator_value in {TriggerOperator.gt, TriggerOperator.gte, TriggerOperator.lt, TriggerOperator.lte}:
        sample = parse_decimal(sample_value, label="résultat")
        trigger = parse_decimal(trigger_value, label="déclenchement")
        if operator_value == TriggerOperator.gt:
            return sample > trigger
        if operator_value == TriggerOperator.gte:
            return sample >= trigger
        if operator_value == TriggerOperator.lt:
            return sample < trigger
        return sample <= trigger
    if operator_value == TriggerOperator.eq:
        return sample_value.strip().lower() == trigger_value.strip().lower()
    values = [item.strip().lower() for item in trigger_value.split(",") if item.strip()]
    return sample_value.strip().lower() in values
