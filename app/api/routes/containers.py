from fastapi import APIRouter, Depends, Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db import User
from app.core import get_current_user
from app.schemas import (
    RunRequest,
    ContainerResponse,
    ContainerListItem,
    NetworkListItem,
    CleanupResponse
)
from app.services import (
    run_container,
    list_user_containers,
    stop_container
)
from app.services.network_service import list_user_networks
from app.services.cleanup_service import cleanup_user_resources

router = APIRouter(prefix="/containers", tags=["containers"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/run", status_code=201, response_model=ContainerResponse)
@limiter.limit("5/minute")
def create_container(
    request: Request,
    body: RunRequest,
    current_user: User = Depends(get_current_user),
):
    """Запускает новый контейнер для текущего пользователя."""
    result = run_container(
        username=current_user.username,
        image_key=body.image
    )
    return result


@router.get("", response_model=list[ContainerListItem])
def get_containers(current_user: User = Depends(get_current_user)):
    """Возвращает список контейнеров текущего пользователя."""
    return list_user_containers(current_user.username)


@router.delete("/{container_id}")
def delete_container(
    container_id: str,
    current_user: User = Depends(get_current_user)
):
    """Останавливает и удаляет контейнер."""
    return stop_container(container_id, current_user.username)


@router.get("/networks", response_model=list[NetworkListItem])
def get_networks(current_user: User = Depends(get_current_user)):
    """Возвращает список сетей текущего пользователя."""
    return list_user_networks(current_user.username)


@router.post("/cleanup", response_model=CleanupResponse)
def cleanup_resources(current_user: User = Depends(get_current_user)):
    """Удаляет остановленные контейнеры и пустые сети."""
    return cleanup_user_resources(current_user.username)