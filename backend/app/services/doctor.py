"""Doctor business logic."""

import uuid

from sqlmodel import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.lis import (
    Doctor,
    DoctorCommissionConfig,
    DoctorCommissionConfigCreate,
    DoctorCommissionConfigUpdate,
    DoctorCreate,
    DoctorUpdate,
    SortOrder,
    Title,
)
from app.repositories import doctor as doctor_repo


def _get_active_doctor(*, session: Session, doctor_id: uuid.UUID) -> Doctor:
    db_obj = doctor_repo.get_by_id(session=session, doctor_id=doctor_id)
    if db_obj is None:
        raise NotFoundError("Médecin non trouvé")
    if db_obj.is_deleted:
        raise BusinessRuleError("Le médecin supprimé doit être restauré avant modification")
    return db_obj


def _validate_title(*, session: Session, title_id: uuid.UUID | None) -> None:
    if title_id is None:
        return
    title = session.get(Title, title_id)
    if title is None or title.is_deleted:
        raise NotFoundError("Titre non trouvé")


def _validate_config_dates(
    *, effective_from, effective_until
) -> None:
    if effective_until is not None and effective_until < effective_from:
        raise BusinessRuleError("La date de fin ne peut pas précéder la date de début")


def _validate_config_overlap(
    *,
    session: Session,
    doctor_id: uuid.UUID,
    effective_from,
    effective_until,
    exclude_id: uuid.UUID | None = None,
) -> None:
    overlaps = doctor_repo.get_overlapping_configs(
        session=session,
        doctor_id=doctor_id,
        effective_from=effective_from,
        effective_until=effective_until,
        exclude_id=exclude_id,
    )
    if overlaps:
        raise BusinessRuleError("Une configuration de commission existe déjà sur cette période")


def create_doctor(*, session: Session, doctor_in: DoctorCreate) -> Doctor:
    _validate_title(session=session, title_id=doctor_in.title_id)
    db_obj = Doctor.model_validate(doctor_in)
    doctor_repo.create(session=session, db_obj=db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_doctors(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    is_deleted: bool | None = None,
    search: str | None = None,
    title_id: uuid.UUID | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.asc,
):
    return doctor_repo.get_all(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        is_deleted=is_deleted,
        search=search,
        title_id=title_id,
        sort_by=sort_by,
        sort_order=sort_order,
    )


def get_doctor(*, session: Session, doctor_id: uuid.UUID) -> Doctor:
    db_obj = doctor_repo.get_by_id(session=session, doctor_id=doctor_id)
    if db_obj is None:
        raise NotFoundError("Médecin non trouvé")
    return db_obj


def get_doctor_with_title(*, session: Session, doctor_id: uuid.UUID):
    row = doctor_repo.get_with_title_by_id(session=session, doctor_id=doctor_id)
    if row is None:
        raise NotFoundError("Médecin non trouvé")
    return row


def update_doctor(
    *, session: Session, doctor_id: uuid.UUID, doctor_in: DoctorUpdate
) -> Doctor:
    db_obj = _get_active_doctor(session=session, doctor_id=doctor_id)
    data = doctor_in.model_dump(exclude_unset=True)
    if "title_id" in data:
        _validate_title(session=session, title_id=data["title_id"])
    doctor_repo.update(session=session, db_obj=db_obj, update_data=data)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def delete_doctor(*, session: Session, doctor_id: uuid.UUID) -> None:
    db_obj = doctor_repo.get_by_id(session=session, doctor_id=doctor_id)
    if db_obj is None:
        raise NotFoundError("Médecin non trouvé")
    doctor_repo.soft_delete(session=session, db_obj=db_obj)
    session.commit()


def restore_doctor(*, session: Session, doctor_id: uuid.UUID) -> Doctor:
    db_obj = doctor_repo.get_by_id(session=session, doctor_id=doctor_id)
    if db_obj is None:
        raise NotFoundError("Médecin non trouvé")
    doctor_repo.update(session=session, db_obj=db_obj, update_data={"is_deleted": False})
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_commission_configs(
    *,
    session: Session,
    doctor_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.desc,
) -> tuple[list[DoctorCommissionConfig], int]:
    get_doctor(session=session, doctor_id=doctor_id)
    return doctor_repo.get_configs(
        session=session,
        doctor_id=doctor_id,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )


def create_commission_config(
    *,
    session: Session,
    doctor_id: uuid.UUID,
    config_in: DoctorCommissionConfigCreate,
) -> DoctorCommissionConfig:
    _get_active_doctor(session=session, doctor_id=doctor_id)
    _validate_config_dates(
        effective_from=config_in.effective_from,
        effective_until=config_in.effective_until,
    )
    _validate_config_overlap(
        session=session,
        doctor_id=doctor_id,
        effective_from=config_in.effective_from,
        effective_until=config_in.effective_until,
    )
    db_obj = DoctorCommissionConfig.model_validate(
        {**config_in.model_dump(), "doctor_id": doctor_id}
    )
    doctor_repo.create_config(session=session, db_obj=db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_commission_config(
    *,
    session: Session,
    config_id: uuid.UUID,
    config_in: DoctorCommissionConfigUpdate,
) -> DoctorCommissionConfig:
    db_obj = doctor_repo.get_config_by_id(session=session, config_id=config_id)
    if db_obj is None:
        raise NotFoundError("Configuration de commission non trouvée")
    data = config_in.model_dump(exclude_unset=True)
    next_effective_from = db_obj.effective_from
    next_effective_until = data.get("effective_until", db_obj.effective_until)
    _validate_config_dates(
        effective_from=next_effective_from,
        effective_until=next_effective_until,
    )
    _validate_config_overlap(
        session=session,
        doctor_id=db_obj.doctor_id,
        effective_from=next_effective_from,
        effective_until=next_effective_until,
        exclude_id=config_id,
    )
    doctor_repo.update_config(session=session, db_obj=db_obj, update_data=data)
    session.commit()
    session.refresh(db_obj)
    return db_obj
