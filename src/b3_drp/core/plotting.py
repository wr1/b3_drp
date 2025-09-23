"""Plotting utilities for ply assignment."""

import pyvista as pv
from typing import Optional


def plot_grid(
    grid: pv.UnstructuredGrid,
    scalar: Optional[str] = None,
    x_axis: str = "x",
    y_axis: str = "y",
) -> None:
    """Plot the grid with optional scalar coloring."""
    plotter = pv.Plotter()
    if scalar and scalar in grid.cell_data:
        plotter.add_mesh(grid, scalars=scalar)
    else:
        plotter.add_mesh(grid)
    plotter.view_xy()
    plotter.show_axes()
    plotter.show()  # Or return plotter for further customization
