import numpy as np
import pyvista as pv
import pandas as pd
import json
import logging
import re
from typing import Dict, List, Any, Union
from collections import defaultdict
from .models import Config, MatDB, Condition

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Config:
    """Load and validate configuration from YAML file."""
    import yaml

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
    if "laminates" in data:
        laminates = data.pop("laminates")
        data.update(laminates)
    if not isinstance(data, dict):
        raise ValueError(f"Config file {config_path} is not a valid YAML dictionary.")
    logger.info(f"Loaded config from {config_path}")
    return Config(**data)


def load_matdb(matdb_path: Union[str, dict]) -> MatDB:
    """Load and validate material database from JSON file or dict."""
    if isinstance(matdb_path, str):
        with open(matdb_path, "r") as f:
            data = json.load(f)
    else:
        data = matdb_path
    logger.info("Loaded material database")
    return MatDB(data)


def prepare_grid(grid: pv.UnstructuredGrid, required_fields: List[str]) -> pd.DataFrame:
    """Prepare grid data."""
    df = pd.DataFrame()
    for field in required_fields:
        if field in grid.cell_data:
            df[field] = grid.cell_data[field]
            logger.info(f"Using cell data for field {field}")
        else:
            raise ValueError(f"Required field {field} not found in grid.")
    return df


def evaluate_conditions(
    df: pd.DataFrame, conditions: List[Condition], datums: Dict[str, Any]
) -> np.ndarray:
    """Evaluate conditions vectorized."""
    logger.info(f"Evaluating {len(conditions)} conditions")
    mask = np.ones(len(df), dtype=bool)
    for cond in conditions:
        field = cond.field
        operator = cond.operator
        operand = cond.operand
        logger.debug(f"Evaluating condition: {field} {operator} {operand}")
        if operator == "in_range":
            min_v, max_v = operand
            mask &= (df[field] >= min_v) & (df[field] <= max_v)
        elif operator == ">":
            if isinstance(operand, str):
                if operand in datums:
                    datum = datums[operand]
                    values = np.array(datum["values"])
                    sort_idx = np.argsort(values[:, 0])
                    values = values[sort_idx]
                    interp_vals = np.interp(
                        df[datum["base"]], values[:, 0], values[:, 1]
                    )
                    mask &= df[field] > interp_vals
                    logger.debug(f"Interpolated datum {operand} for field {field}")
                else:
                    raise ValueError(f"Datum {operand} not found")
            else:
                mask &= df[field] > operand
        # Add more operators as needed
    logger.info(f"Conditions evaluation complete, {mask.sum()} cells match")
    return mask


def parse_thickness_expression(
    thickness_expr: str, datums: Dict[str, Any], df: pd.DataFrame
) -> np.ndarray:
    """Parse and evaluate thickness expression with datums."""
    # Find datum names in expression
    words = re.findall(r"\b\w+\b", thickness_expr)
    datum_names = [w for w in words if w in datums]
    # Interpolate each datum
    interp_datums = {}
    for name in datum_names:
        datum = datums[name]
        values = np.array(datum["values"])
        sort_idx = np.argsort(values[:, 0])
        values = values[sort_idx]
        interp_datums[name] = np.interp(df[datum["base"]], values[:, 0], values[:, 1])
    # Evaluate expression
    try:
        result = eval(thickness_expr, {"__builtins__": None}, interp_datums)
        return np.array(result, dtype=np.float32)
    except Exception as e:
        raise ValueError(
            f"Error evaluating thickness expression '{thickness_expr}': {e}"
        )


def get_thickness(
    thickness: Union[float, str],
    df: pd.DataFrame,
    datums: Dict[str, Any],
) -> np.ndarray:
    """Get thickness array, either constant, datum, or expression."""
    if isinstance(thickness, float):
        logger.debug(f"Using constant thickness {thickness}")
        return np.full(len(df), thickness, dtype=np.float32)
    elif isinstance(thickness, str):
        if thickness in datums:
            datum = datums[thickness]
            values = np.array(datum["values"])
            sort_idx = np.argsort(values[:, 0])
            values = values[sort_idx]
            logger.debug(f"Interpolating thickness from datum {thickness}")
            return np.interp(df[datum["base"]], values[:, 0], values[:, 1])
        else:
            logger.debug(f"Evaluating thickness expression {thickness}")
            return parse_thickness_expression(thickness, datums, df)
    else:
        raise ValueError("Thickness must be float or string.")


def get_datums_from_thickness(
    thickness: Union[float, str], datums: Dict[str, Any]
) -> List[str]:
    """Get list of datum names used in thickness."""
    if isinstance(thickness, str) and thickness not in datums:
        words = re.findall(r"\b\w+\b", thickness)
        return [w for w in words if w in datums]
    return []


def assign_plies(
    config: Config,
    grid_path: str,
    matdb_path: Union[str, dict],
    output_path: str,
) -> pv.UnstructuredGrid:
    """Main function to assign plies."""
    logger.info(f"Loading grid from {grid_path}")
    grid = pv.read(grid_path)
    # Pre-translate all point data to cell data
    grid = grid.point_data_to_cell_data(pass_point_data=True, progress_bar=False)
    logger.info("Translated all point data to cell data")
    logger.info("Loading material database")
    matdb = load_matdb(matdb_path)
    datums = (
        {k: v.model_dump() for k, v in config.datums.items()} if config.datums else {}
    )
    plies = config.plies  # Keep as Pydantic objects

    # Compute required fields from config
    required_fields = set()
    for ply in plies:
        for cond in ply.conditions:
            required_fields.add(cond.field)
            if isinstance(cond.operand, str) and cond.operand in datums:
                required_fields.add(datums[cond.operand]["base"])
        datum_names = get_datums_from_thickness(ply.thickness, datums)
        for name in datum_names:
            required_fields.add(datums[name]["base"])
    required_fields = list(required_fields)
    logger.info(f"Required fields: {required_fields}")

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
        logger.debug(f"Added ply data for {ply_num}")

        # Update sums
        total_thickness += np.where(mask, thickness_arr, 0)
        n_plies += mask.astype(int)
        per_parent_thickness[parent] += np.where(mask, thickness_arr, 0)

    # Add summed arrays
    grid.cell_data["total_thickness"] = total_thickness
    grid.cell_data["n_plies"] = n_plies
    for parent, thick in per_parent_thickness.items():
        grid.cell_data[f"{parent}_thickness"] = thick
    logger.info("Added summed thickness arrays")

    logger.info(f"Saving output to {output_path}")
    # Convert to PolyData for VTK
    poly = pv.PolyData()
    poly.points = grid.points
    poly.lines = grid.lines
    for key, value in grid.cell_data.items():
        poly.cell_data[key] = value
    for key, value in grid.point_data.items():
        poly.point_data[key] = value
    poly.save(output_path)
    return grid
