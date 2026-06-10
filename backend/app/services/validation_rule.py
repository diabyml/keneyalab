"""Validation rule business logic and simulator."""

import re
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlmodel import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.lis import (
    Analyte,
    AnalyteDataType,
    GenderType,
    PatientContext,
    SortOrder,
    TargetGenderType,
    Unit,
    ValidationRule,
    ValidationRuleCreate,
    ValidationRuleDetailPublic,
    ValidationRuleSimulationRequest,
    ValidationRuleSimulationResponse,
    ValidationRuleUpdate,
)
from app.repositories import validation_rule as rule_repo

NUMERIC_FIELDS = {
    "absurd_min",
    "absurd_max",
    "panic_min",
    "panic_max",
    "normal_min",
    "normal_max",
    "expected_value",
    "max_delta_percent",
}
TEXT_FIELDS = {"regex_pattern", "validation_message"}
OPTION_FIELDS = {"allowed_values", "abnormal_values", "critical_values"}


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _decimal(value: str | Decimal | None) -> Decimal | None:
    if value is None or value == "":
        return None
    normalized = str(value).strip().replace(" ", "").replace("\u202f", "").replace("\xa0", "")
    if "," in normalized and "." not in normalized:
        normalized = normalized.replace(",", ".")
    try:
        return Decimal(normalized)
    except (InvalidOperation, ValueError) as exc:
        raise BusinessRuleError("La valeur doit être numérique") from exc


def _get_analyte(*, session: Session, analyte_id: uuid.UUID) -> Analyte:
    analyte = session.get(Analyte, analyte_id)
    if analyte is None or analyte.is_deleted:
        raise BusinessRuleError("Analyte non disponible")
    return analyte


def _ensure_context(*, session: Session, context_id: uuid.UUID | None) -> None:
    if context_id is None:
        return
    context = session.get(PatientContext, context_id)
    if context is None or context.is_deleted:
        raise BusinessRuleError("Contexte patient non disponible")


def _option_list(value: Any, *, field_name: str) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise BusinessRuleError(f"{field_name} doit être une liste")
    cleaned = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return cleaned or None


def _analyte_options(analyte: Analyte) -> set[str]:
    if not isinstance(analyte.options_data, list):
        return set()
    return {item.strip() for item in analyte.options_data if isinstance(item, str) and item.strip()}


def _validate_range(label: str, minimum: Decimal | None, maximum: Decimal | None) -> None:
    if minimum is not None and maximum is not None and minimum > maximum:
        raise BusinessRuleError(f"La borne minimale {label} doit être inférieure à la borne maximale")


def _validate_payload(*, session: Session, data: dict, current: ValidationRule | None = None) -> dict:
    analyte_id = data.get("analyte_id") or (current.analyte_id if current else None)
    if analyte_id is None:
        raise BusinessRuleError("Analyte requis")
    analyte = _get_analyte(session=session, analyte_id=analyte_id)
    data["analyte_id"] = analyte.id

    if "required_context_id" in data:
        _ensure_context(session=session, context_id=data["required_context_id"])

    min_age = data.get("min_age_years", current.min_age_years if current else None)
    max_age = data.get("max_age_years", current.max_age_years if current else None)
    if min_age is not None and min_age < 0:
        raise BusinessRuleError("L'âge minimal doit être positif")
    if max_age is not None and max_age < 0:
        raise BusinessRuleError("L'âge maximal doit être positif")
    if min_age is not None and max_age is not None and min_age > max_age:
        raise BusinessRuleError("L'âge minimal doit être inférieur à l'âge maximal")

    if "regex_pattern" in data:
        data["regex_pattern"] = _clean_text(data["regex_pattern"])
        if data["regex_pattern"]:
            try:
                re.compile(data["regex_pattern"])
            except re.error as exc:
                raise BusinessRuleError("Expression régulière invalide") from exc
    if "validation_message" in data:
        data["validation_message"] = _clean_text(data["validation_message"])

    for key in NUMERIC_FIELDS:
        if key in data:
            data[key] = _decimal(data[key])

    if "max_delta_percent" in data and data["max_delta_percent"] is not None and data["max_delta_percent"] < 0:
        raise BusinessRuleError("Le delta maximum doit être positif")

    for key in OPTION_FIELDS:
        if key in data:
            data[key] = _option_list(data[key], field_name=key)

    if analyte.data_type == AnalyteDataType.numeric:
        _validate_range("absurde", data.get("absurd_min"), data.get("absurd_max"))
        _validate_range("panique", data.get("panic_min"), data.get("panic_max"))
        _validate_range("normale", data.get("normal_min"), data.get("normal_max"))
        for key in TEXT_FIELDS | OPTION_FIELDS:
            data[key] = None
        data["is_required"] = False
        return data

    for key in NUMERIC_FIELDS:
        data[key] = None

    if analyte.data_type == AnalyteDataType.text:
        for key in OPTION_FIELDS:
            data[key] = None
        return data

    if analyte.data_type == AnalyteDataType.options:
        valid_options = _analyte_options(analyte)
        if not valid_options:
            raise BusinessRuleError("Cet analyte n'a pas d'options configurées")
        for key in OPTION_FIELDS:
            values = data.get(key)
            if values and not set(values).issubset(valid_options):
                raise BusinessRuleError("Les valeurs doivent appartenir aux options de l'analyte")
        data["regex_pattern"] = None
        data["validation_message"] = None
        data["is_required"] = False
        return data

    if analyte.data_type == AnalyteDataType.image:
        for key in TEXT_FIELDS | OPTION_FIELDS:
            data[key] = None
        return data

    return data


