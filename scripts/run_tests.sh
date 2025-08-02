#!/bin/bash

source .venv/bin/activate
export PYTHONPATH=./src

pytest --cov=src --cov-report=term-missing --cov-fail-under=80 src/tests