from fastapi import APIRouter, status

from apps.dependencies import CurrentUser, DBSession
from apps.users.schemas import (
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserProfileReadSchema,
    UserReadLightSchema,
)
from apps.users.service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserReadLightSchema,
    status_code=status.HTTP_201_CREATED,
)
async def register(payload: UserCreate, session: DBSession):
    return await UserService(session).register(payload)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: DBSession):
    return await UserService(session).login(payload)


@router.get("/me", response_model=UserProfileReadSchema)
async def me(current_user: CurrentUser):
    return current_user
