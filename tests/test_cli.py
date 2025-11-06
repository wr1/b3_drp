import pytest
from unittest.mock import patch
from b3_drp.cli.cli import grid_command, blade_command, plot_command
import tempfile
import os
import yaml
import json
import pyvista as pv
import numpy as np


def test_grid_command():
    """Test grid command."""
    with patch('b3_drp.core.assign.assign_plies') as mock_assign:
        mock_assign.return_value = None
        grid_command(
            config='dummy_config',
            grid='dummy_grid',
            matdb='dummy_matdb',
            output='dummy_output',
            verbose=False,
        )
        mock_assign.assert_called_once()


def test_blade_command():
    """Test blade command."""
    config_data = {
        "workdir": "test_workdir",
        "matdb": "matdb.json",
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
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "config.yaml")
        workdir = os.path.join(tmpdir, "test_workdir")
        grid_path = os.path.join(workdir, "b3_msh", "lm2.vtp")
        matdb_path = os.path.join(tmpdir, "matdb.json")
        # Create dirs
        os.makedirs(os.path.dirname(grid_path), exist_ok=True)
        # Write config
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
        # Write matdb
        with open(matdb_path, "w") as f:
            json.dump({"carbon": {"id": 1}}, f)
        # Create grid
        points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]])
        cells = np.array([4, 0, 1, 2, 3])
        grid = pv.UnstructuredGrid(cells, [pv.CellType.QUAD], points)
        grid.cell_data["x"] = np.array([0.5])
        grid.save(grid_path)
        with patch('b3_drp.core.assign.assign_plies') as mock_assign:
            mock_assign.return_value = None
            blade_command(
                config=config_path,
                verbose=False,
            )
            mock_assign.assert_called_once()


def test_plot_command():
    """Test plot command."""
    with patch('b3_drp.cli.cli.pv.read') as mock_read, \
         patch('b3_drp.core.plotting.plot_grid') as mock_plot:
        mock_read.return_value = 'dummy_obj'
        plot_command(
            grid='dummy_grid',
            output='dummy_output',
            scalar='total_thickness',
            x_axis='x',
            y_axis='y',
            verbose=False,
        )
        mock_plot.assert_called_once_with(
            grid='dummy_obj',
            scalar='total_thickness',
            x_axis='x',
            y_axis='y',
            output_file='dummy_output',
        )
