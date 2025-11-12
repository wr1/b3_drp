"""CLI entry point using treeparse."""

import logging
from rich.logging import RichHandler
from treeparse import cli, command, option
from ..core.assign import assign_plies, load_config
from ..core.plotting import plot_grid
import pyvista as pv

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(show_time=False)],
)


def drape_command(
    lamplan: str,
    grid: str,
    matdb: str,
    output: str,
    verbose: bool = False,
) -> None:
    """Assign composite plies to FEA mesh."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    config_data = load_config(lamplan)
    assign_plies(config_data, grid, matdb, output)


def plot_command(
    grid: str,
    output: str,
    scalar: str = "total_thickness",
    x_axis: str = "x",
    y_axis: str = "y",
    verbose: bool = False,
) -> None:
    """Plot the grid with scalar coloring."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    grid_obj = pv.read(grid)
    plot_grid(
        grid_obj,
        scalar=scalar,
        x_axis=x_axis,
        y_axis=y_axis,
        output_file=output,
    )


app = cli(
    name="b3_drp",
    help="Assign composite material plies to FEA model elements.",
)

drape_cmd = command(
    name="drape",
    help="Assign plies to a grid using laminate plan, grid, and matdb files.",
    callback=drape_command,
    options=[
        option(
            flags=["--lamplan", "-l"],
            arg_type=str,
            required=True,
            help="Laminate plan YAML file",
        ),
        option(
            flags=["--grid", "-g"],
            arg_type=str,
            required=True,
            help="Input VTK grid file",
        ),
        option(
            flags=["--matdb", "-m"],
            arg_type=str,
            required=True,
            help="Material database JSON file",
        ),
        option(
            flags=["--output", "-o"],
            arg_type=str,
            required=True,
            help="Output VTK file",
        ),
        option(
            flags=["--verbose", "-v"],
            arg_type=bool,
            default=False,
            help="Verbose output",
        ),
    ],
)
app.commands.append(drape_cmd)

plot_cmd = command(
    name="plot",
    help="Plot the grid.",
    callback=plot_command,
    options=[
        option(
            flags=["--grid", "-g"],
            arg_type=str,
            required=True,
            help="Input VTK grid file",
        ),
        option(
            flags=["--output", "-o"],
            arg_type=str,
            required=True,
            help="Output plot file",
        ),
        option(
            flags=["--scalar", "-s"],
            arg_type=str,
            default="total_thickness",
            help="Scalar field to plot (default: total_thickness)",
        ),
        option(
            flags=["--x-axis", "-x"],
            arg_type=str,
            default="x",
            help="X-axis field for plotting (default: x)",
        ),
        option(
            flags=["--y-axis", "-y"],
            arg_type=str,
            default="y",
            help="Y-axis field for plotting (default: y)",
        ),
        option(
            flags=["--verbose", "-v"],
            arg_type=bool,
            default=False,
            help="Verbose output",
        ),
    ],
)
app.commands.append(plot_cmd)


def main():
    app.run()


if __name__ == "__main__":
    main()
