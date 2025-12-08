"""Test ply assignment."""

import numpy as np
import pyvista as pv
import pandas as pd
import tempfile
import os
import json
import pytest
from b3_drp.core.assign import (
    assign_plies,
    load_config,
    load_matdb,
    prepare_grid,
    evaluate_conditions,
    parse_thickness_expression,
    get_thickness,
    get_datums_from_thickness,
)
from b3_drp.core.models import Condition, Config, Ply


def test_load_config():
    config_yaml = """
plies:
  - mat: carbon
    angle: 0
    thickness: 0.001
    parent: plate
    conditions:
      - field: x
        operator: in_range
        operand: [0, 1]
    key: 100
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_yaml)
        f.flush()
        config = load_config(f.name)
    os.unlink(f.name)
    assert len(config.plies) == 1


def test_load_config_with_laminates():
    config_yaml = """
laminates:
  plies:
    - mat: carbon
      angle: 0
      thickness: 0.001
      parent: plate
      conditions:
        - field: x
          operator: in_range
          operand: [0, 1]
      key: 100
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_yaml)
        f.flush()
        config = load_config(f.name)
    os.unlink(f.name)
    assert len(config.plies) == 1


def test_load_matdb():
    matdb_json = '{"carbon": {"id": 1}}'
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(matdb_json)
        f.flush()
        matdb = load_matdb(f.name)
    os.unlink(f.name)
    assert matdb.root["carbon"].id == 1


def test_load_matdb_dict():
    matdb_dict = {"carbon": {"id": 1}}
    matdb = load_matdb(matdb_dict)
    assert matdb.root["carbon"].id == 1


def test_prepare_grid():
    points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]])
    cells = np.array([4, 0, 1, 2, 3])
    grid = pv.UnstructuredGrid(cells, [pv.CellType.QUAD], points)
    grid.cell_data["x"] = np.array([0.5])
    df = prepare_grid(grid, ["x"])
    assert "x" in df.columns
    assert df["x"].iloc[0] == 0.5


def test_prepare_grid_missing_field():
    points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]])
    cells = np.array([4, 0, 1, 2, 3])
    grid = pv.UnstructuredGrid(cells, [pv.CellType.QUAD], points)
    with pytest.raises(ValueError):
        prepare_grid(grid, ["missing"])


def test_evaluate_conditions():
    df = pd.DataFrame({"x": [0.0, 0.5, 1.0], "y": [0.0, 0.5, 1.0]})
    conditions = [
        Condition(field="x", operator="in_range", operand=[0, 1]),
        Condition(field="y", operator="in_range", operand=[0, 1]),
    ]
    datums = {}
    mask = evaluate_conditions(df, conditions, datums)
    assert np.all(mask)  # All true

    conditions = [Condition(field="x", operator="in_range", operand=[0.4, 0.6])]
    mask = evaluate_conditions(df, conditions, datums)
    expected = np.array([False, True, False])
    np.testing.assert_array_equal(mask, expected)


def test_evaluate_conditions_with_datum():
    df = pd.DataFrame({"x": [0.0, 0.5, 1.0], "y": [0.0, 0.5, 1.0]})
    conditions = [
        Condition(field="y", operator=">", operand="datum_y"),
    ]
    datums = {
        "datum_y": {
            "base": "x",
            "values": [[0, 0.2], [0.5, 0.3], [1, 0.4]],
        }
    }
    mask = evaluate_conditions(df, conditions, datums)
    expected = np.array(
        [False, True, True]
    )  # y > interp(x): 0>0.2?F, 0.5>0.3?T, 1>0.4?T
    np.testing.assert_array_equal(mask, expected)


def test_parse_thickness_expression():
    datums = {
        "t1": {
            "base": "x",
            "values": [[0, 0.001], [1, 0.002], [2, 0.003]],
        },
        "t2": {
            "base": "x",
            "values": [[0, 0.1], [1, 0.2], [2, 0.3]],
        },
    }
    df = pd.DataFrame({"x": [0, 1, 2]})
    result = parse_thickness_expression("t1 + t2", datums, df)
    expected = np.array([0.101, 0.202, 0.303])
    np.testing.assert_array_almost_equal(result, expected)


