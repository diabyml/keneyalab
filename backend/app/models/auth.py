from sqlmodel import Field, SQLModel

from .rbac import PermissionPublic


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"
    permissions: list[PermissionPublic] = []


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
