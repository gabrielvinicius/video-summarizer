from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.shared.config.database_settings import DatabaseSettings
from typing import AsyncGenerator

settings = DatabaseSettings()

engine = create_async_engine(
    settings.database_url,
    echo=True,
    pool_pre_ping=True,              # verifica se a conexão está ativa antes de usar
    pool_recycle=1800,               # recicla conexões a cada 30 min
    pool_timeout=30,                 # espera até 30s por uma conexão
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    print("Abrindo sessão DB")
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            print("Fechando sessão DB")

