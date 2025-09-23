"""Programmatic example: Define everything in code, assign plies, and plot."""

import numpy as np
import pyvista as pv
import json
from b3_drp.core.assign import assign_plies
from b3_drp.core.models import Config, MatDB, Datum, Ply, Condition
from b3_drp.core.plotting import plot_grid

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

# Create a simple grid (for demonstration, use the same as before)
points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]])
cells = np.array([4, 0, 1, 2, 3])
grid = pv.UnstructuredGrid(cells, [pv.CellType.QUAD], points)
# Add required fields (mock)
grid.cell_data["r"] = np.array([15])
grid.cell_data["distance_from_le"] = np.array([2])
grid.cell_data["distance_from_te"] = np.array([0.2])
grid.cell_data["distance_from_web0"] = np.array([0.5])

grid.save("examples/prog_input.vtu")

# Assign plies
result_grid = assign_plies(
    config,
    "examples/prog_input.vtu",
    "examples/prog_matdb.json",
    "examples/prog_output.vtu",
)

# Plot
plot_grid(result_grid, scalar="total_thickness")

print("Programmatic example completed.")
