from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.shared.config.database_settings import DatabaseSettings
from typing import AsyncGenerator

settings = DatabaseSettings()

# DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"

# Engine e session assíncronos
engine = create_async_engine(settings.database_url, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


# Dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
