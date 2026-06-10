"""InsuranceProvider repository - pure database access only."""

from uuid import UUID

from sqlmodel import Session, col, func, select

from app.models.lis import InsuranceProvider, SortOrder

SORT_COLUMNS = {
    "name": InsuranceProvider.name,
    "created_at": InsuranceProvider.created_at,
    "updated_at": InsuranceProvider.updated_at,
}


def get_by_id(*, session: Session, ip_id: UUID) -> InsuranceProvider | None:
    return session.get(InsuranceProvider, ip_id)


def get_all(
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
    conditions = []
    if is_deleted is not None:
        conditions.append(InsuranceProvider.is_deleted == is_deleted)
    elif not include_deleted:
        conditions.append(col(InsuranceProvider.is_deleted).is_(False))
    if search:
        conditions.append(col(InsuranceProvider.name).ilike(f"%{search.strip()}%"))
    base_query = select(InsuranceProvider)
    if conditions:
        base_query = base_query.where(*conditions)
    count_statement = select(func.count()).select_from(InsuranceProvider)
    if conditions:
        count_statement = count_statement.where(*conditions)
    count = session.exec(count_statement).one()
    sort_column = SORT_COLUMNS.get(sort_by or "name", InsuranceProvider.name)
    order_expr = col(sort_column).desc() if sort_order == SortOrder.desc else col(sort_column).asc()
    statement = base_query.order_by(order_expr).offset(skip).limit(limit)
    return list(session.exec(statement).all()), count


def create(*, session: Session, db_obj: InsuranceProvider) -> InsuranceProvider:
    session.add(db_obj)
    session.flush()
    return db_obj


def update(*, session: Session, db_obj: InsuranceProvider, update_data: dict) -> InsuranceProvider:
    db_obj.sqlmodel_update(update_data)
    session.add(db_obj)
    return db_obj


def soft_delete(*, session: Session, db_obj: InsuranceProvider) -> None:
    db_obj.is_deleted = True
    session.add(db_obj)
