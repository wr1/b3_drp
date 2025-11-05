#!/bin/bash

# For tests/test_drp_step.py
git add tests/test_drp_step.py
ruff format tests/test_drp_step.py
ruff check --fix tests/test_drp_step.py > out.txt
uv run pytest -v >> out.txt
git commit tests/test_drp_step.py -m 'Add tests for DrapeStep class'

# For tests/test_plotting.py
git add tests/test_plotting.py
ruff format tests/test_plotting.py
ruff check --fix tests/test_plotting.py > out.txt
uv run pytest -v >> out.txt
git commit tests/test_plotting.py -m 'Add tests for plotting utilities'
