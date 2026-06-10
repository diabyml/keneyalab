"""Analyte business logic - CRUD for catalog setup."""

import uuid
from typing import Any

from sqlmodel import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.lis import Analyte, AnalyteCreate, AnalyteDataType, AnalyteUpdate, FormulaResultType
from app.repositories import analyte as analyte_repo
from app.services import formula as formula_service


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _validate_options(options_data: Any) -> list[str]:
    if not isinstance(options_data, list):
        raise BusinessRuleError("Les options doivent être une liste non vide")
    options = [item.strip() for item in options_data if isinstance(item, str)]
    options = [item for item in options if item]
    if not options:
        raise BusinessRuleError("Les options doivent être une liste non vide")
    return options


def _validate_payload(*, session: Session, data: dict) -> dict:
    if "code" in data and data["code"] is not None:
        data["code"] = data["code"].strip().upper()
        if not data["code"]:
            raise BusinessRuleError("Le code est requis")

    if "name" in data and data["name"] is not None:
        data["name"] = data["name"].strip()
        if not data["name"]:
            raise BusinessRuleError("Le nom est requis")

    if "calculation_formula" in data:
        data["calculation_formula"] = _clean_text(data["calculation_formula"])

    if data.get("data_type") == AnalyteDataType.options:
        data["options_data"] = _validate_options(data.get("options_data"))
    elif "options_data" in data:
        data["options_data"] = None

    if data.get("is_calculated") is True and not data.get("calculation_formula"):
        raise BusinessRuleError("La formule de calcul est requise")
    if data.get("is_calculated") is True:
        formula_service.validate_formula(
            session=session,
            formula=data["calculation_formula"],
            expected_result_type=FormulaResultType.number,
        )

    if data.get("is_calculated") is False:
        data["calculation_formula"] = None

    return data


def _merged_payload(db_analyte: Analyte, update_data: dict) -> dict:
    current = {
        "code": db_analyte.code,
        "name": db_analyte.name,
        "unit_id": db_analyte.unit_id,
        "data_type": db_analyte.data_type,
        "options_data": db_analyte.options_data,
        "reference_text": db_analyte.reference_text,
        "is_calculated": db_analyte.is_calculated,
        "calculation_formula": db_analyte.calculation_formula,
    }
    current.update(update_data)
    return current


def _ensure_unique_code(
    *, session: Session, code: str, exclude_id: uuid.UUID | None = None
) -> None:
    existing = analyte_repo.get_by_code(session=session, code=code)
    if existing is not None and existing.id != exclude_id:
        raise ConflictError("Code d'analyte déjà utilisé")


def create_analyte(*, session: Session, analyte_in: AnalyteCreate) -> Analyte:
    data = _validate_payload(session=session, data=analyte_in.model_dump())
    _ensure_unique_code(session=session, code=data["code"])
    db_analyte = Analyte.model_validate(data)
    analyte_repo.create(session=session, db_obj=db_analyte)
    session.commit()
    session.refresh(db_analyte)
    return db_analyte


def get_analytes(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    is_deleted: bool | None = None,
    search: str | None = None,
    data_type: AnalyteDataType | None = None,
    is_calculated: bool | None = None,
) -> tuple[list[Analyte], int]:
    return analyte_repo.get_all(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        is_deleted=is_deleted,
        search=_clean_text(search),
        data_type=data_type,
        is_calculated=is_calculated,
    )


def get_analyte(*, session: Session, analyte_id: uuid.UUID) -> Analyte:
    db_analyte = analyte_repo.get_by_id(session=session, analyte_id=analyte_id)
    if db_analyte is None:
        raise NotFoundError("Analyte non trouvé")
    return db_analyte


def update_analyte(
    *, session: Session, analyte_id: uuid.UUID, analyte_in: AnalyteUpdate
) -> Analyte:
    db_analyte = analyte_repo.get_by_id(session=session, analyte_id=analyte_id)
    if db_analyte is None:
        raise NotFoundError("Analyte non trouvé")

    update_data = analyte_in.model_dump(exclude_unset=True)
    merged = _validate_payload(session=session, data=_merged_payload(db_analyte, update_data))
    if "code" in update_data:
        _ensure_unique_code(
            session=session, code=merged["code"], exclude_id=db_analyte.id
        )

    applied_data = {key: merged[key] for key in update_data}
    if merged["data_type"] != AnalyteDataType.options:
        applied_data["options_data"] = None
    if merged["is_calculated"] is False:
        applied_data["calculation_formula"] = None

    analyte_repo.update(
        session=session, db_analyte=db_analyte, update_data=applied_data
    )
    session.commit()
    session.refresh(db_analyte)
    return db_analyte


def delete_analyte(*, session: Session, analyte_id: uuid.UUID) -> None:
    db_analyte = analyte_repo.get_by_id(session=session, analyte_id=analyte_id)
    if db_analyte is None:
        raise NotFoundError("Analyte non trouvé")

    analyte_repo.soft_delete(session=session, db_analyte=db_analyte)
    session.commit()


def restore_analyte(*, session: Session, analyte_id: uuid.UUID) -> Analyte:
    db_analyte = analyte_repo.get_by_id(session=session, analyte_id=analyte_id)
    if db_analyte is None:
        raise NotFoundError("Analyte non trouvé")

    analyte_repo.update(
        session=session, db_analyte=db_analyte, update_data={"is_deleted": False}
    )
    session.commit()
    session.refresh(db_analyte)
    return db_analyte
