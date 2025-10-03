#!/bin/bash

# Run ruff format
ruff format

# Run ruff check and pipe to out.txt
ruff check --fix > out.txt

# Run pytest and append to out.txt
uv run pytest -v >> out.txt

# Git add and commit for each modified file
git add src/b3_drp/core/assign.py
git commit -m 'Pre-translate all point data to cell data once, remove special w handling'

git add admin.sh
git commit -m 'Update admin.sh for pre-translation and removal of w special treatment'