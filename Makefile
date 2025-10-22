.PHONY: help clean test install uninstall build lint format check-deps validate

# Variables
PYTHON := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python)
PIP := $(shell command -v pip3 2>/dev/null || command -v pip 2>/dev/null || echo pip)
EXTENSION_FILE := SSLTriage.py
CONFIG_FILE := ~/.ssltriage_config.json

help: ## Show this help message
	@echo "SSLTriage - Burp Suite Extension"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

clean: ## Clean temporary files and build artifacts
	@echo "Cleaning temporary files..."
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type d -name '__pycache__' -delete
	find . -type f -name 'sslt_*.json' -delete
	rm -rf build/ dist/ *.egg-info/
	@echo "Clean complete."

check-deps: ## Check if required dependencies are installed
	@echo "Checking dependencies..."
	@command -v sslyze >/dev/null 2>&1 || { echo "ERROR: sslyze not found. Please install it."; exit 1; }
	@echo "  ✓ sslyze found: $$(which sslyze)"
	@echo "Dependencies check passed."

validate: ## Validate the extension Python syntax
	@echo "Validating Python syntax..."
	@$(PYTHON) -m py_compile $(EXTENSION_FILE) && echo "  ✓ Syntax valid" || { echo "  ✗ Syntax error"; exit 1; }

lint: ## Run basic linting checks
	@echo "Running lint checks..."
	@grep -n "f'" $(EXTENSION_FILE) && { echo "ERROR: f-strings found (not compatible with Jython 2.7)"; exit 1; } || echo "  ✓ No f-strings"
	@grep -n "f\"" $(EXTENSION_FILE) && { echo "ERROR: f-strings found (not compatible with Jython 2.7)"; exit 1; } || echo "  ✓ No f-strings"
	@echo "Lint checks passed."

test: validate lint check-deps ## Run all tests
	@echo "All tests passed!"

install: check-deps ## Install SSLyze if not present
	@echo "Checking SSLyze installation..."
	@command -v sslyze >/dev/null 2>&1 || { \
		echo "Installing SSLyze..."; \
		if command -v brew >/dev/null 2>&1; then \
			brew install sslyze; \
		elif command -v apt-get >/dev/null 2>&1; then \
			sudo apt-get update && sudo apt-get install -y python3-pip && pip3 install sslyze; \
		elif command -v yum >/dev/null 2>&1; then \
			sudo yum install -y python3-pip && pip3 install sslyze; \
		elif command -v dnf >/dev/null 2>&1; then \
			sudo dnf install -y python3-pip && pip3 install sslyze; \
		elif command -v pacman >/dev/null 2>&1; then \
			sudo pacman -S --noconfirm python-pip && pip3 install sslyze; \
		else \
			pip install sslyze || pip3 install sslyze; \
		fi; \
	}
	@echo "Installation complete."

uninstall: ## Remove configuration files
	@echo "Removing SSLTriage configuration..."
	rm -f $(CONFIG_FILE)
	rm -f /tmp/sslt_*.json
	rm -f ~/tmp/sslt_*.json
	@echo "Uninstall complete."

build: clean validate lint ## Build distribution package
	@echo "Building distribution..."
	@mkdir -p dist
	@cp $(EXTENSION_FILE) dist/
	@cp README.md dist/
	@cp CHANGELOG.md dist/
	@echo "Build complete. Files in dist/"

package: build ## Create release package
	@echo "Creating release package..."
	@VERSION=$$(grep '^VERSION = ' $(EXTENSION_FILE) | cut -d'"' -f2); \
	tar -czf "dist/SSLTriage-v$${VERSION}.tar.gz" -C dist $(EXTENSION_FILE) README.md CHANGELOG.md
	@echo "Package created: dist/SSLTriage-v*.tar.gz"

version: ## Show current version
	@grep '^VERSION = ' $(EXTENSION_FILE) | cut -d'"' -f2

info: ## Show project information
	@echo "SSLTriage - Burp Suite Extension"
	@echo "Version: $$(make version)"
	@echo "Extension: $(EXTENSION_FILE)"
	@echo "Config: $(CONFIG_FILE)"
	@echo ""
	@echo "SSLyze: $$(which sslyze 2>/dev/null || echo 'not found')"

all: clean test build ## Clean, test, and build
	@echo "All tasks complete!"
