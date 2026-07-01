.PHONY: test lint install

install:
	@for p in packages/* services/*; do \
	  if [ -f "$$p/pyproject.toml" ]; then pip install -e "$$p[dev]"; fi; \
	done

test:
	@for p in packages/* services/*; do \
	  if [ -f "$$p/pyproject.toml" ]; then echo "== $$p =="; ( cd "$$p" && pytest -q ); fi; \
	done

lint:
	@for p in packages/* services/*; do \
	  if [ -f "$$p/pyproject.toml" ]; then ruff check "$$p"; fi; \
	done
