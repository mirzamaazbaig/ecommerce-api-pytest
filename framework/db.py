"""Direct SQL access, used for test setup (promoting an admin) and to verify what was persisted."""
import psycopg

from framework.config import DATABASE_URL


def available() -> bool:
    return bool(DATABASE_URL)


def sql(query: str, params=()):
    """Run a statement; returns rows for SELECT/RETURNING, otherwise an empty list."""
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        cur = conn.execute(query, params)
        return cur.fetchall() if cur.description else []
