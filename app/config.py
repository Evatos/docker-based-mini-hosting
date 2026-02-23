import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-key")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "60"))

CONTAINER_TTL = 60
MAX_CONTAINERS_PER_USER = 3

ALLOWED_IMAGES = {
    "alpine": "alpine:latest",
    "ubuntu": "ubuntu:22.04",
    "nginx": "nginx:alpine",
    "sandbox": "sandbox:latest",
}


DATABASE_URL = "sqlite:///users.db"