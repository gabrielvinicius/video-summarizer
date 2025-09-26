from sqlalchemy import create_engine, NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import AsyncGenerator, Generator

from src.shared.config.database_settings import DatabaseSettings

settings = DatabaseSettings()

# Sync Engine
engine_sync = create_engine(
    url=settings.database_url.replace('+asyncpg', ''),
    echo=True,
    pool_pre_ping=True,
    pool_timeout=30
)

# Async Engine
engine = create_async_engine(
    settings.database_url,
    echo=True,
    poolclass=NullPool,
)

# Session factories
SessionLocal = sessionmaker(bind=engine_sync)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base model
Base = declarative_base()


# Async DB session dependency (e.g. for FastAPI)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    print("Opening DB session")
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            print("Closing DB session")


# Sync DB session dependency (e.g. for CLI tools, tests)
def get_sync_db() -> Generator[Session, None, None]:
    print("Opening DB session")
    with SessionLocal() as session:
        try:
            yield session
        finally:
            print("Closing DB session")
