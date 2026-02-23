from sqlalchemy import Column, String
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True)
    hashed_password = Column(String, nullable=False)