"""Safe expression parsing and evaluation for LIS formulas."""

import ast
import operator
import re
from dataclasses import dataclass
from decimal import Decimal, DivisionByZero, InvalidOperation
from typing import Any

from app.core.exceptions import BusinessRuleError
from app.models.lis import FormulaResultType

REFERENCE_RE = re.compile(r"\{([A-Za-z0-9_.-]+)\}")
SAFE_FUNCTIONS = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
}
BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Not: operator.not_,
}
COMPARE_OPS = {
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
}


@dataclass(frozen=True)
class PreparedFormula:
    expression: str
    references: list[str]
    variable_map: dict[str, str]


def extract_references(formula: str) -> list[str]:
    references = []
    seen = set()
    for code in REFERENCE_RE.findall(formula):
        normalized = code.strip().upper()
        if normalized and normalized not in seen:
            seen.add(normalized)
            references.append(normalized)
    return references


def prepare_formula(formula: str) -> PreparedFormula:
    cleaned = formula.strip()
    if not cleaned:
        raise BusinessRuleError("La formule est requise")

    references = extract_references(cleaned)
    variable_map = {code: f"v_{index}" for index, code in enumerate(references)}
    expression = cleaned
    for code, variable in variable_map.items():
        expression = re.sub(r"\{" + re.escape(code) + r"\}", variable, expression, flags=re.IGNORECASE)
    return PreparedFormula(
        expression=expression,
        references=references,
        variable_map=variable_map,
    )


def parse_decimal(value: Any, *, label: str) -> Decimal:
    if value is None or value == "":
        raise BusinessRuleError(f"La valeur de {label} est requise")
    normalized = str(value).strip().replace(" ", "").replace("\u202f", "").replace("\xa0", "")
    if "," in normalized and "." not in normalized:
        normalized = normalized.replace(",", ".")
    try:
        return Decimal(normalized)
    except (InvalidOperation, ValueError) as exc:
        raise BusinessRuleError(f"La valeur de {label} doit être numérique") from exc


def evaluate_formula(
    *,
    formula: str,
    values: dict[str, Any] | None = None,
    expected_result_type: FormulaResultType,
) -> tuple[Any, list[str]]:
    prepared = prepare_formula(formula)
    value_map = values or {}
    variables = {}
    for code, variable in prepared.variable_map.items():
        source_value = value_map.get(code)
        if source_value is None:
            source_value = value_map.get(code.lower())
        variables[variable] = parse_decimal(source_value, label=code)

    try:
        tree = ast.parse(prepared.expression, mode="eval")
    except SyntaxError as exc:
        raise BusinessRuleError("Syntaxe de formule invalide") from exc

    result = _eval_node(tree.body, variables)
    if expected_result_type == FormulaResultType.boolean:
        if not isinstance(result, bool):
            raise BusinessRuleError("La formule doit retourner vrai ou faux")
    elif isinstance(result, bool) or not isinstance(result, Decimal):
        raise BusinessRuleError("La formule doit retourner une valeur numérique")
    return result, prepared.references


def validate_formula_syntax(*, formula: str, expected_result_type: FormulaResultType) -> list[str]:
    prepared = prepare_formula(formula)
    dummy_values = {code: "1" for code in prepared.references}
    evaluate_formula(
        formula=formula,
        values=dummy_values,
        expected_result_type=expected_result_type,
    )
    return prepared.references


def _eval_node(node: ast.AST, variables: dict[str, Decimal]) -> Any:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return node.value
        if isinstance(node.value, int | float):
            return Decimal(str(node.value))
        raise BusinessRuleError("Seules les constantes numériques sont autorisées")

    if isinstance(node, ast.Name):
        if node.id in variables:
            return variables[node.id]
        raise BusinessRuleError("Référence de formule inconnue")

    if isinstance(node, ast.BinOp):
        op = BIN_OPS.get(type(node.op))
        if op is None:
            raise BusinessRuleError("Opérateur de formule non pris en charge")
        left = _ensure_number(_eval_node(node.left, variables))
        right = _ensure_number(_eval_node(node.right, variables))
        try:
            return op(left, right)
        except (DivisionByZero, ZeroDivisionError, InvalidOperation) as exc:
            raise BusinessRuleError("Division par zéro ou calcul invalide") from exc

    if isinstance(node, ast.UnaryOp):
        op = UNARY_OPS.get(type(node.op))
        if op is None:
            raise BusinessRuleError("Opérateur unaire non pris en charge")
        value = _eval_node(node.operand, variables)
        if isinstance(node.op, ast.Not):
            return op(bool(value))
        return op(_ensure_number(value))

    if isinstance(node, ast.BoolOp):
        values = [_eval_node(value, variables) for value in node.values]
        if isinstance(node.op, ast.And):
            return all(bool(value) for value in values)
        if isinstance(node.op, ast.Or):
            return any(bool(value) for value in values)
        raise BusinessRuleError("Opérateur logique non pris en charge")

    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, variables)
        for op_node, comparator in zip(node.ops, node.comparators, strict=True):
            op = COMPARE_OPS.get(type(op_node))
            if op is None:
                raise BusinessRuleError("Comparaison non prise en charge")
            right = _eval_node(comparator, variables)
            if not op(left, right):
                return False
            left = right
        return True

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in SAFE_FUNCTIONS:
            raise BusinessRuleError("Fonction de formule non autorisée")
        if node.keywords:
            raise BusinessRuleError("Les arguments nommés ne sont pas autorisés")
        args = [_ensure_number(_eval_node(arg, variables)) for arg in node.args]
        if node.func.id == "round" and len(args) == 2:
            args = [args[0], int(args[1])]
        try:
            result = SAFE_FUNCTIONS[node.func.id](*args)
        except (TypeError, InvalidOperation, ValueError) as exc:
            raise BusinessRuleError("Arguments de fonction invalides") from exc
        if isinstance(result, int | float):
            return Decimal(str(result))
        return result

    raise BusinessRuleError("Expression de formule non autorisée")


def _ensure_number(value: Any) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, Decimal):
        raise BusinessRuleError("Une valeur numérique est attendue")
    return value
