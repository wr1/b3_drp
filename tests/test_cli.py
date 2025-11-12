from unittest.mock import patch
from b3_drp.cli.cli import drape_command, plot_command
import pyvista as pv
import numpy as np


def test_drape_command():
    """Test drape command."""
    with patch("b3_drp.cli.cli.load_config") as mock_load, patch(
        "b3_drp.cli.cli.assign_plies"
    ) as mock_assign:
        mock_load.return_value = None
        mock_assign.return_value = None
        drape_command(
            lamplan="dummy_lamplan",
            grid="dummy_grid",
            matdb="dummy_matdb",
            output="dummy_output",
            verbose=False,
        )
        mock_load.assert_called_once_with("dummy_lamplan")
        mock_assign.assert_called_once()


def test_plot_command():
    """Test plot command."""
    # Create a real grid for mocking
    points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]])
    cells = np.array([4, 0, 1, 2, 3])
    mock_grid = pv.UnstructuredGrid(cells, [pv.CellType.QUAD], points)
    mock_grid.cell_data["total_thickness"] = np.array([0.001])
    with patch("b3_drp.cli.cli.pv.read") as mock_read, patch(
        "b3_drp.cli.cli.plot_grid"
    ) as mock_plot:
        mock_read.return_value = mock_grid
        plot_command(
            grid="dummy_grid",
            output="dummy_output",
            scalar="total_thickness",
            x_axis="x",
            y_axis="y",
            verbose=False,
        )
        mock_plot.assert_called_once_with(
            mock_grid,
            scalar="total_thickness",
            x_axis="x",
            y_axis="y",
            output_file="dummy_output",
        )
