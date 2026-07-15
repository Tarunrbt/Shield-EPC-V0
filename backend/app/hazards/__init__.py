"""Tenant Hazard Library package.

Exposes the immutable hazard catalog and accessor functions used by
downstream agents (e.g. RiskAssessmentAgent). No hazard data should
ever be fabricated outside of this module — this is the single
source of truth for hazard definitions.
"""

from app.hazards.library import Hazard, get_hazard, get_hazards, HAZARD_CATALOG

__all__ = ["Hazard", "get_hazard", "get_hazards", "HAZARD_CATALOG"]
