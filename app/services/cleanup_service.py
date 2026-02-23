import time
import logging
import docker

client = docker.from_env()
logger = logging.getLogger(__name__)


def cleanup_user_resources(username: str) -> dict:
    """Удаляет все остановленные контейнеры и пустые сети пользователя."""
    removed_containers = []
    removed_networks = []

    stopped = client.containers.list(
        all=True,
        filters={
            "label": [
                "managed-by=mini-hosting",
                f"user={username}"
            ],
            "status": "exited"
        }
    )
    for c in stopped:
        removed_containers.append(c.name)
        c.remove()

    networks = client.networks.list(
        filters={"label": f"user={username}"}
    )
    for net in networks:
        net.reload()
        if not net.containers:
            removed_networks.append(net.name)
            net.remove()

    return {
        "removed_containers": removed_containers,
        "removed_networks": removed_networks,
    }


def cleanup_expired_containers():
    """
    Фоновая задача: каждую минуту чистит истёкшие контейнеры.
    Вызывается в отдельном потоке.
    """
    while True:
        try:
            containers = client.containers.list(
                filters={"label": "managed-by=mini-hosting"}
            )
            now = int(time.time())
            
            for c in containers:
                expires_at = int(c.labels.get("expires-at", 0))
                if expires_at and now > expires_at:
                    logger.info(f"TTL истёк: останавливаем {c.name}")
                    c.stop(timeout=5)
                    c.remove()
                    
        except Exception as e:
            logger.error(f"Ошибка при очистке: {e}")

        time.sleep(60)