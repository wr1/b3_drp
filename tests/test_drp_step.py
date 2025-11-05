"""Test DrapeStep class."""

import tempfile
import os
import json
import yaml
from unittest.mock import patch, MagicMock
from b3_drp.core.drp_step import DrapeStep
from b3_drp.core.models import Config


def test_drape_step():
    # Mock config
    config_data = {
        "workdir": "test_workdir",
        "matdb": {"carbon": {"id": 1}},
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
        grid_path = os.path.join(workdir, "b3_msh", "lm2.vtu")
        output_path = os.path.join(workdir, "b3_drp", "draped.vtu")
        matdb_path = os.path.join(tmpdir, "matdb.json")

        # Create directories
        os.makedirs(os.path.dirname(grid_path), exist_ok=True)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write config
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        # Write matdb
        with open(matdb_path, "w") as f:
            json.dump({"carbon": {"id": 1}}, f)

        # Create a simple grid
        import pyvista as pv
        import numpy as np
        points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]])
        cells = np.array([4, 0, 1, 2, 3])
        grid = pv.UnstructuredGrid(cells, [pv.CellType.QUAD], points)
        grid.cell_data["x"] = np.array([0.5])
        grid.save(grid_path)

        # Mock the step
        step = DrapeStep(config_path)
        step.config = config_data
        step.logger = MagicMock()

        # Run _execute
        step._execute()

        # Check output exists
        assert os.path.exists(output_path)
        step.logger.info.assert_called()
