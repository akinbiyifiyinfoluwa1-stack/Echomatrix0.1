"""PostgreSQL database configuration for EchoMatrix."""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./echomatrix_dev.db")

if DATABASE_URL.startswith(("postgres://", "postgresql://", "postgresql+psycopg://")) and "sslmode=" not in DATABASE_URL:
    DATABASE_URL = f"{DATABASE_URL}{'&' if '?' in DATABASE_URL else '?'}sslmode=require"

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
