from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, require_permission
from app.models import FormulaPreviewRequest, FormulaPreviewResponse
from app.services import formula as formula_service

router = APIRouter(prefix="/formulas", tags=["formulas"])


@router.post(
    "/preview",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=FormulaPreviewResponse,
)
def preview_formula(*, session: SessionDep, preview_in: FormulaPreviewRequest) -> Any:
    """Validate and preview a safe LIS formula."""
    return formula_service.preview_formula(
        session=session,
        formula=preview_in.formula,
        expected_result_type=preview_in.expected_result_type,
        values=preview_in.values,
        allowed_analyte_ids=preview_in.allowed_analyte_ids,
    )
