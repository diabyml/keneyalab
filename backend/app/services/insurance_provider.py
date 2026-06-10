"""InsuranceProvider business logic — CRUD for reference data."""

import uuid

from sqlmodel import Session

from app.core.exceptions import NotFoundError
from app.models.lis import (
    InsuranceProvider,
    InsuranceProviderCreate,
    InsuranceProviderUpdate,
    SortOrder,
)
from app.repositories import insurance_provider as ip_repo


def create_insurance_provider(*, session: Session, ip_in: InsuranceProviderCreate) -> InsuranceProvider:
    db_obj = InsuranceProvider.model_validate(ip_in)
    ip_repo.create(session=session, db_obj=db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_insurance_providers(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    is_deleted: bool | None = None,
    search: str | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.asc,
) -> tuple[list[InsuranceProvider], int]:
    return ip_repo.get_all(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        is_deleted=is_deleted,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


def get_insurance_provider(*, session: Session, ip_id: uuid.UUID) -> InsuranceProvider:
    db_obj = ip_repo.get_by_id(session=session, ip_id=ip_id)
    if db_obj is None:
        raise NotFoundError("Assureur non trouvé")
    return db_obj


def update_insurance_provider(*, session: Session, ip_id: uuid.UUID, ip_in: InsuranceProviderUpdate) -> InsuranceProvider:
    db_obj = ip_repo.get_by_id(session=session, ip_id=ip_id)
    if db_obj is None:
        raise NotFoundError("Assureur non trouvé")
    ip_repo.update(session=session, db_obj=db_obj, update_data=ip_in.model_dump(exclude_unset=True))
    session.commit()
    session.refresh(db_obj)
    return db_obj


def delete_insurance_provider(*, session: Session, ip_id: uuid.UUID) -> None:
    db_obj = ip_repo.get_by_id(session=session, ip_id=ip_id)
    if db_obj is None:
        raise NotFoundError("Assureur non trouvé")
    ip_repo.soft_delete(session=session, db_obj=db_obj)
    session.commit()


def restore_insurance_provider(*, session: Session, ip_id: uuid.UUID) -> InsuranceProvider:
    db_obj = ip_repo.get_by_id(session=session, ip_id=ip_id)
    if db_obj is None:
        raise NotFoundError("Assureur non trouvé")
    ip_repo.update(session=session, db_obj=db_obj, update_data={"is_deleted": False})
    session.commit()
    session.refresh(db_obj)
    return db_obj
