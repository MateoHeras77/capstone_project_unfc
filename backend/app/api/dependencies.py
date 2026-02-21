"""
app/api/dependencies.py
───────────────────────
FastAPI dependency functions shared across all endpoints.

Usage
-----
    from app.api.dependencies import get_db

    @router.get("/foo")
    def my_route(db = Depends(get_db)):
        ...
"""

from supabase import Client

from core.database import get_supabase_client


def get_db() -> Client:
    """
    FastAPI dependency that returns the Supabase client singleton.

    Inject via ``Depends(get_db)`` in any route handler.

    Returns:
        Authenticated Supabase ``Client`` instance.
    """
    return get_supabase_client()
