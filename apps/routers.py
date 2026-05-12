from fastapi import APIRouter

from apps.secrets.api import router as secrets_router
from apps.users.api import router as users_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(users_router)
api_router.include_router(secrets_router)
