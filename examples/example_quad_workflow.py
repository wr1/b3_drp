"""Example quad workflow: Create a 20x20 mesh with y from 0-5, z=x**2, assign glass ply tapering in y."""

import numpy as np
import pyvista as pv
import logging
from b3_drp.core.assign import assign_plies, load_config
from b3_drp.core.plotting import plot_grid

logging.basicConfig(level=logging.INFO)

# Create a 20x20 mesh with y in [0,5], z = x**2
n = 51
x = np.linspace(0, 1, n)
y = np.linspace(0, 5, n)
X, Y = np.meshgrid(x, y)
Z = X**2
points = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])

# Create structured grid
mesh = pv.StructuredGrid()
mesh.points = points
mesh.dimensions = [n, n, 1]

# Compute cell centers for x, y, z
cell_centers = mesh.cell_centers()
mesh.cell_data["x"] = cell_centers.points[:, 0]
mesh.cell_data["y"] = cell_centers.points[:, 1]
mesh.cell_data["z"] = cell_centers.points[:, 2]

# Convert to unstructured grid for .vtu saving
mesh = mesh.cast_to_unstructured_grid()

# Save initial mesh
mesh.save("examples/quad_input.vtu")

# Load config and matdb
config = load_config("examples/config_quad.yaml")
result_grid = assign_plies(
    config, "examples/quad_input.vtu", "examples/matdb.json", "examples/quad_output.vtu"
)

# Plot
plot_grid(result_grid, scalar="total_thickness", output_file="examples/quad_plot.png")

logging.info(
    "Quad example completed. Check examples/quad_output.vtu and examples/quad_plot.png"
)
logging.info(
    "To run: b3_drp drape examples/config_quad.yaml examples/quad_input.vtu -m examples/matdb.json -o examples/quad_output.vtu"
)
logging.info(
    "Then: b3_drp plot examples/quad_output.vtu -o examples/quad_plot.png -s total_thickness"
)
