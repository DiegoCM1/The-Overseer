"""Alembic environment.

The database URL is NOT stored in alembic.ini. It is read from the same
pydantic-settings object the app uses, so there is exactly one source of truth
for the DSN and no chance of migrating a different database than the one the
app actually talks to.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from core.config import settings
from core.db import Base

# Importing the models is what populates Base.metadata. There are NO models right
# now, so Base.metadata is empty — which means `alembic revision --autogenerate`
# would cheerfully emit a migration that DROPS every existing table. Import each
# model here as soon as one exists, and do not autogenerate until then.

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inject the real DSN at runtime. '%' is escaped because ConfigParser would
# otherwise read a percent-encoded password (e.g. %40 for '@') as interpolation.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

target_metadata = Base.metadata


def include_object(object_, name, type_, reflected, compare_to):
    """Keep autogenerate scoped to the schema this project owns.

    Supabase ships managed schemas (auth, storage, realtime, ...) alongside the
    application schema. Without this filter, autogenerate can propose dropping
    objects this project did not create and must not touch.
    """
    if type_ == "table":
        schema = getattr(object_, "schema", None)
        if schema not in (None, "public"):
            return False
    return True


_common = dict(
    target_metadata=target_metadata,
    include_object=include_object,
    compare_type=True,            # catch column type drift
    compare_server_default=True,  # catch default drift
)


def run_migrations_offline() -> None:
    """Emit SQL to stdout without connecting — lets you review DDL before applying."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **_common,
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
        context.configure(connection=connection, **_common)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
