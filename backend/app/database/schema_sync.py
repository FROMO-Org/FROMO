from sqlalchemy import text
from sqlalchemy.engine import Engine


def ensure_minimum_schema(engine: Engine) -> None:
    """Apply additive dev-safe schema updates required by the current app."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                ALTER TABLE events
                ADD COLUMN IF NOT EXISTS url TEXT
                """
            )
        )
