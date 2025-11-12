"""Test example workflow."""

import tempfile
import os
import numpy as np
import pyvista as pv
import yaml
import json
from b3_drp.core.assign import assign_plies, load_config
from b3_drp.core.plotting import plot_grid


def test_example_workflow():
    """Test the workflow example."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a 20x20 square mesh in [0,1]
        x = np.linspace(0, 1, 21)
        y = np.linspace(0, 1, 21)
        X, Y = np.meshgrid(x, y)
        points = np.column_stack([X.ravel(), Y.ravel(), np.zeros_like(X.ravel())])

        # Create structured grid
        mesh = pv.StructuredGrid()
        mesh.points = points
        mesh.dimensions = [21, 21, 1]

        # Compute cell centers for x, y
        cell_centers = mesh.cell_centers()
        mesh.cell_data["x"] = cell_centers.points[:, 0]
        mesh.cell_data["y"] = cell_centers.points[:, 1]

        # Convert to unstructured grid for .vtu saving
        mesh = mesh.cast_to_unstructured_grid()

        grid_path = os.path.join(tmpdir, "input_mesh.vtu")
        mesh.save(grid_path)

        # Create config.yaml
        config_data = {
            "plies": [
                {
                    "mat": "carbon",
                    "angle": 0,
                    "thickness": 0.001,
                    "parent": "plate",
                    "conditions": [
                        {"field": "x", "operator": "in_range", "operand": [0, 1]},
                        {"field": "y", "operator": "in_range", "operand": [0, 1]},
                    ],
                    "key": 100,
                },
                {
                    "mat": "glass",
                    "angle": 45,
                    "thickness": 0.0005,
                    "parent": "plate",
                    "conditions": [
                        {"field": "x", "operator": "in_range", "operand": [0.4, 0.6]},
                        {"field": "y", "operator": "in_range", "operand": [0.4, 0.6]},
                    ],
                    "key": 101,
                },
            ],
        }
        config_path = os.path.join(tmpdir, "config.yaml")
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        # Create matdb.json
        matdb_path = os.path.join(tmpdir, "matdb.json")
        with open(matdb_path, "w") as f:
            json.dump({"carbon": {"id": 1}, "glass": {"id": 2}}, f)

        # Load config and assign
        config = load_config(config_path)
        output_path = os.path.join(tmpdir, "output_mesh.vtu")
        result_grid = assign_plies(config, grid_path, matdb_path, output_path)

        # Check results
        assert "total_thickness" in result_grid.cell_data
        assert result_grid.cell_data["total_thickness"].sum() > 0

        # Plot
        plot_path = os.path.join(tmpdir, "workflow_plot.png")
        plot_grid(result_grid, scalar="total_thickness", output_file=plot_path)

        assert os.path.exists(plot_path)
