import docker
from docker.models.networks import Network

client = docker.from_env()

def get_or_create_network(username: str) -> Network:
    """
    Возвращает сеть пользователя, создавая её если не существует.
    Называем сеть net-{user}
    """
    network_name = f"net-{username}"

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
                "user": username,
            }
        )
        return network


def list_user_networks(username: str) -> list[dict]:
    networks = client.networks.list(
        filters={"label": f"user={username}"}
    )
    return [
        {
            "name": n.name,
            "user": n.attrs["Labels"].get("user", "unknown"),
        }
        for n in networks
    ]