import docker
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
client = docker.from_env()

ALLOWED_IMAGES = {
    "alpine": "alpine:latest",
    "ubuntu": "ubuntu:22.04",
}


def get_or_create_network(user: str):
    """
    Возвращает сеть пользователя, создавая её если не существует.
    Называем сеть net-{user}
    """
    network_name = f"net-{user}"

    try:
        network = client.networks.get(network_name)
        print(f"Сеть {network_name} уже существует")
        return network
    except docker.errors.NotFound:
        print(f"Создаём новую сеть {network_name}")
        network = client.networks.create(
            name=network_name,
            driver="bridge",
            labels={
                "managed-by": "mini-hosting",
                "user": user,
            }
        )
        return network


class RunRequest(BaseModel):
    image: str = "alpine"
    user: str = "anonymous"


@app.post("/containers/run", status_code=201)
def run_container(body: RunRequest):
    if body.image not in ALLOWED_IMAGES:
        raise HTTPException(status_code=400, detail={
            "error": f"образ '{body.image}' не разрешён",
            "allowed": list(ALLOWED_IMAGES.keys()),
        })

    image = ALLOWED_IMAGES[body.image]
    network = get_or_create_network(body.user)

    router_name = f"sandbox-{body.user}"

    container = client.containers.run(
        image=image,
        command="sleep 60",
        detach=True,
        network=network.name,
        mem_limit="128m",
        cpu_period=100000,
        cpu_quota=50000,
        privileged=False,
        cap_drop=["ALL"],
        labels={
            "managed-by": "mini-hosting",
            "user": body.user,

            "traefik.enable": "true",
            f"traefik.http.routers.{router_name}.rule": f"Host({body.user}.localhost)",
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
        "url": f"http://{body.user}.localhost",
    }


@app.get("/containers")
def list_containers():
    containers = client.containers.list(
        filters={"label": "managed-by=mini-hosting"}
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


@app.get("/networks")
def list_networks():
    networks = client.networks.list(
        filters={"label": "managed-by=mini-hosting"}
    )
    return [
        {
            "name": n.name,
            "user": n.attrs["Labels"].get("user", "unknown"),
        }
        for n in networks
    ]

@app.delete("/containers/{container_id}")
def stop_container(container_id: str):
    """
    Останавливает и удаляет конкретный контейнер.
    container_id берётся прямо из URL: DELETE /containers/abc123
    """
    try:
        container = client.containers.get(container_id)

        if container.labels.get("managed-by") != "mini-hosting":
            raise HTTPException(status_code=403, detail="не наш контейнер")

        container.stop(timeout=5)
        container.remove()
        return {"message": f"контейнер {container_id} удалён"}

    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="контейнер не найден")


@app.post("/cleanup")
def cleanup():
    """
    Удаляет все остановленные контейнеры и пустые сети.
    """
    removed_containers = []
    removed_networks = []

    stopped = client.containers.list(
        all=True,
        filters={
            "label": "managed-by=mini-hosting",
            "status": "exited"
        }
    )
    for c in stopped:
        removed_containers.append(c.name)
        c.remove()

    networks = client.networks.list(
        filters={"label": "managed-by=mini-hosting"}
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