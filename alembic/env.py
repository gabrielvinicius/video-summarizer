import os
from logging.config import fileConfig
from dotenv import load_dotenv

from sqlalchemy import engine_from_config
from sqlalchemy import pool
import asyncio
from sqlalchemy.ext.asyncio import AsyncEngine
from src.shared.infrastructure.database import settings

from alembic import context
from src.shared.infrastructure.database import Base  # Importar a Base

# ---------- Importe todos os modelos aqui ----------
from src.auth.domain.user import User
from src.notifications.domain.notification import Notification
from src.summarization.domain.summary import Summary
from src.transcription.domain.transcription import Transcription
from src.video_management.domain.video import Video

# ---------------------------------------------------

load_dotenv(".env")

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Mantém a URL original com +asyncpg
config.set_main_option("sqlalchemy.url", settings.database_url)

# Define os metadados para o Alembic detectar as mudanças
target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
