# Makefile for managing common tasks in a Python project

# Variables
PYTHON=python3
PYTEST=pytest tests/

# Run the client application with prompts for configuration
start-client:
	@read -p "Enter IRC server host: " host; \
	read -p "Enter IRC server port: " port; \
	read -p "Enter user info: " userinfo; \
	read -p "Enter nickname: " nickname; \
	read -p "Enter default channel (e.g., #general): " default_channel; \
	echo "Starting client..."; \
	$(PYTHON) irc_app.py --host $$host --port $$port --userinfo "$$userinfo" --nickname $$nickname --default-channel $$default_channel

# Run the unit test suite with pytest
test:
	@echo "Running unit tests..."
	@$(PYTEST)

# Define default make action
.PHONY: start-client test
