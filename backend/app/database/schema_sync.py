from sqlalchemy import text
from sqlalchemy.engine import Engine


def ensure_minimum_schema(engine: Engine) -> None:
    """Apply additive dev-safe schema updates required by the current app."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_name = 'events'
                    ) THEN
                        ALTER TABLE public.events
                        ADD COLUMN IF NOT EXISTS url TEXT;
                    END IF;
                END $$;
                """
            )
        )
