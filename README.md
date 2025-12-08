# b3_drp

A library for assigning composite material plies to FEA model elements.

## Description

b3_drp processes finite element analysis (FEA) meshes by assigning composite plies based on laminate plans, material databases, and geometric conditions. It supports parallel processing for efficient computation on large meshes, vectorized operations using NumPy, and validation with Pydantic.

Key features:
- Load laminate configurations from YAML files
- Assign plies to mesh elements based on conditions (e.g., position ranges, datums)
- Support for constant, datum-based, or expression-based thicknesses
- Parallel ply evaluation for performance
- Output VTK files with ply data for visualization
- CLI and programmatic interfaces

## Installation

Install using uv (recommended):

```bash
uv pip install b3_drp
```

Or with pip:

```bash
pip install b3_drp
```

For development, clone the repository and install dependencies:

```bash
uv sync --dev
```

## Usage

### Command Line Interface

The CLI provides two main commands: `drape` and `plot`.

#### Drape Command

Assign plies to a mesh:

```bash
b3_drp drape --lamplan config.yaml --grid input.vtu --matdb materials.json --output output.vtk --verbose
```

Options:
- `--lamplan`, `-l`: Laminate plan YAML file
- `--grid`, `-g`: Input VTK grid file
- `--matdb`, `-m`: Material database JSON file
- `--output`, `-o`: Output VTK file
- `--verbose`, `-v`: Enable verbose logging

#### Plot Command

Plot the grid with scalar coloring:

```bash
b3_drp plot --grid output.vtk --output plot.png --scalar total_thickness --x-axis x --y-axis y --verbose
```

Options:
- `--grid`, `-g`: Input VTK grid file
- `--output`, `-o`: Output plot file (PNG)
- `--scalar`, `-s`: Scalar field to plot (default: total_thickness)
- `--x-axis`, `-x`: X-axis field (default: x)
- `--y-axis`, `-y`: Y-axis field (default: y)
- `--verbose`, `-v`: Enable verbose logging

### Programmatic Usage

```python
import b3_drp
from b3_drp.core.assign import assign_plies, load_config

# Load configuration
config = load_config('config.yaml')

# Assign plies
grid = assign_plies(config, 'input.vtu', 'materials.json', 'output.vtk')

# Plot
b3_drp.plot_grid(grid, scalar='total_thickness', output_file='plot.png')
```

### Configuration Files

#### Laminate Plan (YAML)

Example `config.yaml`:

```yaml
datums:
  thickness_datum:
    base: x
    values:
      - [0.0, 0.001]
      - [1.0, 0.002]

plies:
  - mat: carbon
    angle: 0
    thickness: thickness_datum
    parent: plate
    conditions:
      - field: x
        operator: in_range
        operand: [0.0, 1.0]
    key: 1
```

#### Material Database (JSON)

Example `materials.json`:

```json
{
  "carbon": {
    "id": 1
  }
}
```

## Examples

See the `examples/` directory for sample workflows and data.

Run an example:

```bash
uv run python examples/example_workflow.py
```
