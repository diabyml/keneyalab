import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, require_permission
from app.models import (
    AnalyteDataType,
    SortOrder,
    TargetGenderType,
    ValidationRuleCreate,
    ValidationRuleDetailPublic,
    ValidationRuleSimulationRequest,
    ValidationRuleSimulationResponse,
    ValidationRulesPublic,
    ValidationRuleUpdate,
)
from app.services import validation_rule as rule_service

router = APIRouter(prefix="/validation-rules", tags=["validation-rules"])


@router.get(
    "/",
    dependencies=[Depends(require_permission("rules", "manage"))],
    response_model=ValidationRulesPublic,
)
def read_validation_rules(
    session: SessionDep,
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
) -> Any:
    """Retrieve validation rules with server-side search, filters, and sorting."""
    items, count = rule_service.get_rules(
        session=session,
        skip=skip,
        limit=limit,
        search=search,
        analyte_id=analyte_id,
        data_type=data_type,
        is_active=is_active,
        target_gender=target_gender,
        required_context_id=required_context_id,
        age_years=age_years,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return ValidationRulesPublic(data=items, count=count)


@router.post(
    "/simulate",
    dependencies=[Depends(require_permission("rules", "manage"))],
    response_model=ValidationRuleSimulationResponse,
)
def simulate_validation_rule(
    *, session: SessionDep, simulation_in: ValidationRuleSimulationRequest
) -> Any:
    """Simulate rule matching and result classification."""
    return rule_service.simulate_rule(session=session, simulation_in=simulation_in)


@router.post(
    "/",
    dependencies=[Depends(require_permission("rules", "manage"))],
    response_model=ValidationRuleDetailPublic,
)
def create_validation_rule(
    *, session: SessionDep, rule_in: ValidationRuleCreate
) -> Any:
    """Create a validation rule."""
    return rule_service.create_rule(session=session, rule_in=rule_in)


@router.put(
    "/{id}",
    dependencies=[Depends(require_permission("rules", "manage"))],
    response_model=ValidationRuleDetailPublic,
)
def update_validation_rule(
    *, session: SessionDep, id: uuid.UUID, rule_in: ValidationRuleUpdate
) -> Any:
    """Update a validation rule."""
    return rule_service.update_rule(session=session, rule_id=id, rule_in=rule_in)


@router.get(
    "/{id}",
    dependencies=[Depends(require_permission("rules", "manage"))],
    response_model=ValidationRuleDetailPublic,
)
def read_validation_rule(session: SessionDep, id: uuid.UUID) -> Any:
    """Get a validation rule by ID."""
    return rule_service.get_rule(session=session, rule_id=id)
