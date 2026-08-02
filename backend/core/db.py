"""Engine + session factory.

Connection args are dialect-dependent on purpose:

- Postgres gets a hard ``connect_timeout`` so an unreachable host fails loudly in
  seconds. Without it libpq waits on the OS default, which is how a dead database
  turns into a scheduler tick that hangs forever instead of logging an error.
- ``pool_pre_ping`` discards connections that a pooler (Supabase's Supavisor) or a
  network blip killed while idle, instead of handing a dead socket to a caller.
- ``pool_recycle`` caps connection age so we never sit on one the pooler has
  already given up on.

sqlite is supported only because the test suite runs against it; libpq options
must not be passed to it.
"""

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker

from core.config import settings

_url = make_url(settings.DATABASE_URL)
_is_postgres = _url.get_backend_name() == "postgresql"

_connect_args: dict = {}
if _is_postgres:
    # libpq options. sqlite's DBAPI has no such keywords and would raise.
    _connect_args["connect_timeout"] = settings.DB_CONNECT_TIMEOUT

    # psycopg2 defaults to sslmode=prefer, which silently DOWNGRADES to plaintext
    # if the server does not offer TLS — so a stripped connection looks identical
    # to a healthy one. Require it instead, unless the DSN says otherwise on
    # purpose (e.g. sslmode=disable against a local dev database).
    if "sslmode" not in _url.query:
        _connect_args["sslmode"] = "require"

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
    pool_recycle=settings.DB_POOL_RECYCLE,
    echo=settings.SQL_ECHO,
)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


def safe_db_url() -> str:
    """The DSN with the password masked — safe to log or print."""
    return _url.render_as_string(hide_password=True)
