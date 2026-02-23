import logging
import threading
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.routes import auth, containers, health
from app.services.cleanup_service import cleanup_expired_containers


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

app = FastAPI(
    title="Mini Hosting API",
    description="Docker-based container hosting platform",
    version="1.0.0"
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

Instrumentator().instrument(app).expose(app)

app.include_router(auth.router)
app.include_router(containers.router)
app.include_router(health.router)

cleanup_thread = threading.Thread(
    target=cleanup_expired_containers,
    daemon=True
)
cleanup_thread.start()


@app.get("/")
def root():
    """Главная страница API."""
    return {
        "message": "Mini Hosting API",
        "docs": "/docs",
        "health": "/health"
    }