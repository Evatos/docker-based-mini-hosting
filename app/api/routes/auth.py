from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db import User, get_db
from app.core import hash_password, verify_password, create_token
from app.schemas import TokenResponse, MessageResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=MessageResponse)
def register(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Регистрация нового пользователя."""
    if db.get(User, form.username):
        raise HTTPException(status_code=400, detail="пользователь уже существует")

    user = User(
        username=form.username,
        hashed_password=hash_password(form.password)
    )
    db.add(user)
    db.commit()
    
    return {"message": f"пользователь {form.username} создан"}


@router.post("/login", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Вход пользователя, возвращает JWT токен."""
    user: User | None = db.get(User, form.username)

    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="неверный логин или пароль")

    token = create_token(user.username)

    return {"access_token": token, "token_type": "bearer"}