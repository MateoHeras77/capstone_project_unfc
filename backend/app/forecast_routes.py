"""DEPRECATED shim — see app/api/v1/endpoints/forecast.py"""
from app.api.v1.endpoints.forecast import router  # noqa: F401
__all__ = ["router"]
