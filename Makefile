.PHONY: test test-contracts lint

test: test-contracts

test-contracts:
	pytest packages/contracts -q

lint:
	ruff check packages/contracts
