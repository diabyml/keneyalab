import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.exceptions import (
    AccountInactiveError,
    AppError,
    AuthenticationError,
    BusinessRuleError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ---------------------------------------------------------------------------
# Domain exception handlers — map service-layer exceptions to HTTP responses
# ---------------------------------------------------------------------------

@app.exception_handler(NotFoundError)
async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": exc.message})


@app.exception_handler(ConflictError)
async def conflict_handler(_request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": exc.message})


@app.exception_handler(AuthenticationError)
async def authentication_handler(_request: Request, exc: AuthenticationError) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": exc.message})


@app.exception_handler(ForbiddenError)
async def forbidden_handler(_request: Request, exc: ForbiddenError) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": exc.message})


@app.exception_handler(BusinessRuleError)
async def business_rule_handler(_request: Request, exc: BusinessRuleError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": exc.message})


@app.exception_handler(AccountInactiveError)
async def account_inactive_handler(_request: Request, exc: AccountInactiveError) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": exc.message})


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": exc.message})


app.include_router(api_router, prefix=settings.API_V1_STR)
