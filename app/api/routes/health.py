import docker
from fastapi import APIRouter

router = APIRouter(tags=["health"])
client = docker.from_env()


@router.get("/health")
def health_check():
    """Проверка состояния API и Docker."""
    try:
        client.ping()
        docker_status = "ok"
    except Exception:
        docker_status = "unavailable"

    return {
        "status": "ok",
        "docker": docker_status,
    }