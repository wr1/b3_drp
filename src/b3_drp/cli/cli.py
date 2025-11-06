"""CLI entry point using treeparse."""

import logging
from rich.logging import RichHandler
from treeparse import cli, command, argument, option
from ..core.assign import assign_plies, load_config
from ..core.plotting import plot_grid
import pyvista as pv
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(show_time=False)],
)


def grid_command(
    config: str,
    grid: str,
    matdb: str,
    output: str,
    verbose: bool = False,
) -> None:
    """Assign composite plies to FEA mesh."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    config_data = load_config(config)
    assign_plies(config_data, grid, matdb, output)


def blade_command(
    config: str,
    verbose: bool = False,
) -> None:
    """Assign plies based on blade config YAML."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    import yaml

    with open(config, "r") as f:
        blade_config = yaml.safe_load(f)
    config_dir = Path(config).parent
    workdir = blade_config.get("workdir", ".")
    workdir_path = config_dir / workdir
    grid_path = workdir_path / "b3_msh" / "lm2.vtu"
    if not grid_path.exists():
        raise FileNotFoundError(
            f"Input grid not found: {grid_path}. Ensure b3_msh step has run."
        )
    matdb = blade_config["matdb"]
    output_path = workdir_path / "b3_drp" / "draped.vtu"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    config_data = load_config(config)
    assign_plies(config_data, str(grid_path), matdb, str(output_path))


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


drape_group = cli(
    name="drape",
    help="Commands for draping plies onto meshes.",
)

grid_cmd = command(
    name="grid",
    help="Assign plies to a grid using separate config and matdb files.",
    callback=grid_command,
    arguments=[
        argument(name="config", arg_type=str, help="Config YAML file"),
        argument(name="grid", arg_type=str, help="Input VTK grid file"),
    ],
    options=[
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
drape_group.commands.append(grid_cmd)

blade_cmd = command(
    name="blade",
    help="Assign plies to a blade mesh using a single config YAML.",
    callback=blade_command,
    arguments=[
        argument(name="config", arg_type=str, help="Blade config YAML file"),
    ],
    options=[
        option(
            flags=["--verbose", "-v"],
            arg_type=bool,
            default=False,
            help="Verbose output",
        ),
    ],
)
drape_group.commands.append(blade_cmd)

app = cli(
    name="b3_drp",
    help="Assign composite material plies to FEA model elements.",
)

plot_cmd = command(
    name="plot",
    help="Plot the grid.",
    callback=plot_command,
    arguments=[
        argument(name="grid", arg_type=str, help="Input VTK grid file"),
    ],
    options=[
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
app.commands.append(drape_group)


def main():
    app.run()


if __name__ == "__main__":
    main()
