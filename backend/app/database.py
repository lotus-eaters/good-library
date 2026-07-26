from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.is_development,  # logs every SQL query in dev
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,             # drops stale connections before use
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,         # keep model attributes accessible after commit
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass
