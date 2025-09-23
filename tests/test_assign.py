"""Test ply assignment."""

import numpy as np
import pyvista as pv
import pandas as pd
import tempfile
import os
import json
from b3_drp.core.assign import (
    assign_plies,
    load_config,
    load_matdb,
    evaluate_conditions,
)


def test_load_config():
    config_yaml = """
plies:
  - mat: carbon
    angle: 0
    thickness: 0.001
    parent: plate
    conditions:
      - x in range 0-1
    key: 100
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_yaml)
        f.flush()
        config = load_config(f.name)
    os.unlink(f.name)
    assert "plies" in config
    assert len(config["plies"]) == 1


def test_load_matdb():
    matdb_json = '{"carbon": {"id": 1}}'
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(matdb_json)
        f.flush()
        matdb = load_matdb(f.name)
    os.unlink(f.name)
    assert matdb["carbon"]["id"] == 1


def test_evaluate_conditions():
    df = pd.DataFrame({"x": [0.0, 0.5, 1.0], "y": [0.0, 0.5, 1.0]})
    conditions = ["x in range 0-1", "y in range 0-1"]
    datums = {}
    mask = evaluate_conditions(df, conditions, datums)
    assert np.all(mask)  # All true

    conditions = ["x in range 0.4-0.6"]
    mask = evaluate_conditions(df, conditions, datums)
    expected = np.array([False, True, False])
    np.testing.assert_array_equal(mask, expected)


def test_assign_plies():
    # Create a simple unstructured grid
    points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]])
    cells = np.array([4, 0, 1, 2, 3])  # One quad cell
    grid = pv.UnstructuredGrid(cells, [pv.CellType.QUAD], points)
    grid.cell_data["x"] = np.array([0.5])
    grid.cell_data["y"] = np.array([0.5])

    config = {
        "plies": [
            {
                "mat": "carbon",
                "angle": 0,
                "thickness": 0.001,
                "parent": "plate",
                "conditions": ["x in range 0-1", "y in range 0-1"],
                "key": 100,
            }
        ]
    }
    matdb = {"carbon": {"id": 1}}

    with tempfile.TemporaryDirectory() as tmpdir:
        grid_path = os.path.join(tmpdir, "grid.vtu")
        matdb_path = os.path.join(tmpdir, "matdb.json")
        output_path = os.path.join(tmpdir, "output.vtu")

        grid.save(grid_path)
        with open(matdb_path, "w") as f:
            json.dump(matdb, f)

        result_grid = assign_plies(
            config, grid_path, matdb_path, output_path, required_fields=["x", "y"]
        )

        assert "ply_000001_plate_100_material" in result_grid.cell_data
        assert result_grid.cell_data["ply_000001_plate_100_material"][0] == 1
        assert "total_thickness" in result_grid.cell_data
        assert result_grid.cell_data["total_thickness"][0] == 0.001
        assert "n_plies" in result_grid.cell_data
        assert result_grid.cell_data["n_plies"][0] == 1
        assert "plate_thickness" in result_grid.cell_data
        assert result_grid.cell_data["plate_thickness"][0] == 0.001
