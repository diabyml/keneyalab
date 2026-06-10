import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, require_permission
from app.models import (
    ConsistencyRuleCreate,
    ConsistencyRuleDetailPublic,
    ConsistencyRulePreviewRequest,
    ConsistencyRulesPublic,
    ConsistencyRuleUpdate,
    FormulaPreviewResponse,
    Message,
    ReflexRuleCreate,
    ReflexRuleDetailPublic,
    ReflexRulePreviewRequest,
    ReflexRulePreviewResponse,
    ReflexRulesPublic,
    ReflexRuleUpdate,
    RuleSeverity,
    SortOrder,
    TriggerOperator,
)
from app.services import automated_rule as automated_rule_service

router = APIRouter(prefix="/automated-rules", tags=["automated-rules"])


@router.get(
    "/consistency",
    dependencies=[Depends(require_permission("rules", "manage"))],
    response_model=ConsistencyRulesPublic,
)
def read_consistency_rules(
    session: SessionDep,
    skip: int = 0,
    limit: int = 25,
    include_deleted: bool = False,
    is_deleted: bool | None = None,
    search: str | None = None,
    severity: RuleSeverity | None = None,
    analyte_id: uuid.UUID | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.asc,
) -> Any:
    rules, count = automated_rule_service.get_consistency_rules(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        is_deleted=is_deleted,
        search=search,
        severity=severity,
        analyte_id=analyte_id,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return ConsistencyRulesPublic(data=rules, count=count)


@router.post(
    "/consistency/preview",
    dependencies=[Depends(require_permission("rules", "manage"))],
    response_model=FormulaPreviewResponse,
)
def preview_consistency_rule(
    *, session: SessionDep, preview_in: ConsistencyRulePreviewRequest
) -> Any:
    return automated_rule_service.preview_consistency_rule(
        session=session, preview_in=preview_in
    )


@router.get(
    "/consistency/{id}",
    dependencies=[Depends(require_permission("rules", "manage"))],
    response_model=ConsistencyRuleDetailPublic,
)
def read_consistency_rule(session: SessionDep, id: uuid.UUID) -> Any:
    return automated_rule_service.get_consistency_rule(session=session, rule_id=id)


@router.post(
    "/consistency",
    dependencies=[Depends(require_permission("rules", "manage"))],
    response_model=ConsistencyRuleDetailPublic,
)
def create_consistency_rule(
    *, session: SessionDep, rule_in: ConsistencyRuleCreate
) -> Any:
    return automated_rule_service.create_consistency_rule(
        session=session, rule_in=rule_in
    )


@router.put(
    "/consistency/{id}",
    dependencies=[Depends(require_permission("rules", "manage"))],
    response_model=ConsistencyRuleDetailPublic,
)
def update_consistency_rule(
    *, session: SessionDep, id: uuid.UUID, rule_in: ConsistencyRuleUpdate
) -> Any:
    return automated_rule_service.update_consistency_rule(
        session=session, rule_id=id, rule_in=rule_in
    )


@router.delete(
    "/consistency/{id}",
    dependencies=[Depends(require_permission("rules", "manage"))],
)
def delete_consistency_rule(session: SessionDep, id: uuid.UUID) -> Message:
    automated_rule_service.delete_consistency_rule(session=session, rule_id=id)
    return Message(message="Règle de cohérence supprimée avec succès")


@router.post(
    "/consistency/{id}/restore",
    dependencies=[Depends(require_permission("rules", "manage"))],
    response_model=ConsistencyRuleDetailPublic,
)
def restore_consistency_rule(session: SessionDep, id: uuid.UUID) -> Any:
    return automated_rule_service.restore_consistency_rule(session=session, rule_id=id)


@router.get(
    "/reflex",
    dependencies=[Depends(require_permission("rules", "manage"))],
    response_model=ReflexRulesPublic,
)
def read_reflex_rules(
    session: SessionDep,
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
) -> Any:
    rules, count = automated_rule_service.get_reflex_rules(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        is_deleted=is_deleted,
        search=search,
        trigger_analyte_id=trigger_analyte_id,
        trigger_operator=trigger_operator,
        action_catalog_id=action_catalog_id,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return ReflexRulesPublic(data=rules, count=count)


@router.post(
    "/reflex/preview",
    dependencies=[Depends(require_permission("rules", "manage"))],
    response_model=ReflexRulePreviewResponse,
)
def preview_reflex_rule(preview_in: ReflexRulePreviewRequest) -> Any:
    return automated_rule_service.preview_reflex_rule(preview_in)


@router.get(
    "/reflex/{id}",
    dependencies=[Depends(require_permission("rules", "manage"))],
    response_model=ReflexRuleDetailPublic,
)
def read_reflex_rule(session: SessionDep, id: uuid.UUID) -> Any:
    return automated_rule_service.get_reflex_rule(session=session, rule_id=id)


@router.post(
    "/reflex",
    dependencies=[Depends(require_permission("rules", "manage"))],
    response_model=ReflexRuleDetailPublic,
)
def create_reflex_rule(*, session: SessionDep, rule_in: ReflexRuleCreate) -> Any:
    return automated_rule_service.create_reflex_rule(session=session, rule_in=rule_in)


@router.put(
    "/reflex/{id}",
    dependencies=[Depends(require_permission("rules", "manage"))],
    response_model=ReflexRuleDetailPublic,
)
def update_reflex_rule(
    *, session: SessionDep, id: uuid.UUID, rule_in: ReflexRuleUpdate
) -> Any:
    return automated_rule_service.update_reflex_rule(
        session=session, rule_id=id, rule_in=rule_in
    )


@router.delete(
    "/reflex/{id}",
    dependencies=[Depends(require_permission("rules", "manage"))],
)
def delete_reflex_rule(session: SessionDep, id: uuid.UUID) -> Message:
    automated_rule_service.delete_reflex_rule(session=session, rule_id=id)
    return Message(message="Règle réflexe supprimée avec succès")


@router.post(
    "/reflex/{id}/restore",
    dependencies=[Depends(require_permission("rules", "manage"))],
    response_model=ReflexRuleDetailPublic,
)
def restore_reflex_rule(session: SessionDep, id: uuid.UUID) -> Any:
    return automated_rule_service.restore_reflex_rule(session=session, rule_id=id)
