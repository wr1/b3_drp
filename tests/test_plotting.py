"""Test plotting utilities."""

import tempfile
import os
import numpy as np
import pyvista as pv
from b3_drp.core.plotting import plot_grid


def test_plot_grid():
    # Create a simple grid
    points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]])
    cells = np.array([4, 0, 1, 2, 3])
    grid = pv.UnstructuredGrid(cells, [pv.CellType.QUAD], points)
    grid.cell_data["x"] = np.array([0.5])
    grid.cell_data["y"] = np.array([0.5])
    grid.cell_data["total_thickness"] = np.array([0.001])

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "plot.png")

        # Test plotting with scalar
        plot_grid(grid, scalar="total_thickness", output_file=output_file)
        if not ("CI" in os.environ or "GITHUB_ACTIONS" in os.environ):
            assert os.path.exists(output_file)

        # Test plotting without scalar
        output_file2 = os.path.join(tmpdir, "plot2.png")
        plot_grid(grid, output_file=output_file2)
        if not ("CI" in os.environ or "GITHUB_ACTIONS" in os.environ):
            assert os.path.exists(output_file2)
