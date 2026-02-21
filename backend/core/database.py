"""
core/database.py
────────────────
Supabase client factory with a module-level singleton.

The client is created once per process (using ``functools.lru_cache``)
and reused for every request.  All database interaction must go through
``get_supabase_client()`` — never call ``create_client`` elsewhere.

Usage (route handler)
---------------------
    # Prefer injecting via the FastAPI dependency in app/api/dependencies.py:
    from app.api.dependencies import get_db
    from fastapi import Depends

    @router.get("/")
    def my_route(db = Depends(get_db)):
        return db.table("assets").select("*").execute().data

Usage (non-FastAPI context, e.g. DataCoordinator)
--------------------------------------------------
    from core.database import get_supabase_client

    client = get_supabase_client()
"""

import logging
from functools import lru_cache

from supabase import Client, create_client

from core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Return the application-wide Supabase client singleton.

    The client is initialised lazily on first call and reused for all
    subsequent calls in the same process.

    Returns:
        Authenticated Supabase ``Client`` ready for table queries.

    Raises:
        ValueError: If ``SUPABASE_URL`` or ``SUPABASE_KEY`` are empty
                    (caught at startup by :class:`~core.config.Settings`).
    """
    settings = get_settings()
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    logger.info("Supabase client initialised (url=%s)", settings.SUPABASE_URL)
    return client
