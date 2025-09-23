"""CLI entry point using treeparse."""
import logging
from treeparse import cli, command, argument, option
from ..core.assign import assign_plies, load_config
from ..core.plotting import plot_grid


def assign_command(
    config: str,
    grid: str,
    matdb: str,
    output: str,
    verbose: bool = False,
    plot: bool = False,
    scalar: str = "total_thickness",
    x_axis: str = "x",
    y_axis: str = "y",
    plot_output: str = "thickness_plot.png",
) -> None:
    """Assign composite plies to FEA mesh."""
    if verbose:
        logging.basicConfig(level=logging.INFO)
    config_data = load_config(config)
    result_grid = assign_plies(config_data, grid, matdb, output)
    if plot:
        plot_grid(result_grid, scalar=scalar, x_axis=x_axis, y_axis=y_axis, output_file=plot_output)


app = cli(
    name="b3_drp",
    help="Assign composite material plies to FEA model elements.",
)

assign_cmd = command(
    name="assign",
    help="Assign plies based on config.",
    callback=assign_command,
    arguments=[
        argument(name="config", arg_type=str, help="Configuration YAML file"),
        argument(name="grid", arg_type=str, help="Input VTK grid file"),
        argument(name="matdb", arg_type=str, help="Material database JSON file"),
        argument(name="output", arg_type=str, help="Output VTK file"),
    ],
    options=[
        option(
            flags=["--verbose", "-v"],
            arg_type=bool,
            default=False,
            help="Verbose output",
        ),
        option(
            flags=["--plot", "-p"],
            arg_type=bool,
            default=False,
            help="Plot the thickness distribution after assignment",
        ),
        option(
            flags=["--scalar", "-s"],
            arg_type=str,
            default="total_thickness",
            help="Scalar field to plot (default: total_thickness)",
        ),
        option(
            flags=["--x-axis"],
            arg_type=str,
            default="x",
            help="X-axis field for plotting (default: x)",
        ),
        option(
            flags=["--y-axis"],
            arg_type=str,
            default="y",
            help="Y-axis field for plotting (default: y)",
        ),
        option(
            flags=["--plot-output"],
            arg_type=str,
            default="thickness_plot.png",
            help="Output file for the plot (default: thickness_plot.png)",
        ),
    ],
)
app.commands.append(assign_cmd)


def main():
    app.run()


if __name__ == "__main__":
    main()