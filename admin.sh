#!/bin/bash

# List of files
files=(
    "src/b3_drp/__init__.py"
    "src/b3_drp/cli/__init__.py"
    "src/b3_drp/cli/cli.py"
    "src/b3_drp/core/drp_step.py"
    "src/b3_drp/core/plotting.py"
    "src/b3_drp/core/assign.py"
    "src/b3_drp/core/__init__.py"
    "src/b3_drp/core/models.py"
    "examples/programmatic_example.py"
    "examples/example_quad_workflow.py"
    "examples/example_workflow.py"
    "examples/__init__.py"
    "tests/test_cli.py"
    "tests/test_drp_step.py"
    "tests/__init__.py"
    "tests/test_assign.py"
    "tests/test_plotting.py"
    "tests/test_programmatic_example.py"
    "tests/test_example_quad_workflow.py"
    "tests/test_example_workflow.py"
    "pyproject.toml"
)

ruff format
ruff check --fix > out.txt
uv run pytest -v >> out.txt

for file in "${files[@]}"; do
    if [ ! -f "$file" ]; then
        git add "$file"
    fi
    summary="Updated $file with refactoring and new features"
    git commit "$file" -m "$summary"
done
