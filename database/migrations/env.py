from logging.config import fileConfig
import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - runtime dependency is present in the application environment
    load_dotenv = None

from alembic import context
from sqlalchemy import engine_from_config, pool

from backend.models.base import Base
from backend.models import (  # noqa: F401
    Commodity,
    Market,
    MarketPrice,
    DataSource,
    IngestionRun,
    DataQualityRun,
)


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

if load_dotenv:
    load_dotenv()

database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL must be set before running Alembic")
config.set_main_option("sqlalchemy.url", database_url)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
