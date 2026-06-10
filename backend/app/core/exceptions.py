class AppError(Exception):
    """Base for all domain exceptions. Never raised directly."""

    def __init__(self, message: str, *, code: str | None = None):
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(AppError):
    """Resource not found (→ 404)."""

    pass


class ConflictError(AppError):
    """Resource already exists or is in a conflicting state (→ 409)."""

    pass


class AuthenticationError(AppError):
    """Authentication/authorization failure (→ 401)."""

    pass


class ForbiddenError(AppError):
    """User does not have sufficient privileges (→ 403)."""

    pass


class BusinessRuleError(AppError):
    """Business rule violation (→ 400)."""

    pass


class AccountInactiveError(AppError):
    """Account is deactivated (→ 403)."""

    pass
