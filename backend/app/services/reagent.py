"""Reagent inventory business logic."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlmodel import Session, col, select

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.lis import (
    Reagent,
    ReagentAlertSummaryPublic,
    ReagentCreate,
    ReagentExpiryStatus,
    ReagentLot,
    ReagentLotCreate,
    ReagentLotPublic,
    ReagentLotsPublic,
    ReagentLotStatus,
    ReagentLotUpdate,
    ReagentMovementCreate,
    ReagentMovementType,
    ReagentPublic,
    ReagentSettings,
    ReagentSettingsPublic,
    ReagentSettingsUpdate,
    ReagentsPublic,
    ReagentStockMovement,
    ReagentStockMovementPublic,
    ReagentStockMovementsPublic,
    ReagentUpdate,
)
from app.repositories import reagent as reagent_repo

SETTINGS_ID = 1
ZERO = Decimal("0.000")


def _clean(data: dict) -> dict:
    cleaned = {}
    for key, value in data.items():
        if isinstance(value, str):
            value = value.strip()
            cleaned[key] = value or None
        else:
            cleaned[key] = value
    return cleaned


def _code(value: str) -> str:
    return value.strip().upper()


def _today() -> date:
    return datetime.now(timezone.utc).date()


def get_settings(*, session: Session) -> ReagentSettings:
    settings = session.get(ReagentSettings, SETTINGS_ID)
    if settings is None:
        settings = ReagentSettings(id=SETTINGS_ID)
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings


def get_settings_public(*, session: Session) -> ReagentSettingsPublic:
    return ReagentSettingsPublic.model_validate(get_settings(session=session))


def update_settings(
    *, session: Session, settings_in: ReagentSettingsUpdate, user_id: uuid.UUID
) -> ReagentSettingsPublic:
    settings = get_settings(session=session)
    updates = settings_in.model_dump(exclude_unset=True)
    if not updates:
        return ReagentSettingsPublic.model_validate(settings)
    for field_name, value in updates.items():
        setattr(settings, field_name, value)
    settings.updated_by_id = user_id
    settings.updated_at = datetime.now(timezone.utc)
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return ReagentSettingsPublic.model_validate(settings)


def _expiry_status(expiry_date: date, warning_days: int) -> ReagentExpiryStatus:
    days = (expiry_date - _today()).days
    if days < 0:
        return ReagentExpiryStatus.expired
    if days <= warning_days:
        return ReagentExpiryStatus.expiring
    return ReagentExpiryStatus.ok


def _lot_public(
    lot: ReagentLot, reagent: Reagent, settings: ReagentSettings
) -> ReagentLotPublic:
    warning_days = reagent.expiry_warning_days_override or settings.default_expiry_warning_days
    days_until_expiry = (lot.expiry_date - _today()).days
    return ReagentLotPublic(
        **lot.model_dump(),
        reagent_name=reagent.name,
        reagent_code=reagent.code,
        unit_label=reagent.unit_label,
        expiry_status=_expiry_status(lot.expiry_date, warning_days),
        days_until_expiry=days_until_expiry,
    )


def _reagent_public(
    reagent: Reagent, lots: list[ReagentLot], settings: ReagentSettings
) -> ReagentPublic:
    warning_days = reagent.expiry_warning_days_override or settings.default_expiry_warning_days
    non_expired_stock = ZERO
    total_stock = ZERO
    active_count = 0
    expiring_count = 0
    expired_count = 0
    for lot in lots:
        if lot.reagent_id != reagent.id or lot.status != ReagentLotStatus.active:
            continue
        active_count += 1
        total_stock += lot.current_quantity
        status = _expiry_status(lot.expiry_date, warning_days)
        if status == ReagentExpiryStatus.expired:
            expired_count += 1
        else:
            non_expired_stock += lot.current_quantity
            if status == ReagentExpiryStatus.expiring:
                expiring_count += 1
    low_stock = (
        reagent.minimum_stock_level is not None
        and non_expired_stock <= reagent.minimum_stock_level
    )
    return ReagentPublic(
        **reagent.model_dump(),
        total_stock=total_stock,
        active_lot_count=active_count,
        expiring_lot_count=expiring_count,
        expired_lot_count=expired_count,
        low_stock=low_stock,
    )


def list_reagents(
    *,
    session: Session,
    skip: int,
    limit: int,
    include_deleted: bool = False,
    is_deleted: bool | None = None,
    search: str | None = None,
    stock_status: str | None = None,
    expiry_status: ReagentExpiryStatus | None = None,
) -> ReagentsPublic:
    items, count = reagent_repo.list_reagents(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        is_deleted=is_deleted,
        search=search.strip() if search else None,
    )
    settings = get_settings(session=session)
    lots = reagent_repo.active_lots_for_reagents(
        session=session, reagent_ids=[item.id for item in items]
    )
    data = [_reagent_public(item, lots, settings) for item in items]
    if stock_status == "low":
        data = [item for item in data if item.low_stock]
    elif stock_status == "ok":
        data = [item for item in data if not item.low_stock]
    if expiry_status == ReagentExpiryStatus.expiring:
        data = [item for item in data if item.expiring_lot_count > 0]
    elif expiry_status == ReagentExpiryStatus.expired:
        data = [item for item in data if item.expired_lot_count > 0]
    elif expiry_status == ReagentExpiryStatus.ok:
        data = [
            item
            for item in data
            if item.expiring_lot_count == 0 and item.expired_lot_count == 0
        ]
    return ReagentsPublic(data=data, count=count if len(data) == len(items) else len(data))


def get_reagent(*, session: Session, reagent_id: uuid.UUID) -> ReagentPublic:
    reagent = reagent_repo.get_reagent(session=session, reagent_id=reagent_id)
    if reagent is None:
        raise NotFoundError("Réactif non trouvé")
    settings = get_settings(session=session)
    lots = reagent_repo.active_lots_for_reagents(session=session, reagent_ids=[reagent.id])
    return _reagent_public(reagent, lots, settings)


def create_reagent(*, session: Session, reagent_in: ReagentCreate) -> ReagentPublic:
    data = _clean(reagent_in.model_dump())
    data["code"] = _code(str(data["code"]))
    existing = reagent_repo.get_reagent_by_code(session=session, code=data["code"])
    if existing is not None:
        raise ConflictError("Un réactif avec ce code existe déjà")
    reagent = reagent_repo.create(session=session, db_obj=Reagent.model_validate(data))
    session.commit()
    session.refresh(reagent)
    return get_reagent(session=session, reagent_id=reagent.id)


def update_reagent(
    *, session: Session, reagent_id: uuid.UUID, reagent_in: ReagentUpdate
) -> ReagentPublic:
    reagent = reagent_repo.get_reagent(session=session, reagent_id=reagent_id)
    if reagent is None:
        raise NotFoundError("Réactif non trouvé")
    updates = _clean(reagent_in.model_dump(exclude_unset=True))
    if "code" in updates and updates["code"] is not None:
        updates["code"] = _code(str(updates["code"]))
        existing = reagent_repo.get_reagent_by_code(session=session, code=updates["code"])
        if existing is not None and existing.id != reagent.id:
            raise ConflictError("Un réactif avec ce code existe déjà")
    if "minimum_stock_level" in updates and updates["minimum_stock_level"] is not None:
        if updates["minimum_stock_level"] < 0:
            raise BusinessRuleError("Le seuil minimum ne peut pas être négatif")
    reagent_repo.update(session=session, db_obj=reagent, update_data=updates)
    reagent.updated_at = datetime.now(timezone.utc)
    session.commit()
    return get_reagent(session=session, reagent_id=reagent.id)


def delete_reagent(*, session: Session, reagent_id: uuid.UUID) -> None:
    reagent = reagent_repo.get_reagent(session=session, reagent_id=reagent_id)
    if reagent is None:
        raise NotFoundError("Réactif non trouvé")
    reagent.is_deleted = True
    reagent.updated_at = datetime.now(timezone.utc)
    session.add(reagent)
    session.commit()


def restore_reagent(*, session: Session, reagent_id: uuid.UUID) -> ReagentPublic:
    reagent = reagent_repo.get_reagent(session=session, reagent_id=reagent_id)
    if reagent is None:
        raise NotFoundError("Réactif non trouvé")
    reagent.is_deleted = False
    reagent.updated_at = datetime.now(timezone.utc)
    session.add(reagent)
    session.commit()
    return get_reagent(session=session, reagent_id=reagent.id)


def create_lot(
    *, session: Session, lot_in: ReagentLotCreate, user_id: uuid.UUID
) -> ReagentLotPublic:
    reagent = reagent_repo.get_reagent(session=session, reagent_id=lot_in.reagent_id)
    if reagent is None or reagent.is_deleted:
        raise NotFoundError("Réactif non trouvé")
    data = _clean(lot_in.model_dump())
    data["lot_number"] = str(data["lot_number"]).strip().upper()
    if data["initial_quantity"] <= 0:
        raise BusinessRuleError("La quantité reçue doit être supérieure à zéro")
    existing = reagent_repo.get_lot_by_number(
        session=session,
        reagent_id=lot_in.reagent_id,
        lot_number=data["lot_number"],
    )
    if existing is not None:
        raise ConflictError("Un lot avec ce numéro existe déjà pour ce réactif")
    lot = ReagentLot.model_validate({**data, "current_quantity": data["initial_quantity"]})
    reagent_repo.create(session=session, db_obj=lot)
    reagent_repo.create(
        session=session,
        db_obj=ReagentStockMovement(
            reagent_id=reagent.id,
            lot_id=lot.id,
            movement_type=ReagentMovementType.received,
            quantity=lot.initial_quantity,
            balance_after=lot.current_quantity,
            reason="Réception initiale",
            performed_by_id=user_id,
        ),
    )
    session.commit()
    session.refresh(lot)
    return _lot_public(lot, reagent, get_settings(session=session))


def update_lot(
    *, session: Session, lot_id: uuid.UUID, lot_in: ReagentLotUpdate
) -> ReagentLotPublic:
    lot = reagent_repo.get_lot(session=session, lot_id=lot_id)
    if lot is None:
        raise NotFoundError("Lot de réactif non trouvé")
    reagent = reagent_repo.get_reagent(session=session, reagent_id=lot.reagent_id)
    if reagent is None:
        raise NotFoundError("Réactif non trouvé")
    updates = _clean(lot_in.model_dump(exclude_unset=True))
    if "lot_number" in updates and updates["lot_number"] is not None:
        updates["lot_number"] = str(updates["lot_number"]).strip().upper()
        existing = reagent_repo.get_lot_by_number(
            session=session, reagent_id=reagent.id, lot_number=updates["lot_number"]
        )
        if existing is not None and existing.id != lot.id:
            raise ConflictError("Un lot avec ce numéro existe déjà pour ce réactif")
    reagent_repo.update(session=session, db_obj=lot, update_data=updates)
    lot.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(lot)
    return _lot_public(lot, reagent, get_settings(session=session))


def list_lots(
    *,
    session: Session,
    skip: int,
    limit: int,
    reagent_id: uuid.UUID | None = None,
    status: ReagentLotStatus | None = None,
    search: str | None = None,
    expiry_status: ReagentExpiryStatus | None = None,
) -> ReagentLotsPublic:
    rows, count = reagent_repo.list_lots(
        session=session,
        skip=skip,
        limit=limit,
        reagent_id=reagent_id,
        status=status,
        search=search.strip() if search else None,
    )
    settings = get_settings(session=session)
    data = [_lot_public(lot, reagent, settings) for lot, reagent in rows]
    if expiry_status:
        data = [item for item in data if item.expiry_status == expiry_status]
    return ReagentLotsPublic(data=data, count=count if len(data) == len(rows) else len(data))


def create_movement(
    *, session: Session, movement_in: ReagentMovementCreate, user_id: uuid.UUID
) -> ReagentStockMovementPublic:
    lot = session.exec(
        select(ReagentLot)
        .where(ReagentLot.id == movement_in.lot_id)
        .with_for_update()
    ).first()
    if lot is None:
        raise NotFoundError("Lot de réactif non trouvé")
    reagent = reagent_repo.get_reagent(session=session, reagent_id=lot.reagent_id)
    if reagent is None:
        raise NotFoundError("Réactif non trouvé")
    if lot.status == ReagentLotStatus.disposed:
        raise BusinessRuleError("Ce lot a déjà été éliminé")
    if movement_in.movement_type == ReagentMovementType.received:
        raise BusinessRuleError("Utilisez la réception de lot pour ajouter un stock initial")
    if (
        movement_in.movement_type == ReagentMovementType.used
        and _expiry_status(lot.expiry_date, 0) == ReagentExpiryStatus.expired
    ):
        raise BusinessRuleError("Impossible d'utiliser un lot expiré")
    if (
        movement_in.movement_type == ReagentMovementType.disposed
        and movement_in.quantity != lot.current_quantity
    ):
        raise BusinessRuleError(
            "La quantité éliminée doit correspondre au stock restant du lot"
        )

    quantity = movement_in.quantity
    next_balance = lot.current_quantity
    if movement_in.movement_type == ReagentMovementType.adjusted:
        next_balance += quantity
    elif movement_in.movement_type in {
        ReagentMovementType.used,
        ReagentMovementType.disposed,
    }:
        next_balance -= quantity
    if next_balance < 0:
        raise BusinessRuleError("Le stock ne peut pas devenir négatif")

    lot.current_quantity = next_balance
    if movement_in.movement_type == ReagentMovementType.disposed:
        lot.status = ReagentLotStatus.disposed
        lot.current_quantity = ZERO
        next_balance = ZERO
    elif lot.current_quantity == 0:
        lot.status = ReagentLotStatus.depleted
    else:
        lot.status = ReagentLotStatus.active
    lot.updated_at = datetime.now(timezone.utc)
    session.add(lot)
    movement = ReagentStockMovement(
        reagent_id=reagent.id,
        lot_id=lot.id,
        movement_type=movement_in.movement_type,
        quantity=quantity,
        balance_after=next_balance,
        reason=movement_in.reason.strip(),
        notes=(movement_in.notes or "").strip() or None,
        performed_by_id=user_id,
    )
    reagent_repo.create(session=session, db_obj=movement)
    session.commit()
    session.refresh(movement)
    return _movement_public(movement, reagent, lot)


def _movement_public(
    movement: ReagentStockMovement, reagent: Reagent, lot: ReagentLot
) -> ReagentStockMovementPublic:
    return ReagentStockMovementPublic(
        **movement.model_dump(),
        reagent_name=reagent.name,
        reagent_code=reagent.code,
        lot_number=lot.lot_number,
    )


def list_movements(
    *,
    session: Session,
    skip: int,
    limit: int,
    reagent_id: uuid.UUID | None = None,
    lot_id: uuid.UUID | None = None,
) -> ReagentStockMovementsPublic:
    rows, count = reagent_repo.list_movements(
        session=session,
        skip=skip,
        limit=limit,
        reagent_id=reagent_id,
        lot_id=lot_id,
    )
    return ReagentStockMovementsPublic(
        data=[_movement_public(movement, reagent, lot) for movement, reagent, lot in rows],
        count=count,
    )


def get_alert_summary(*, session: Session) -> ReagentAlertSummaryPublic:
    settings = get_settings(session=session)
    reagents = session.exec(select(Reagent).where(col(Reagent.is_deleted).is_(False))).all()
    lots = reagent_repo.active_lots_for_reagents(
        session=session, reagent_ids=[reagent.id for reagent in reagents]
    )
    data = [_reagent_public(reagent, lots, settings) for reagent in reagents]
    expiring_count = sum(item.expiring_lot_count for item in data)
    expired_count = sum(item.expired_lot_count for item in data)
    low_stock_count = sum(1 for item in data if item.low_stock)
    if not settings.expiry_alerts_enabled:
        expiring_count = 0
        expired_count = 0
    if not settings.low_stock_alerts_enabled:
        low_stock_count = 0
    return ReagentAlertSummaryPublic(
        expiring_count=expiring_count,
        expired_count=expired_count,
        low_stock_count=low_stock_count,
        total_count=expiring_count + expired_count + low_stock_count,
    )
