"""CLI entry point using treeparse."""

import logging
from treeparse import cli, command, argument, option
from ..core.assign import assign_plies, load_config


def assign_command(
    config: str,
    grid: str,
    matdb: str,
    output: str,
    verbose: bool = False,
) -> None:
    """Assign composite plies to FEA mesh."""
    if verbose:
        logging.basicConfig(level=logging.INFO)
    config_data = load_config(config)
    assign_plies(config_data, grid, matdb, output)


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
    ],
)
app.commands.append(assign_cmd)


def main():
    app.run()


if __name__ == "__main__":
    main()
