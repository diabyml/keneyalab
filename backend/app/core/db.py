from sqlmodel import Session, create_engine, select

from app.core import audit as _audit  # noqa: F401
from app.core.config import settings
from app.core.rbac_init import seed_rbac
from app.models import User, UserCreate
from app.models.rbac import Role, UserRole
from app.services.user import create_user

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    # Seed RBAC data regardless of whether the superuser already exists
    # (upserts are idempotent — safe to run on every startup)
    seed_rbac(session)
    session.commit()

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = create_user(session=session, user_in=user_in)

        # Assign super_admin role to the first superuser (self-assigned)
        super_admin_role = session.exec(
            select(Role).where(Role.name == "super_admin")
        ).first()
        if super_admin_role:
            user_role = UserRole(
                user_id=user.id,
                role_id=super_admin_role.id,
                assigned_by_id=user.id,  # self-assigned — no other user exists
            )
            session.add(user_role)
            session.commit()
            session.refresh(user)
