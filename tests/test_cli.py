"""Test CLI commands."""

import tempfile
import os
import json
import yaml
from unittest.mock import patch, MagicMock
from b3_drp.cli.cli import drape_command, plot_command


def test_drape_command():
    # Create mock files
    config_data = {
        "plies": [
            {
                "mat": "carbon",
                "angle": 0,
                "thickness": 0.001,
                "parent": "plate",
                "conditions": [
                    {"field": "x", "operator": "in_range", "operand": [0, 1]},
                ],
                "key": 100,
            }
        ],
    }
    matdb_data = {"carbon": {"id": 1}}

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "config.yaml")
        grid_path = os.path.join(tmpdir, "grid.vtu")
        matdb_path = os.path.join(tmpdir, "matdb.json")
        output_path = os.path.join(tmpdir, "output.vtu")

        # Write config
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        # Write matdb
        with open(matdb_path, "w") as f:
            json.dump(matdb_data, f)

        # Create a simple grid
        import pyvista as pv
        import numpy as np
        points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]])
        cells = np.array([4, 0, 1, 2, 3])
        grid = pv.UnstructuredGrid(cells, [pv.CellType.QUAD], points)
        grid.cell_data["x"] = np.array([0.5])
        grid.save(grid_path)

        # Mock assign_plies
        with patch("b3_drp.cli.cli.assign_plies") as mock_assign:
            mock_assign.return_value = grid
            drape_command(config_path, grid_path, matdb_path, output_path, verbose=True)
            mock_assign.assert_called_once()


def test_plot_command():
    with tempfile.TemporaryDirectory() as tmpdir:
        grid_path = os.path.join(tmpdir, "grid.vtu")
        output_path = os.path.join(tmpdir, "plot.png")

        # Create a simple grid
        import pyvista as pv
        import numpy as np
        points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]])
        cells = np.array([4, 0, 1, 2, 3])
        grid = pv.UnstructuredGrid(cells, [pv.CellType.QUAD], points)
        grid.cell_data["x"] = np.array([0.5])
        grid.cell_data["total_thickness"] = np.array([0.001])
        grid.save(grid_path)

        # Mock plot_grid
        with patch("b3_drp.cli.cli.plot_grid") as mock_plot:
            plot_command(grid_path, output_path, scalar="total_thickness", verbose=True)
            mock_plot.assert_called_once_with(
                grid, scalar="total_thickness", x_axis="x", y_axis="y", output_file=output_path
            )
