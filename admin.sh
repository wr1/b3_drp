#!/bin/bash

# pyproject.toml
ruff format pyproject.toml
ruff check --fix pyproject.toml > out.txt
uv run pytest -v >> out.txt
git add pyproject.toml
git commit -m 'Add treeparse dependency to pyproject.toml'

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

# admin.sh
ruff format admin.sh
ruff check --fix admin.sh > out.txt
uv run pytest -v >> out.txt
git add admin.sh
git commit -m 'Update admin.sh for modified files'