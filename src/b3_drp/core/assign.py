"""Assign plies to mesh elements based on conditions."""

import numpy as np
import pyvista as pv
import pandas as pd
import json
import logging
from typing import Dict, List, Any, Union
from collections import defaultdict
from .models import Config, MatDB, Condition

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Config:
    """Load and validate configuration from YAML file."""
    import yaml

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
    return Config(**data)


def load_matdb(matdb_path: str) -> MatDB:
    """Load and validate material database from JSON."""
    with open(matdb_path, "r") as f:
        data = json.load(f)
    return MatDB(data)


def prepare_grid(grid: pv.UnstructuredGrid, required_fields: List[str]) -> pd.DataFrame:
    """Prepare grid data, translating point to cell if needed."""
    df = pd.DataFrame()
    for field in required_fields:
        if field in grid.cell_data:
            df[field] = grid.cell_data[field]
        elif field in grid.point_data:
            # Translate point to cell
            grid = grid.point_data_to_cell_data(pass_point_data=True)
            df[field] = grid.cell_data[field]
        else:
            raise ValueError(f"Required field {field} not found in grid.")
    return df


def evaluate_conditions(
    df: pd.DataFrame, conditions: List[Condition], datums: Dict[str, Any]
) -> np.ndarray:
    """Evaluate conditions vectorized."""
    mask = np.ones(len(df), dtype=bool)
    for cond in conditions:
        field = cond.field
        operator = cond.operator
        operand = cond.operand
        if operator == "in_range":
            min_v, max_v = operand
            mask &= (df[field] >= min_v) & (df[field] <= max_v)
        elif operator == ">":
            if isinstance(operand, str):
                if operand in datums:
                    datum = datums[operand]
                    values = np.array(datum["values"])
                    interp_vals = np.interp(
                        df[field.split("_")[0]], values[:, 0], values[:, 1]
                    )
                    mask &= df[field] > interp_vals
                else:
                    raise ValueError(f"Datum {operand} not found")
            else:
                mask &= df[field] > operand
        # Add more operators as needed
    return mask


def get_thickness(
    thickness: Union[float, str],
    df: pd.DataFrame,
    datums: Dict[str, Any],
    base_field: str = "x",
) -> np.ndarray:
    """Get thickness array, either constant or interpolated from datum."""
    if isinstance(thickness, float):
        return np.full(len(df), thickness, dtype=np.float32)
    elif isinstance(thickness, str):
        if thickness in datums:
            datum = datums[thickness]
            values = np.array(datum["values"])
            return np.interp(df[base_field], values[:, 0], values[:, 1])
        else:
            raise ValueError(f"Datum {thickness} not found for thickness.")
    else:
        raise ValueError("Thickness must be float or string.")


def assign_plies(
    config: Config,
    grid_path: str,
    matdb_path: str,
    output_path: str,
    required_fields: List[str] = [
        "r",
        "distance_from_le",
        "distance_from_te",
        "distance_from_web0",
    ],
) -> pv.UnstructuredGrid:
    """Main function to assign plies."""
    logger.info(f"Loading grid from {grid_path}")
    grid = pv.read(grid_path)
    logger.info(f"Loading material database from {matdb_path}")
    matdb = load_matdb(matdb_path)
    datums = {k: v.dict() for k, v in config.datums.items()} if config.datums else {}
    plies = config.plies  # Keep as Pydantic objects

    # Check materials
    used_mats = {p.mat for p in plies}
    missing = used_mats - set(matdb.root.keys())
    if missing:
        raise ValueError(f"Missing materials: {missing}")
    logger.info(f"Used materials: {used_mats}")

    # Prepare grid
    df = prepare_grid(grid, required_fields)
    logger.info(f"Prepared grid with {len(df)} cells")

    # Sort plies by key, then by definition order
    plies_list = list(enumerate(plies))
    plies_list.sort(key=lambda x: (x[1].key, x[0]))
    plies = [p for _, p in plies_list]
    logger.info(f"Sorted {len(plies)} plies")

    # Initialize sums
    total_thickness = np.zeros(len(df), dtype=np.float32)
    n_plies = np.zeros(len(df), dtype=int)
    per_parent_thickness = defaultdict(lambda: np.zeros(len(df), dtype=np.float32))

    # Assign plies
    for ply in plies:
        logger.info(f"Processing ply {ply.key} with material {ply.mat}")
        mask = evaluate_conditions(df, ply.conditions, datums)
        thickness_arr = get_thickness(ply.thickness, df, datums)
        parent = ply.parent
        # Create arrays
        mat_id = matdb.root[ply.mat].id
        angle = ply.angle
        key = ply.key
        ply_num = f"{plies.index(ply) + 1:06d}"
        grid.cell_data[f"ply_{ply_num}_{parent}_{key}_material"] = np.where(
            mask, mat_id, -1
        )
        grid.cell_data[f"ply_{ply_num}_{parent}_{key}_angle"] = np.where(mask, angle, 0)
        grid.cell_data[f"ply_{ply_num}_{parent}_{key}_thickness"] = np.where(
            mask, thickness_arr, 0
        )

        # Update sums
        total_thickness += np.where(mask, thickness_arr, 0)
        n_plies += mask.astype(int)
        per_parent_thickness[parent] += np.where(mask, thickness_arr, 0)

    # Add summed arrays
    grid.cell_data["total_thickness"] = total_thickness
    grid.cell_data["n_plies"] = n_plies
    for parent, thick in per_parent_thickness.items():
        grid.cell_data[f"{parent}_thickness"] = thick

    logger.info(f"Saving output to {output_path}")
    grid.save(output_path)
    return grid
