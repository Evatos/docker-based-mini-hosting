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
- SQLAlchemy + SQLite
- JWT (python-jose) + bcrypt
- Traefik reverse-proxy (Linux/WSL2)

## Запуск

### Локально
```bash
p .env.example .env  # fill your SECRET_KEY
pip install fastapi uvicorn docker
uvicorn main:app --reload --port 5000
```

### Через Docker Compose (Linux / WSL2)
```bash
docker compose up --build
```

## Открыть документацию
http://localhost:5000/docs

## API

### Авторизация
- POST /auth/register  — регистрация
- POST /auth/login     — логин, возвращает JWT токен

### Контейнеры (требуют токен)
- POST   /containers/run       — запустить контейнер
- GET    /containers            — список своих контейнеров
- DELETE /containers/{id}      — остановить контейнер
- POST   /cleanup              — удалить остановленные контейнеры
- GET /networks         — список сетей

## Архитектура

Приложение подключается к Docker-демону через сокет (/var/run/docker.sock).
Каждый пользователь получает изолированную bridge-сеть.
Контейнеры помечаются label managed-by=mini-hosting
