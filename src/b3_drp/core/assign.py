"""Assign plies to mesh elements based on conditions."""

import numpy as np
import pyvista as pv
import pandas as pd
import json
from typing import Dict, List, Any


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    import yaml

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_matdb(matdb_path: str) -> Dict[str, Any]:
    """Load material database from JSON."""
    with open(matdb_path, "r") as f:
        return json.load(f)


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
    df: pd.DataFrame, conditions: List[str], datums: Dict[str, Any]
) -> np.ndarray:
    """Evaluate conditions vectorized."""
    mask = np.ones(len(df), dtype=bool)
    for cond in conditions:
        # Parse simple conditions like 'r in range 10-20', 'distance_from_te > te_offset'
        # This is simplified; extend as needed
        if "in range" in cond:
            var, rng = cond.split(" in range ")
            min_v, max_v = map(float, rng.split("-"))
            mask &= (df[var] >= min_v) & (df[var] <= max_v)
        elif ">" in cond:
            left, right = cond.split(" > ")
            if right in datums:
                # Interpolate datum
                datum = datums[right]
                interp_vals = np.interp(
                    df[left.split("_")[0]], datum["values"][:, 0], datum["values"][:, 1]
                )
                mask &= df[left] > interp_vals
            else:
                mask &= df[left] > float(right)
        # Add more condition types as needed
    return mask


def assign_plies(
    config: Dict[str, Any],
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
    # Load data
    grid = pv.read(grid_path)
    matdb = load_matdb(matdb_path)
    datums = config.get("datums", {})
    plies = config.get("plies", [])

    # Check materials
    used_mats = {p["mat"] for p in plies}
    missing = used_mats - set(matdb.keys())
    if missing:
        raise ValueError(f"Missing materials: {missing}")

    # Prepare grid
    df = prepare_grid(grid, required_fields)

    # Sort plies by key, then by definition order
    plies_with_index = [(i, p) for i, p in enumerate(plies)]
    plies_with_index.sort(key=lambda x: (x[1]["key"], x[0]))
    plies = [p for _, p in plies_with_index]

    # Assign plies
    for ply in plies:
        mask = evaluate_conditions(df, ply["conditions"], datums)
        # Create arrays
        mat_id = matdb[ply["mat"]]["id"]  # Assume matdb has 'id'
        angle = ply["angle"]
        thickness = ply["thickness"]
        parent = ply["parent"]
        key = ply["key"]
        ply_num = f"{plies.index(ply) + 1:06d}"
        grid.cell_data[f"ply_{ply_num}_{parent}_{key}_material"] = np.where(
            mask, mat_id, -1
        )
        grid.cell_data[f"ply_{ply_num}_{parent}_{key}_angle"] = np.where(mask, angle, 0)
        grid.cell_data[f"ply_{ply_num}_{parent}_{key}_thickness"] = np.where(
            mask, thickness, 0
        )

    grid.save(output_path)
    return grid
