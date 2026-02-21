"""
analytics/optimization
───────────────────────
Portfolio optimization and risk analytics sub-package.

Modules
-------
portfolio     — PyPortfolioOpt wrapper (align prices, optimize, frontier).
risk_metrics  — Pure NumPy/SciPy statistics (individual and cross-asset).
"""

from analytics.optimization import portfolio, risk_metrics

__all__ = ["portfolio", "risk_metrics"]
