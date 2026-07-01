.PHONY: test lint install demo-alpha-mirage docker-demo api

install:
	@for p in packages/* services/* apps/*; do \
	  if [ -f "$$p/pyproject.toml" ]; then pip install -e "$$p[dev]"; fi; \
	done

test:
	@for p in packages/* services/* apps/*; do \
	  if [ -f "$$p/pyproject.toml" ]; then echo "== $$p =="; ( cd "$$p" && pytest -q ); fi; \
	done

lint:
	@for p in packages/* services/* apps/*; do \
	  if [ -f "$$p/pyproject.toml" ]; then ruff check "$$p"; fi; \
	done

demo-alpha-mirage:
	quantstream-demo

docker-demo:
	docker compose up --build

api:
	quantstream-api
