"""Shared formula validation and preview service."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlmodel import Session

from app.core.exceptions import BusinessRuleError
from app.models.lis import (
    Analyte,
    AnalyteDataType,
    FormulaPreviewResponse,
    FormulaReferencePublic,
    FormulaResultType,
    Unit,
)
from app.repositories import analyte as analyte_repo
from app.services import formula_engine


def _references_public(
    *, session: Session, codes: list[str], allowed_analyte_ids: list | None = None
) -> list[FormulaReferencePublic]:
    analytes = analyte_repo.get_by_codes(session=session, codes=codes)
    by_code = {item.code.upper(): item for item in analytes}
    allowed = set(allowed_analyte_ids or [])
    references = []
    for code in codes:
        analyte = by_code.get(code)
        if analyte is None or analyte.is_deleted:
            raise BusinessRuleError(f"Analyte inconnu dans la formule: {code}")
        if allowed and analyte.id not in allowed:
            raise BusinessRuleError(f"L'analyte {code} n'est pas autorisé dans cette formule")
        if analyte.data_type != AnalyteDataType.numeric:
            raise BusinessRuleError(f"L'analyte {code} doit être numérique")
        unit = session.get(Unit, analyte.unit_id) if analyte.unit_id else None
        references.append(_reference_public(analyte, unit))
    return references


def _reference_public(analyte: Analyte, unit: Unit | None) -> FormulaReferencePublic:
    return FormulaReferencePublic(
        id=analyte.id,
        code=analyte.code,
        name=analyte.name,
        data_type=analyte.data_type,
        unit_name=unit.name if unit else None,
    )


def validate_formula(
    *,
    session: Session,
    formula: str,
    expected_result_type: FormulaResultType,
    allowed_analyte_ids: list | None = None,
) -> list[FormulaReferencePublic]:
    codes = formula_engine.validate_formula_syntax(
        formula=formula,
        expected_result_type=expected_result_type,
    )
    return _references_public(
        session=session,
        codes=codes,
        allowed_analyte_ids=allowed_analyte_ids,
    )


def preview_formula(
    *,
    session: Session,
    formula: str,
    expected_result_type: FormulaResultType,
    values: dict[str, Any],
    allowed_analyte_ids: list | None = None,
) -> FormulaPreviewResponse:
    references = validate_formula(
        session=session,
        formula=formula,
        expected_result_type=expected_result_type,
        allowed_analyte_ids=allowed_analyte_ids,
    )
    result, _codes = formula_engine.evaluate_formula(
        formula=formula,
        values=values,
        expected_result_type=expected_result_type,
    )
    result_type = FormulaResultType.boolean if isinstance(result, bool) else FormulaResultType.number
    return FormulaPreviewResponse(
        references=references,
        result=_result_to_string(result),
        result_type=result_type,
        is_valid=True,
        message="Formule valide",
    )


def _result_to_string(result: Any) -> str:
    if isinstance(result, bool):
        return "true" if result else "false"
    if isinstance(result, Decimal):
        return str(result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return str(result)
