from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import DeclarativeBase, Session

engine = create_engine("sqlite:///users.db")

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True)

    hashed_password = Column(String, nullable=False)


Base.metadata.create_all(engine)


def get_db():
    """Открывает сессию к базе и закрывает после использования."""
    with Session(engine) as session:
        yield session