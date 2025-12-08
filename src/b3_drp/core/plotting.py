"""Plotting utilities for ply assignment."""

import os
import pyvista as pv
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def plot_grid(
    grid,
    scalar: Optional[str] = None,
    x_axis: str = "x",
    y_axis: str = "y",
    output_file: str = "plot.png",
) -> None:
    """Plot the grid with scalar coloring and save screenshot."""
    plotter = pv.Plotter(off_screen=True)
    if scalar and scalar in grid.cell_data:
        plotter.add_mesh(grid, scalars=scalar)
    else:
        plotter.add_mesh(grid)
    plotter.view_xy()
    if "CI" in os.environ or "GITHUB_ACTIONS" in os.environ:
        logger.info(f"Skipping screenshot in CI environment")
    else:
        plotter.screenshot(output_file)
        logger.info(f"Plot saved to {output_file}")
