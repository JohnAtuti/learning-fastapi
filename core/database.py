from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from typing import Generator
from core.config import settings


engine = create_engine(
    settings.database_url,
    echo=settings.DEBUG,
    pool_pre_ping= True,
    pool_size = 5,
    max_overflow=10,
    pool_recycle=3600,
    future=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit = False,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    
    try:
        yield db
    finally:
        db.close()