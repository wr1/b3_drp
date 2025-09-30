"""Example workflow: Create a 20x20 square mesh, assign x and y, and drape plies narrowing from whole to [0.4-0.6]."""
import numpy as np
import pyvista as pv
import logging
from b3_drp.core.assign import assign_plies, load_config
from b3_drp.core.plotting import plot_grid

logging.basicConfig(level=logging.INFO)

# Create a 20x20 square mesh in [0,1]
x = np.linspace(0, 1, 21)
y = np.linspace(0, 1, 21)
X, Y = np.meshgrid(x, y)
points = np.column_stack([X.ravel(), Y.ravel(), np.zeros_like(X.ravel())])

# Create structured grid
mesh = pv.StructuredGrid()
mesh.points = points
mesh.dimensions = [21, 21, 1]

# Compute cell centers for x, y
cell_centers = mesh.cell_centers()
mesh.cell_data['x'] = cell_centers.points[:, 0]
mesh.cell_data['y'] = cell_centers.points[:, 1]

# Convert to unstructured grid for .vtu saving
mesh = mesh.cast_to_unstructured_grid()

# Save initial mesh
mesh.save('examples/input_mesh.vtu')

# Load config and matdb
config = load_config('examples/config.yaml')
result_grid = assign_plies(config, 'examples/input_mesh.vtu', 'examples/matdb.json', 'examples/output_mesh.vtu')

# Plot
plot_grid(result_grid, scalar="total_thickness", output_file="examples/workflow_plot.png")

logging.info("Example completed. Check examples/output_mesh.vtu and examples/workflow_plot.png")
logging.info("To run the same draping operation using b3_drp CLI: b3_drp assign examples/config.yaml examples/input_mesh.vtu examples/matdb.json examples/output_mesh.vtu --plot --plot-output examples/workflow_plot.png")