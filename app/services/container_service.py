import time
import socket
import docker
from fastapi import HTTPException

from app.config import ALLOWED_IMAGES, CONTAINER_TTL, MAX_CONTAINERS_PER_USER
from app.services.network_service import get_or_create_network

client = docker.from_env()


def get_free_port() -> int:
    """Находит свободный порт."""
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def run_container(username: str, image_key: str) -> dict:
    """Запускает новый контейнер для пользователя."""
    
    user_containers = client.containers.list(
        filters={"label": f"user={username}"}
    )
    if len(user_containers) >= MAX_CONTAINERS_PER_USER:
        raise HTTPException(
            status_code=429,
            detail=f"максимум {MAX_CONTAINERS_PER_USER} контейнера на пользователя"
        )

    if image_key not in ALLOWED_IMAGES:
        raise HTTPException(status_code=400, detail={
            "error": f"образ '{image_key}' не разрешён",
            "allowed": list(ALLOWED_IMAGES.keys()),
        })

    image = ALLOWED_IMAGES[image_key]
    network = get_or_create_network(username)
    router_name = f"sandbox-{username}"
    ttyd_port = get_free_port()

    container = client.containers.run(
        image=image,
        command=f"ttyd -p 7681 -o bash",
        detach=True,
        network=network.name,
        mem_limit="128m",
        cpu_period=100000,
        cpu_quota=50000,
        privileged=False,
        cap_drop=["ALL"],
        ports={"7681/tcp": ttyd_port},
        labels={
            "managed-by": "mini-hosting",
            "user": username,
            "expires-at": str(int(time.time()) + CONTAINER_TTL),
            "traefik.enable": "true",
            f"traefik.http.routers.{router_name}.rule": f"Host(`{username}.localhost`)",
            f"traefik.http.services.{router_name}.loadbalancer.server.port": "80",
            f"traefik.http.routers.{router_name}.entrypoints": "web",
        }
    )

    return {
        "id": container.short_id,
        "name": container.name,
        "status": container.status,
        "image": image,
        "network": network.name,
        "url": f"http://{username}.localhost",
        "terminal_url": f"http://localhost:{ttyd_port}",
    }


def list_user_containers(username: str) -> list[dict]:
    """Возвращает список контейнеров пользователя."""
    containers = client.containers.list(
        filters={"label": f"user={username}"}
    )
    return [
        {
            "id": c.short_id,
            "name": c.name,
            "status": c.status,
            "user": c.labels.get("user", "unknown"),
        }
        for c in containers
    ]


def stop_container(container_id: str, username: str) -> dict:
    """Останавливает и удаляет контейнер."""
    try:
        container = client.containers.get(container_id)

        if container.labels.get("user") != username:
            raise HTTPException(status_code=403, detail="это не ваш контейнер")

        container.stop(timeout=5)
        container.remove()
        return {"message": f"контейнер {container_id} удалён"}

    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="контейнер не найден")