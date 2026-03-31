# agi-cli — developer ergonomics (reference binary is ./agi)
.PHONY: help check fmt-sh

help:
	@echo "Targets:"
	@echo "  check   — shellcheck/bash -n on agi + install.sh (if tools present)"
	@echo "  fmt-sh  — normalize trailing newlines on shell scripts"

check:
	@bash -n agi && bash -n install.sh && bash -n scripts/verify_env.sh && bash -n scripts/hash_weights.sh && bash -n scripts/export_manifest.sh && echo "OK: bash syntax"

fmt-sh:
	@perl -pi -e 's/\r$$//' agi install.sh scripts/*.sh 2>/dev/null; echo "OK"
