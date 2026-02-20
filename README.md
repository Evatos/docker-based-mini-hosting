# Mini Hosting

Мини-хостинг на FastAPI + Docker SDK. Позволяет через REST API запускать 
изолированные контейнеры-песочницы.

## Что умеет

- Запускать контейнеры через HTTP запрос
- Изолировать пользователей в отдельные Docker-сети
- Ограничивать ресурсы (128MB RAM, 50% CPU)
- Чистить мусор — остановленные контейнеры и пустые сети

## Стек

- Python, FastAPI
- Docker SDK for Python
- Docker (Docker Outside of Docker через сокет)

## Запуск

### Локально
pip install fastapi uvicorn docker
uvicorn main:app --reload --port 5000

### Через Docker Compose (Linux / WSL2)
docker compose up --build

## Открыть документацию
http://localhost:5000/docs

## API

POST /containers/run  — запустить контейнер
GET  /containers      — список контейнеров
DELETE /containers/id — остановить контейнер
POST /cleanup         — удалить остановленные контейнеры и пустые сети
GET /networks         — список сетей

## Архитектура

Приложение подключается к Docker-демону через сокет (/var/run/docker.sock).
Каждый пользователь получает изолированную bridge-сеть.
Контейнеры помечаются label managed-by=mini-hosting