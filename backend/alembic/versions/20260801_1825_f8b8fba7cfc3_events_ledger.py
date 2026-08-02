"""events ledger

Creates the append-only event log, and enforces "append-only" in the database
rather than by convention.

The design principle for this project is that the author is the adversary: Diego
owns this code and has a financial incentive to find loopholes. A Python module
that merely *declines to offer* an UPDATE path is not a control — he can open a
SQL console. So the guarantee is installed where it is expensive to subvert:

- ``events_no_mutate`` raises on any UPDATE or DELETE, per row.
- A statement-level trigger also blocks TRUNCATE, which row triggers do not see.
- RLS is enabled with no policies, so the table is unreachable via Supabase's
  Data API with an anon key.

None of this makes tampering impossible — dropping a trigger is one statement.
It makes tampering a deliberate, visible act instead of a side effect, which is
exactly the bar the design principle sets.

Revision ID: f8b8fba7cfc3
Revises: 1c530a96c1dd
Create Date: 2026-08-01 18:25:49.463646

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f8b8fba7cfc3'
down_revision: Union[str, Sequence[str], None] = '1c530a96c1dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


_GUARD_FN = """
CREATE OR REPLACE FUNCTION public.events_no_mutate() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'events is append-only; % is not permitted', TG_OP;
END;
$$;
"""


def upgrade() -> None:
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('log_date', sa.Date(), nullable=False),
        # sa.Text() — autogenerate emitted a bare Text() here, which is not imported
        # in the generated namespace and raises NameError on apply.
        sa.Column(
            'payload',
            sa.JSON().with_variant(
                postgresql.JSONB(astext_type=sa.Text()), 'postgresql'
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('log_date', 'event_type', name='uq_event_day_type'),
    )
    # The streak fold scans by day; keep it index-ordered as the log grows.
    op.create_index('ix_events_log_date', 'events', ['log_date'])

    if _is_postgres():
        op.execute(_GUARD_FN)
        op.execute(
            "CREATE TRIGGER events_no_mutate "
            "BEFORE UPDATE OR DELETE ON public.events "
            "FOR EACH ROW EXECUTE FUNCTION public.events_no_mutate()"
        )
        # Row-level triggers never fire for TRUNCATE.
        op.execute(
            "CREATE TRIGGER events_no_truncate "
            "BEFORE TRUNCATE ON public.events "
            "FOR EACH STATEMENT EXECUTE FUNCTION public.events_no_mutate()"
        )
        op.execute("ALTER TABLE public.events ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    if _is_postgres():
        op.execute("DROP TRIGGER IF EXISTS events_no_truncate ON public.events")
        op.execute("DROP TRIGGER IF EXISTS events_no_mutate ON public.events")
        op.execute("DROP FUNCTION IF EXISTS public.events_no_mutate()")
    op.drop_index('ix_events_log_date', table_name='events')
    op.drop_table('events')
