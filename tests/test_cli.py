import pytest
from unittest.mock import patch
from b3_drp.cli.cli import grid_command, blade_command, plot_command


def test_grid_command():
    """Test grid command."""
    with patch('b3_drp.core.assign.assign_plies') as mock_assign:
        mock_assign.return_value = None
        grid_command(
            config='dummy_config',
            grid='dummy_grid',
            matdb='dummy_matdb',
            output='dummy_output',
            verbose=False,
        )
        mock_assign.assert_called_once()


def test_blade_command():
    """Test blade command."""
    with patch('b3_drp.core.assign.assign_plies') as mock_assign:
        mock_assign.return_value = None
        blade_command(
            config='dummy_config',
            verbose=False,
        )
        mock_assign.assert_called_once()


def test_plot_command():
    """Test plot command."""
    with patch('b3_drp.core.plotting.plot_grid') as mock_plot:
        mock_plot.return_value = None
        plot_command(
            grid='dummy_grid',
            output='dummy_output',
            scalar='total_thickness',
            x_axis='x',
            y_axis='y',
            verbose=False,
        )
        mock_plot.assert_called_once_with(
            grid='dummy_grid',
            scalar='total_thickness',
            x_axis='x',
            y_axis='y',
            output_file='dummy_output',
        )
