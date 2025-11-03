"""b3_drp: Assign composite plies to FEA elements."""

from .core.assign import assign_plies
from .core.drp_step import DrapeStep

__version__ = "0.1.0"
__all__ = ["assign_plies", "DrapeStep"]
