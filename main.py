import docker
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import User, get_db
from auth import hash_password, verify_password, create_token, get_current_user
from fastapi import Depends

app = FastAPI()
client = docker.from_env()

ALLOWED_IMAGES = {
    "alpine": "alpine:latest",
    "ubuntu": "ubuntu:22.04",
    "nginx": "nginx:alpine",
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


@app.post("/auth/register", status_code=201)
def register(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    if db.get(User, form.username):
        raise HTTPException(status_code=400, detail="пользователь уже существует")

    user = User(
        username=form.username,
        hashed_password=hash_password(form.password)
    )
    db.add(user)
    db.commit()
    return {"message": f"пользователь {form.username} создан"}


@app.post("/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user: User | None = db.get(User, form.username)

    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="неверный логин или пароль")

    token = create_token(user.username)

    return {"access_token": token, "token_type": "bearer"}


@app.post("/containers/run", status_code=201)
def run_container(
        body: RunRequest,
        current_user: User = Depends(get_current_user),
):

    user = current_user.username

    if body.image not in ALLOWED_IMAGES:
        raise HTTPException(status_code=400, detail={
            "error": f"образ '{body.image}' не разрешён",
            "allowed": list(ALLOWED_IMAGES.keys()),
        })

    image = ALLOWED_IMAGES[body.image]
    network = get_or_create_network(user)
    router_name = f"sandbox-{user}"

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
            "user": user,
            "traefik.enable": "true",
            f"traefik.http.routers.{router_name}.rule": f"Host({user}.localhost)",
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
        "url": f"http://{user}.localhost",
    }


@app.get("/containers")
def list_containers(current_user: User = Depends(get_current_user)):
    containers = client.containers.list(
        filters={
            "label": f"user={current_user.username}"
        }
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
def list_networks(current_user: User = Depends(get_current_user)):
    networks = client.networks.list(
        filters={"label": f"user={current_user.username}"}
    )
    return [
        {
            "name": n.name,
            "user": n.attrs["Labels"].get("user", "unknown"),
        }
        for n in networks
    ]

@app.delete("/containers/{container_id}")
def stop_container(container_id: str, current_user: User = Depends(get_current_user)):
    """
    Останавливает и удаляет конкретный контейнер.
    container_id берётся прямо из URL: DELETE /containers/abc123
    """
    try:
        container = client.containers.get(container_id)

        if container.labels.get("user") != current_user.username:
            raise HTTPException(status_code=403, detail="это не ваш контейнер")

        container.stop(timeout=5)
        container.remove()
        return {"message": f"контейнер {container_id} удалён"}

    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="контейнер не найден")


@app.post("/cleanup")
def cleanup(current_user: User = Depends(get_current_user)):
    """
    Удаляет все остановленные контейнеры и пустые сети.
    """
    removed_containers = []
    removed_networks = []

    stopped = client.containers.list(
        all=True,
        filters={
            "label": [
                "managed-by=mini-hosting",
                f"user={current_user.username}"
            ],
            "status": "exited"
        }
    )
    for c in stopped:
        removed_containers.append(c.name)
        c.remove()

    networks = client.networks.list(
        filters={"label": f"user={current_user.username}"}
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