def _public(
    row: tuple[ValidationRule, Analyte, Unit | None, PatientContext | None]
) -> ValidationRuleDetailPublic:
    rule, analyte, unit, context = row
    return ValidationRuleDetailPublic(
        **rule.model_dump(),
        analyte_code=analyte.code,
        analyte_name=analyte.name,
        analyte_data_type=analyte.data_type,
        unit_name=unit.name if unit else None,
        required_context_name=context.name if context else None,
    )


def get_rules(
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
) -> tuple[list[ValidationRuleDetailPublic], int]:
    rows, count = rule_repo.get_all(
        session=session,
        skip=skip,
        limit=limit,
        search=_clean_text(search),
        analyte_id=analyte_id,
        data_type=data_type,
        is_active=is_active,
        target_gender=target_gender,
        required_context_id=required_context_id,
        age_years=age_years,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return [_public(row) for row in rows], count


def get_rule(*, session: Session, rule_id: uuid.UUID) -> ValidationRuleDetailPublic:
    row = rule_repo.get_detail(session=session, rule_id=rule_id)
    if row is None:
        raise NotFoundError("Règle de validation non trouvée")
    return _public(row)


def create_rule(*, session: Session, rule_in: ValidationRuleCreate) -> ValidationRuleDetailPublic:
    data = _validate_payload(session=session, data=rule_in.model_dump())
    db_rule = ValidationRule.model_validate(data)
    rule_repo.create(session=session, db_obj=db_rule)
    session.commit()
    return get_rule(session=session, rule_id=db_rule.id)


def update_rule(
    *, session: Session, rule_id: uuid.UUID, rule_in: ValidationRuleUpdate
) -> ValidationRuleDetailPublic:
    db_rule = rule_repo.get_by_id(session=session, rule_id=rule_id)
    if db_rule is None:
        raise NotFoundError("Règle de validation non trouvée")
    data = _validate_payload(
        session=session,
        data=rule_in.model_dump(exclude_unset=True),
        current=db_rule,
    )
    rule_repo.update(session=session, db_rule=db_rule, update_data=data)
    session.commit()
    return get_rule(session=session, rule_id=db_rule.id)


def _matches_patient(
    rule: ValidationRule,
    *,
    gender: GenderType | None,
    age_years: int | None,
    patient_context_id: uuid.UUID | None,
) -> bool:
    if rule.target_gender != TargetGenderType.all and gender != rule.target_gender.value:
        return False
    if rule.min_age_years is not None and (age_years is None or age_years < rule.min_age_years):
        return False
    if rule.max_age_years is not None and (age_years is None or age_years > rule.max_age_years):
        return False
    if rule.required_context_id is not None and rule.required_context_id != patient_context_id:
        return False
    return True


def _specificity(rule: ValidationRule) -> int:
    return sum(
        [
            rule.target_gender != TargetGenderType.all,
            rule.min_age_years is not None,
            rule.max_age_years is not None,
            rule.required_context_id is not None,
        ]
    )


def _matched_candidate(
    rows: list[tuple[ValidationRule, Analyte, Unit | None, PatientContext | None]],
    *,
    gender: GenderType | None,
    age_years: int | None,
    patient_context_id: uuid.UUID | None,
) -> tuple[ValidationRule, Analyte, Unit | None, PatientContext | None] | None:
    matches = [
        row
        for row in rows
        if _matches_patient(
            row[0],
            gender=gender,
            age_years=age_years,
            patient_context_id=patient_context_id,
        )
    ]
    if not matches:
        return None
    return sorted(matches, key=lambda row: (row[0].priority, _specificity(row[0]), row[0].created_at), reverse=True)[0]


def _simulate_numeric(
    rule: ValidationRule,
    *,
    result_value: str | None,
    previous_value: str | None,
) -> dict:
    value = _decimal(result_value)
    if value is None:
        return {"is_valid": False, "classification": "missing", "message": "Résultat numérique requis"}

    flags = {"is_valid": True, "is_abnormal": False, "is_critical": False, "is_absurd": False, "delta_flag": False}
    if (rule.absurd_min is not None and value < rule.absurd_min) or (rule.absurd_max is not None and value > rule.absurd_max):
        flags.update({"is_valid": False, "is_abnormal": True, "is_critical": True, "is_absurd": True})
        return {**flags, "classification": "absurd", "message": "Valeur absurde"}
    if (rule.panic_min is not None and value < rule.panic_min) or (rule.panic_max is not None and value > rule.panic_max):
        flags.update({"is_abnormal": True, "is_critical": True})
        return {**flags, "classification": "critical", "message": "Valeur critique"}
    if (rule.normal_min is not None and value < rule.normal_min) or (rule.normal_max is not None and value > rule.normal_max):
        flags["is_abnormal"] = True
        message = "Hors intervalle normal"
        classification = "abnormal"
    else:
        message = "Dans l'intervalle attendu"
        classification = "normal"

    previous = _decimal(previous_value)
    if previous is not None and previous != 0 and rule.max_delta_percent is not None:
        delta = abs((value - previous) / previous) * Decimal("100")
        if delta > rule.max_delta_percent:
            flags["delta_flag"] = True
            flags["is_abnormal"] = True
            message = "Variation delta au-dessus du seuil"
            classification = "delta"

    return {**flags, "classification": classification, "message": message}


def _simulate_text(rule: ValidationRule, *, result_value: str | None) -> dict:
    value = _clean_text(result_value)
    if rule.is_required and value is None:
        return {"is_valid": False, "is_abnormal": True, "classification": "missing", "message": rule.validation_message or "Résultat requis"}
    if value is not None and rule.regex_pattern and not re.fullmatch(rule.regex_pattern, value):
        return {"is_valid": False, "is_abnormal": True, "classification": "invalid", "message": rule.validation_message or "Format invalide"}
    return {"is_valid": True, "is_abnormal": False, "classification": "valid", "message": "Résultat valide"}


def _simulate_options(rule: ValidationRule, *, result_value: str | None, analyte: Analyte) -> dict:
    value = _clean_text(result_value)
    if value is None:
        return {"is_valid": False, "is_abnormal": True, "classification": "missing", "message": "Option requise"}
    allowed = set(rule.allowed_values or list(_analyte_options(analyte)))
    if value not in allowed:
        return {"is_valid": False, "is_abnormal": True, "classification": "invalid", "message": "Option non autorisée"}
    if value in set(rule.critical_values or []):
        return {"is_valid": True, "is_abnormal": True, "is_critical": True, "classification": "critical", "message": "Option critique"}
    if value in set(rule.abnormal_values or []):
        return {"is_valid": True, "is_abnormal": True, "classification": "abnormal", "message": "Option anormale"}
    return {"is_valid": True, "is_abnormal": False, "classification": "normal", "message": "Option valide"}


def _simulate_image(rule: ValidationRule, *, result_value: str | None) -> dict:
    if rule.is_required and _clean_text(result_value) is None:
        return {"is_valid": False, "is_abnormal": True, "classification": "missing", "message": "Image requise"}
    return {"is_valid": True, "is_abnormal": False, "classification": "valid", "message": "Image valide"}


def simulate_rule(
    *, session: Session, simulation_in: ValidationRuleSimulationRequest
) -> ValidationRuleSimulationResponse:
    _get_analyte(session=session, analyte_id=simulation_in.analyte_id)
    row = _matched_candidate(
        rule_repo.get_match_candidates(session=session, analyte_id=simulation_in.analyte_id),
        gender=simulation_in.gender,
        age_years=simulation_in.age_years,
        patient_context_id=simulation_in.patient_context_id,
    )
    if row is None:
        return ValidationRuleSimulationResponse(
            matched_rule=None,
            is_valid=True,
            classification="no_rule",
            message="Aucune règle applicable",
        )

    rule, analyte, _, _ = row
    if analyte.data_type == AnalyteDataType.numeric:
        result = _simulate_numeric(rule, result_value=simulation_in.result_value, previous_value=simulation_in.previous_value)
    elif analyte.data_type == AnalyteDataType.text:
        result = _simulate_text(rule, result_value=simulation_in.result_value)
    elif analyte.data_type == AnalyteDataType.options:
        result = _simulate_options(rule, result_value=simulation_in.result_value, analyte=analyte)
    else:
        result = _simulate_image(rule, result_value=simulation_in.result_value)

    return ValidationRuleSimulationResponse(
        matched_rule=_public(row),
        is_valid=result.get("is_valid", True),
        is_abnormal=result.get("is_abnormal", False),
        is_critical=result.get("is_critical", False),
        is_absurd=result.get("is_absurd", False),
        delta_flag=result.get("delta_flag", False),
        classification=result["classification"],
        message=result["message"],
    )