def test_parse_thickness_expression_error():
    datums = {}
    df = pd.DataFrame({"x": [0]})
    with pytest.raises(ValueError):
        parse_thickness_expression("invalid", datums, df)


def test_get_thickness():
    df = pd.DataFrame({"x": [0.0, 0.5, 1.0]})
    datums = {
        "thickness_taper": {
            "base": "x",
            "values": [[0, 0.001], [0.5, 0.002], [1, 0.001]],
        }
    }

    # Constant thickness
    thick = get_thickness(0.001, df, datums)
    expected = np.array([0.001, 0.001, 0.001])
    np.testing.assert_array_almost_equal(thick, expected)

    # Tapered thickness
    thick = get_thickness("thickness_taper", df, datums)
    expected = np.array([0.001, 0.002, 0.001])
    np.testing.assert_array_almost_equal(thick, expected)

    # Expression
    datums["t1"] = {"base": "x", "values": [[0, 0.1], [1, 0.2]]}
    thick = get_thickness("t1", df, datums)
    expected = np.array([0.1, 0.15, 0.2])
    np.testing.assert_array_almost_equal(thick, expected)


def test_get_thickness_invalid():
    df = pd.DataFrame({"x": [0.0]})
    with pytest.raises(ValueError):
        get_thickness([], df, {})


def test_get_datums_from_thickness():
    datums = {"t1": {}, "t2": {}}
    assert get_datums_from_thickness(0.001, datums) == []
    assert get_datums_from_thickness("t1", datums) == []
    assert get_datums_from_thickness("t1 + t2", datums) == ["t1", "t2"]


def test_assign_plies():
    # Create a simple unstructured grid
    points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]])
    cells = np.array([4, 0, 1, 2, 3])  # One quad cell
    grid = pv.UnstructuredGrid(cells, [pv.CellType.QUAD], points)
    grid.cell_data["x"] = np.array([0.5])
    grid.cell_data["y"] = np.array([0.5])

    config_dict = {
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
            }
        ]
    }
    config = Config(**config_dict)
    matdb = {"carbon": {"id": 1}}

    with tempfile.TemporaryDirectory() as tmpdir:
        grid_path = os.path.join(tmpdir, "grid.vtu")
        matdb_path = os.path.join(tmpdir, "matdb.json")
        output_path = os.path.join(tmpdir, "output.vtu")

        grid.save(grid_path)
        with open(matdb_path, "w") as f:
            json.dump(matdb, f)

        result_grid = assign_plies(config, grid_path, matdb_path, output_path)

        assert "ply_000001_plate_100_material" in result_grid.cell_data
        assert result_grid.cell_data["ply_000001_plate_100_material"][0] == 1
        assert "total_thickness" in result_grid.cell_data
        assert result_grid.cell_data["total_thickness"][0] == 0.001
        assert "n_plies" in result_grid.cell_data
        assert result_grid.cell_data["n_plies"][0] == 1
        assert "plate_thickness" in result_grid.cell_data
        assert result_grid.cell_data["plate_thickness"][0] == 0.001


def test_assign_plies_missing_material():
    points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]])
    cells = np.array([4, 0, 1, 2, 3])
    grid = pv.UnstructuredGrid(cells, [pv.CellType.QUAD], points)
    grid.cell_data["x"] = np.array([0.5])

    config = Config(
        plies=[
            Ply(
                mat="missing",
                angle=0,
                thickness=0.001,
                parent="plate",
                conditions=[],
                key=100,
            )
        ]
    )
    matdb = {"carbon": {"id": 1}}

    with tempfile.TemporaryDirectory() as tmpdir:
        grid_path = os.path.join(tmpdir, "grid.vtu")
        matdb_path = os.path.join(tmpdir, "matdb.json")
        output_path = os.path.join(tmpdir, "output.vtu")

        grid.save(grid_path)
        with open(matdb_path, "w") as f:
            json.dump(matdb, f)

        with pytest.raises(ValueError):
            assign_plies(config, grid_path, matdb_path, output_path)
