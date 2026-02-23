from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Ответ с JWT токеном."""
    access_token: str
    token_type: str


class MessageResponse(BaseModel):
    """Общий ответ с сообщением."""
    message: str