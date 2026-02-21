"""
data_engine/data_coordinator.py — DEPRECATED backward-compat shim.

The canonical implementation has moved to
``data_engine/coordinator.py``.
This file re-exports ``DataCoordinator`` so existing imports keep working.

New code should use::

    from data_engine.coordinator import DataCoordinator
"""

# Re-export from the new canonical location.
from data_engine.coordinator import DataCoordinator  # noqa: F401

__all__ = ["DataCoordinator"]
