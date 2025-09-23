"""Helper functions for data processing."""

import numpy as np


def interpolate_datum(r_vals: np.ndarray, datum: Dict[str, Any]) -> np.ndarray:
    """Interpolate datum values."""
    base = datum['base']
    values = np.array(datum['values'])
    return np.interp(r_vals, values[:, 0], values[:, 1])