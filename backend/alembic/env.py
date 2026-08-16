from logging.config import fileConfig
import os
import sys
import asyncio

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Add project root to Python path
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
)

# Same as backend/main.py: must run before backend.database's module-level os.environ[...] read
# below, since a bare `alembic` CLI invocation (unlike uvicorn) never goes through main.py.
load_dotenv()

from backend.database import Base, DATABASE_URL
from backend.models.scan import Scan  # noqa: F401


# Alembic Config object
config = context.config


# Configure logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Tell Alembic about our SQLAlchemy models
target_metadata = Base.metadata


# Reuse database.py's DATABASE_URL rather than re-reading the env var here — that's the one
# source of truth for it, and it already fails loudly (os.environ[...], no default) if unset.
# A second, independent os.getenv(...) with its own hardcoded fallback used to live here, which
# had drifted back to a weak default password after database.py's own fallback was removed.
config.set_main_option(
    "sqlalchemy.url",
    DATABASE_URL.replace("%", "%%")
)


# Run migrations in offline mode (emits SQL without a live DB connection).
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# Run migrations synchronously against an already-open connection.
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


# Run migrations in online mode using the async PostgreSQL engine.
async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())