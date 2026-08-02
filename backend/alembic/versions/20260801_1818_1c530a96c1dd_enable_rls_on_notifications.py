"""enable rls on notifications

Supabase exposes the `public` schema through its Data API. Without RLS, any
holder of the project's publishable/anon key could SELECT — or INSERT — rows in
`notifications` over plain HTTPS, with no database credentials at all.

That matters more here than in a normal app. `notifications` is the idempotency
ledger: a row means "this escalation step already fired." Anyone able to insert
rows into it can pre-emptively suppress messages, and anyone able to delete rows
can force duplicates. Under this project's design principle — the adversary is
the author — a REST-writable audit table is precisely the kind of cheat that
happens as a *side effect* rather than a deliberate act.

Enabling RLS with **zero policies** is a deny-all for the `anon` and
`authenticated` roles. The application is unaffected: it connects over the
session pooler as `postgres`, which carries the BYPASSRLS attribute.

Deliberately NOT using `FORCE ROW LEVEL SECURITY` — that would apply RLS to the
table owner too and lock out the application itself.

Revision ID: 1c530a96c1dd
Revises: 79ffbe8aa335
Create Date: 2026-08-01 18:18:47.771071

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '1c530a96c1dd'
down_revision: Union[str, Sequence[str], None] = '79ffbe8aa335'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgres() -> bool:
    # RLS is Postgres-only. The test suite round-trips migrations on sqlite,
    # which would choke on this DDL.
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if _is_postgres():
        op.execute("ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    if _is_postgres():
        op.execute("ALTER TABLE public.notifications DISABLE ROW LEVEL SECURITY")
