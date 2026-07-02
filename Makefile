.PHONY: test lint install demo-alpha-mirage docker-demo api fetch-hf-demo test-reproducibility regenerate-dataset

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

# Fetch + verify the official reproducibility dataset. Prefers a valid local cache,
# then Hugging Face (if the 'hf' extra + network are available), then offline
# regeneration. Always verifies SHA-256 and fails loudly on any mismatch.
fetch-hf-demo:
	quantstream-fetch-dataset

# Run the full backend flow on the verified dataset and print the Alpha Mirage
# verdict. Depends on the dataset being present (fetch-hf-demo ensures it).
demo-alpha-mirage: fetch-hf-demo
	quantstream-demo

# Assert the pipeline reproduces the locked expected_results.json exactly.
test-reproducibility: fetch-hf-demo
	cd services/dataset_registry && pytest -q tests/test_reproducibility.py

# Regenerate the committed dataset (use after an intentional pipeline change).
regenerate-dataset:
	quantstream-fetch-dataset --offline --force

docker-demo:
	docker compose up --build

api:
	quantstream-api
