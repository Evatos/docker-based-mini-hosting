from pydantic import BaseModel


class RunRequest(BaseModel):
    """Запрос на запуск контейнера."""
    image: str = "alpine"


class ContainerResponse(BaseModel):
    """Ответ с информацией о запущенном контейнере."""
    id: str
    name: str
    status: str
    image: str
    network: str
    url: str
    terminal_url: str


class ContainerListItem(BaseModel):
    """Элемент списка контейнеров."""
    id: str
    name: str
    status: str
    user: str


class NetworkListItem(BaseModel):
    """Элемент списка сетей."""
    name: str
    user: str


class CleanupResponse(BaseModel):
    """Результат очистки."""
    removed_containers: list[str]
    removed_networks: list[str]