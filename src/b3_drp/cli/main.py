"""CLI entry point."""
import argparse
from ..core.assign import assign_plies, load_config


def main():
    parser = argparse.ArgumentParser(description="Assign composite plies to FEA mesh.")
    parser.add_argument("config", help="Configuration YAML file")
    parser.add_argument("grid", help="Input VTK grid file")
    parser.add_argument("matdb", help="Material database JSON file")
    parser.add_argument("output", help="Output VTK file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    config = load_config(args.config)
    assign_plies(config, args.grid, args.matdb, args.output)

if __name__ == "__main__":
    main()