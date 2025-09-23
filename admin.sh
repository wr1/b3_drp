#!/bin/bash

# pyproject.toml
ruff format pyproject.toml
ruff check --fix pyproject.toml > out.txt
uv run pytest -v >> out.txt
git add pyproject.toml
git commit -m 'Add treeparse and matplotlib dependencies to pyproject.toml'

# src/b3_drp/cli/main.py
ruff format src/b3_drp/cli/main.py
ruff check --fix src/b3_drp/cli/main.py > out.txt
uv run pytest -v >> out.txt
git add src/b3_drp/cli/main.py
git commit -m 'Refactor CLI to use treeparse and add optional plotting in src/b3_drp/cli/main.py'

# examples/programmatic_example.py
ruff format examples/programmatic_example.py
ruff check --fix examples/programmatic_example.py > out.txt
uv run pytest -v >> out.txt
git add examples/programmatic_example.py
git commit -m 'Fix MatDB instantiation and add matdb file save in examples/programmatic_example.py'

# src/b3_drp/core/assign.py
ruff format src/b3_drp/core/assign.py
ruff check --fix src/b3_drp/core/assign.py > out.txt
uv run pytest -v >> out.txt
git add src/b3_drp/core/assign.py
git commit -m 'Fix datum interpolation to use correct base field in src/b3_drp/core/assign.py'

# examples/programmatic_example.py
ruff format examples/programmatic_example.py
ruff check --fix examples/programmatic_example.py > out.txt
uv run pytest -v >> out.txt
git add examples/programmatic_example.py
git commit -m 'Add verbose logging to programmatic example'

# examples/example_workflow.py
ruff format examples/example_workflow.py
ruff check --fix examples/example_workflow.py > out.txt
uv run pytest -v >> out.txt
git add examples/example_workflow.py
git commit -m 'Add verbose logging to example workflow'

# src/b3_drp/core/assign.py
ruff format src/b3_drp/core/assign.py
ruff check --fix src/b3_drp/core/assign.py > out.txt
uv run pytest -v >> out.txt
git add src/b3_drp/core/assign.py
git commit -m 'Add verbose logger output for internal activities in src/b3_drp/core/assign.py'

# src/b3_drp/core/plotting.py
ruff format src/b3_drp/core/plotting.py
ruff check --fix src/b3_drp/core/plotting.py > out.txt
uv run pytest -v >> out.txt
git add src/b3_drp/core/plotting.py
git commit -m 'Change plotting to use matplotlib for thickness distribution in src/b3_drp/core/plotting.py'

# tests/test_assign.py
ruff format tests/test_assign.py
ruff check --fix tests/test_assign.py > out.txt
uv run pytest -v >> out.txt
git add tests/test_assign.py
git commit -m 'Fix test_get_thickness to include base in datum dict'

# admin.sh
ruff format admin.sh
ruff check --fix admin.sh > out.txt
uv run pytest -v >> out.txt
git add admin.sh
git commit -m 'Update admin.sh for modified files'