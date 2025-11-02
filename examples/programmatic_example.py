"""Programmatic example: Define everything in code, assign plies, and plot."""

import numpy as np
import pyvista as pv
import json
import logging
from b3_drp.core.assign import assign_plies
from b3_drp.core.models import Config, MatDB, Datum, Ply, Condition
from b3_drp.core.plotting import plot_grid

logging.basicConfig(level=logging.INFO)

# Define datums
te_offset = Datum(base="r", values=[[0, 0], [20, 0.1], [40, 0.2]])

# Define plies
ply1 = Ply(
    mat="carbon",
    angle=45,
    thickness=0.45e-3,
    parent="sparcap",
    conditions=[
        Condition(field="r", operator="in_range", operand=[10, 20]),
        Condition(field="distance_from_te", operator=">", operand=0.1),
        Condition(field="distance_from_le", operator=">", operand=1),
    ],
    key=100,
)
ply2 = Ply(
    mat="glass",
    angle=0,
    thickness=1.2e-3,
    parent="allover",
    conditions=[
        Condition(field="r", operator="in_range", operand=[15, 25]),
        Condition(field="distance_from_te", operator=">", operand="te_offset"),
        Condition(field="distance_from_le", operator=">", operand=0.5),
        Condition(field="distance_from_web0", operator="<", operand=0.6),
    ],
    key=102,
)

config = Config(datums={"te_offset": te_offset}, plies=[ply1, ply2])

# Define matdb
matdb = MatDB.model_validate({"carbon": {"id": 1}, "glass": {"id": 2}})

# Save matdb to file
with open("examples/prog_matdb.json", "w") as f:
    json.dump({"carbon": {"id": 1}, "glass": {"id": 2}}, f)

# Create a 10x10 square mesh in [0,1]
x = np.linspace(0, 1, 11)
y = np.linspace(0, 1, 11)
X, Y = np.meshgrid(x, y)
points = np.column_stack([X.ravel(), Y.ravel(), np.zeros_like(X.ravel())])

# Create structured grid
mesh = pv.StructuredGrid()
mesh.points = points
mesh.dimensions = [11, 11, 1]

# Compute cell centers for x, y
cell_centers = mesh.cell_centers()
mesh.cell_data["x"] = cell_centers.points[:, 0]
mesh.cell_data["y"] = cell_centers.points[:, 1]

# Convert to unstructured grid for .vtu saving
mesh = mesh.cast_to_unstructured_grid()

# Add required fields (mock, constant for simplicity)
n_cells = len(mesh.cell_data["x"])
mesh.cell_data["r"] = np.full(n_cells, 15.0)
mesh.cell_data["distance_from_le"] = np.full(n_cells, 2.0)
mesh.cell_data["distance_from_te"] = np.full(n_cells, 0.2)
mesh.cell_data["distance_from_web0"] = np.full(n_cells, 0.5)

mesh.save("examples/prog_input.vtu")

# Assign plies
result_grid = assign_plies(
    config,
    "examples/prog_input.vtu",
    "examples/prog_matdb.json",
    "examples/prog_output.vtu",
)

# Plot
plot_grid(result_grid, scalar="total_thickness", output_file="examples/prog_plot.png")

logging.info("Programmatic example completed.")
