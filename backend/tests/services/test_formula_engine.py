import pytest

from app.core.exceptions import BusinessRuleError
from app.models.lis import FormulaResultType
from app.services.formula import _result_to_string
from app.services.formula_engine import evaluate_formula, validate_formula_syntax


def test_formula_engine_evaluates_numeric_formula_with_safe_functions() -> None:
    result, references = evaluate_formula(
        formula="round(abs({A} - {B}) / 2, 2)",
        values={"A": "10", "B": "3"},
        expected_result_type=FormulaResultType.number,
    )

    assert str(result) == "3.50"
    assert references == ["A", "B"]


def test_formula_engine_evaluates_boolean_consistency_formula() -> None:
    result, references = evaluate_formula(
        formula="{GLU} > 5 and max({A}, {B}) < 20",
        values={"GLU": "6", "A": "12", "B": "10"},
        expected_result_type=FormulaResultType.boolean,
    )

    assert result is True
    assert references == ["GLU", "A", "B"]


def test_formula_engine_rejects_unsafe_calls() -> None:
    with pytest.raises(BusinessRuleError):
        validate_formula_syntax(
            formula="__import__('os').system('id')",
            expected_result_type=FormulaResultType.number,
        )


def test_formula_engine_rejects_wrong_result_type() -> None:
    with pytest.raises(BusinessRuleError):
        evaluate_formula(
            formula="{A} + {B}",
            values={"A": "1", "B": "2"},
            expected_result_type=FormulaResultType.boolean,
        )


def test_formula_result_string_uses_two_decimal_digits() -> None:
    result, _references = evaluate_formula(
        formula="{A} / {B}",
        values={"A": "10", "B": "3"},
        expected_result_type=FormulaResultType.number,
    )

    assert _result_to_string(result) == "3.33"
