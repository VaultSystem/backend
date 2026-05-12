from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from apps.routers import api_router
from core.exceptions import VaultError
from core.middleware.rate_limit import InMemoryRateLimitMiddleware
from core.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    from core.storage.factory import get_storage

    get_storage()
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="Vault API",
        description="Encrypted, versioned secrets management API.",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        InMemoryRateLimitMiddleware,
        enabled=settings.RATE_LIMIT_ENABLED,
        requests=settings.RATE_LIMIT_REQUESTS,
        window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )
    application.include_router(api_router)

    @application.exception_handler(VaultError)
    async def vault_error_handler(_: Request, exc: VaultError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
            },
        )

    @application.get("/healthz", tags=["health"])
    async def healthz():
        return {"status": "ok"}

    return application


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=1)
