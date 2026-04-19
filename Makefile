.DEFAULT_GOAL := help

.PHONY: help \
	dev-aibaa dev-alphahunter dev-ecomonitor \
	test-aibaa test-alphahunter test-ecomonitor \
	lint-aibaa lint-alphahunter lint-ecomonitor

AIBAA_DIR := AI Investment Banking Analyst Agent (AIBAA)

help:
	@echo "ECo Times Suite root commands"
	@echo "  make dev-aibaa         - Delegate to AIBAA's existing Docker-based dev entrypoint"
	@echo "  make dev-alphahunter   - Delegate to AlphaHunter's existing dev entrypoint"
	@echo "  make dev-ecomonitor    - Delegate to EcoMonitor's existing dev server"
	@echo "  make test-aibaa        - Delegate to AIBAA's existing backend test command"
	@echo "  make test-alphahunter  - Delegate to AlphaHunter's existing test command"
	@echo "  make test-ecomonitor   - Delegate to EcoMonitor's existing data test command"
	@echo "  make lint-aibaa        - Delegate to AIBAA's existing lint command"
	@echo "  make lint-alphahunter  - Delegate to AlphaHunter's existing lint command"
	@echo "  make lint-ecomonitor   - Delegate to EcoMonitor's existing lint command"
	@echo ""
	@echo "These wrappers keep each product modular and defer to the canonical project-local workflows."

dev-aibaa:
	cd "$(AIBAA_DIR)" && $(MAKE) up

dev-alphahunter:
	cd alphahunter && $(MAKE) dev

dev-ecomonitor:
	cd ecomonitor && npm run dev

test-aibaa:
	cd "$(AIBAA_DIR)" && $(MAKE) test

test-alphahunter:
	cd alphahunter && $(MAKE) test

test-ecomonitor:
	cd ecomonitor && npm run test:data

lint-aibaa:
	cd "$(AIBAA_DIR)" && $(MAKE) lint

lint-alphahunter:
	cd alphahunter && $(MAKE) lint

lint-ecomonitor:
	cd ecomonitor && npm run lint
