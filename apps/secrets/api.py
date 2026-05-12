from fastapi import APIRouter, Query, Response, status

from apps.dependencies import CurrentUser, DBSession
from apps.secrets.schemas import (
    PaginatedSecrets,
    SecretCreate,
    SecretGrantRequest,
    SecretRead,
    SecretRollbackRequest,
    SecretUpdate,
    SecretValueRead,
    SecretVersionRead,
)
from apps.secrets.service import SecretService

router = APIRouter(prefix="/secrets", tags=["secrets"])


@router.post("", response_model=SecretRead, status_code=status.HTTP_201_CREATED)
async def create_secret(
    payload: SecretCreate,
    session: DBSession,
    current_user: CurrentUser,
):
    return await SecretService(session).create_secret(actor=current_user, payload=payload)


@router.get("", response_model=PaginatedSecrets)
async def list_secrets(
    session: DBSession,
    current_user: CurrentUser,
    search: str | None = Query(default=None, min_length=1, max_length=120),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return await SecretService(session).list_secrets(
        actor=current_user,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get("/{secret_id}", response_model=SecretValueRead)
async def read_secret(
    secret_id: int,
    session: DBSession,
    current_user: CurrentUser,
):
    return await SecretService(session).read_secret(
        actor=current_user,
        secret_id=secret_id,
    )


@router.put("/{secret_id}", response_model=SecretRead)
async def update_secret(
    secret_id: int,
    payload: SecretUpdate,
    session: DBSession,
    current_user: CurrentUser,
):
    return await SecretService(session).update_secret(
        actor=current_user,
        secret_id=secret_id,
        payload=payload,
    )


@router.delete("/{secret_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_secret(
    secret_id: int,
    session: DBSession,
    current_user: CurrentUser,
):
    await SecretService(session).delete_secret(actor=current_user, secret_id=secret_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{secret_id}/versions", response_model=list[SecretVersionRead])
async def list_versions(
    secret_id: int,
    session: DBSession,
    current_user: CurrentUser,
):
    return await SecretService(session).list_versions(
        actor=current_user,
        secret_id=secret_id,
    )


@router.get("/{secret_id}/versions/{version}", response_model=SecretValueRead)
async def read_secret_version(
    secret_id: int,
    version: int,
    session: DBSession,
    current_user: CurrentUser,
):
    return await SecretService(session).read_secret(
        actor=current_user,
        secret_id=secret_id,
        version=version,
    )


@router.post("/{secret_id}/rollback", response_model=SecretRead)
async def rollback_secret(
    secret_id: int,
    payload: SecretRollbackRequest,
    session: DBSession,
    current_user: CurrentUser,
):
    return await SecretService(session).rollback(
        actor=current_user,
        secret_id=secret_id,
        payload=payload,
    )


@router.post("/{secret_id}/access", status_code=status.HTTP_204_NO_CONTENT)
async def grant_access(
    secret_id: int,
    payload: SecretGrantRequest,
    session: DBSession,
    current_user: CurrentUser,
):
    await SecretService(session).grant_access(
        actor=current_user,
        secret_id=secret_id,
        payload=payload,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
