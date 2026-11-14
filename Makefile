.PHONY: all audit images clean

all: audit

# Run comprehensive CAD and binary STL audit
audit:
	@python3 cad/tools/verify_models.py

# Render assembly screenshots and perspectives for documentation
images:
	@python3 cad/tools/render_assembly.py

# Clean temporary files, backup files, and caches
clean:
	@rm -rf build/ *.tmp **/*.tmp **/*.FCBak **/__pycache__
	@echo "Cleaned build artifacts and temporary files."
