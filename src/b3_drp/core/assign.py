"""Core assignment logic for plies."""

import numpy as np
import pyvista as pv
import pandas as pd
import json
import logging
import re
from typing import Dict, List, Any, Union
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial

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
    """Prepare grid data into DataFrame."""
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


def _process_ply(ply_data, df, datums, matdb):
    """Worker function for parallel ply processing."""
    idx, ply = ply_data
    key = ply.key
    parent = ply.parent
    mat_id = matdb.root[ply.mat].id
    angle = ply.angle
    ply_num = f"{idx + 1:06d}"

    # Evaluate condition mask (vectorized)
    mask = evaluate_conditions(df, ply.conditions, datums)

    # Compute thickness array
    thickness_arr = get_thickness(ply.thickness, df, datums)

    # Return only serializable NumPy arrays + metadata
    return {
        "ply_num": ply_num,
        "parent": parent,
        "key": key,
        "mask": mask.astype(np.bool_),
        "thickness": thickness_arr.astype(np.float32),
        "material_id": mat_id,
        "angle": float(angle),
    }


def assign_plies(
    config: Config,
    grid_path: str,
    matdb_path: Union[str, dict],
    output_path: str,
    max_workers: int = None,
) -> pv.UnstructuredGrid:
    """Assign composite plies to FEA mesh using parallel processing."""
    logger.info(f"Loading grid from {grid_path}")
    grid = pv.read(grid_path)
    grid = grid.point_data_to_cell_data(pass_point_data=True, progress_bar=False)

    matdb = load_matdb(matdb_path)
    datums = {k: v.model_dump() for k, v in (config.datums or {}).items()}
    plies = config.plies

    # Check materials
    used_mats = {p.mat for p in plies}
    missing = used_mats - set(matdb.root.keys())
    if missing:
        raise ValueError(f"Missing materials: {missing}")
    logger.info(f"Used materials: {used_mats}")

    # Precompute required fields
    required_fields = set()
    for ply in plies:
        for cond in ply.conditions:
            required_fields.add(cond.field)
            if isinstance(cond.operand, str) and cond.operand in datums:
                required_fields.add(datums[cond.operand]["base"])
        for name in get_datums_from_thickness(ply.thickness, datums):
            required_fields.add(datums[name]["base"])
    df = prepare_grid(grid, list(required_fields))
    logger.info(
        f"Prepared DataFrame with {len(df):,} cells and {len(df.columns)} fields"
    )

    # Sort plies for deterministic output
    plies_with_idx = sorted(enumerate(plies), key=lambda x: (x[1].key, x[0]))

    # Parallel processing of plies
    logger.info(
        f"Starting parallel evaluation of {len(plies_with_idx)} plies on {max_workers or 'auto'} workers"
    )

    worker = partial(_process_ply, df=df, datums=datums, matdb=matdb)

    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker, ply_item) for ply_item in plies_with_idx]

        for future in as_completed(futures):
            results.append(future.result())

    # Sort results back to original order
    results.sort(key=lambda r: r["ply_num"])

    # Serial assignment to grid
    logger.info("Gathering results and assigning to grid (serial)")

    total_thickness = np.zeros(len(df), dtype=np.float32)
    n_plies = np.zeros(len(df), dtype=np.int32)
    per_parent_thickness = defaultdict(lambda: np.zeros(len(df), dtype=np.float32))

    for res in results:
        mask = res["mask"]
        thick = res["thickness"]

        prefix = f"ply_{res['ply_num']}_{res['parent']}_{res['key']}"
        grid.cell_data[f"{prefix}_material"] = np.where(mask, res["material_id"], -1)
        grid.cell_data[f"{prefix}_angle"] = np.where(mask, res["angle"], 0.0)
        grid.cell_data[f"{prefix}_thickness"] = np.where(mask, thick, 0.0)

        total_thickness += np.where(mask, thick, 0)
        n_plies += mask.astype(np.int32)
        per_parent_thickness[res["parent"]] += np.where(mask, thick, 0)

    # Add summary arrays
    grid.cell_data["total_thickness"] = total_thickness
    grid.cell_data["n_plies"] = n_plies
    for parent, thick in per_parent_thickness.items():
        grid.cell_data[f"{parent}_thickness"] = thick

    logger.info(f"Saving result to {output_path}")
    grid.save(output_path)
    return grid
