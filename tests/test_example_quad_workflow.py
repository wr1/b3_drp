"""Test example quad workflow."""

import tempfile
import os
import numpy as np
import pyvista as pv
import yaml
import json
from b3_drp.core.assign import assign_plies, load_config
from b3_drp.core.plotting import plot_grid


def test_example_quad_workflow():
    """Test the quad workflow example."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a 20x20 mesh with y in [0,5], z = x**2
        n = 51
        x = np.linspace(0, 1, n)
        y = np.linspace(0, 5, n)
        X, Y = np.meshgrid(x, y)
        Z = X**2
        points = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])

        # Create structured grid
        mesh = pv.StructuredGrid()
        mesh.points = points
        mesh.dimensions = [n, n, 1]

        # Compute cell centers for x, y, z
        cell_centers = mesh.cell_centers()
        mesh.cell_data["x"] = cell_centers.points[:, 0]
        mesh.cell_data["y"] = cell_centers.points[:, 1]
        mesh.cell_data["z"] = cell_centers.points[:, 2]

        # Convert to unstructured grid for .vtu saving
        mesh = mesh.cast_to_unstructured_grid()

        grid_path = os.path.join(tmpdir, "quad_input.vtu")
        mesh.save(grid_path)

        # Create config_quad.yaml
        config_data = {
            "plies": [
                {
                    "mat": "glass",
                    "angle": 0,
                    "thickness": "thickness_taper",
                    "parent": "plate",
                    "conditions": [
                        {"field": "x", "operator": "in_range", "operand": [0, 1]},
                        {"field": "y", "operator": "in_range", "operand": [0, 5]},
                    ],
                    "key": 100,
                }
            ],
            "datums": {
                "thickness_taper": {
                    "base": "y",
                    "values": [[0, 0.001], [2.5, 0.002], [5, 0.001]],
                }
            },
        }
        config_path = os.path.join(tmpdir, "config_quad.yaml")
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        # Create matdb.json
        matdb_path = os.path.join(tmpdir, "matdb.json")
        with open(matdb_path, "w") as f:
            json.dump({"glass": {"id": 1}}, f)

        # Load config and assign
        config = load_config(config_path)
        output_path = os.path.join(tmpdir, "quad_output.vtu")
        result_grid = assign_plies(config, grid_path, matdb_path, output_path)

        # Check results
        assert "total_thickness" in result_grid.cell_data
        assert result_grid.cell_data["total_thickness"].sum() > 0

        # Plot
        plot_path = os.path.join(tmpdir, "quad_plot.png")
        plot_grid(result_grid, scalar="total_thickness", output_file=plot_path)

        if not ("CI" in os.environ or "GITHUB_ACTIONS" in os.environ):
            assert os.path.exists(plot_path)
