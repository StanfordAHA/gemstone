#!/bin/bash

# force color
export PYTEST_ADDOPTS="--color=yes"

cd /gemstone/

pytest --codestyle gemstone \
       --cov gemstone       \
       -v --cov-report term-missing tests
