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
) -> None:
    """Assign composite plies to FEA mesh."""
    if verbose:
        logging.basicConfig(level=logging.INFO)
    config_data = load_config(config)
    result_grid = assign_plies(config_data, grid, matdb, output)
    if plot:
        plot_grid(result_grid, scalar=scalar)


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
    ],
)
app.commands.append(assign_cmd)


def main():
    app.run()


if __name__ == "__main__":
    main()
