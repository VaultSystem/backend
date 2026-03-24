from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from core.settings import settings
from core.storage.s3 import S3Storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    from core.storage.factory import get_storage

    storage = get_storage()

    if isinstance(storage, S3Storage):
        storage.client = await storage.session.client(...).__aenter__()

    yield

    if isinstance(storage, S3Storage):
        await storage.client.__aexit__(None, None, None)


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=1)
