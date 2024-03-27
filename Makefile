# Makefile for managing common tasks in a Python project

# Variables
PYTHON=python3
PYTEST=pytest

# Run the client application
start-client:
	@echo "Starting client..."
	@$(PYTHON) client.py

# Run the unit test suite with pytest
test:
	@echo "Running unit tests..."
	@$(PYTEST)

# Define default make action
.PHONY: start-client test

