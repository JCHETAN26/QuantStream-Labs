# QuantStream Labs — Alpha Mirage demo image.
#
# Installs the packages in dependency order (contracts first) as a runtime artifact,
# then runs the demo, which prints the mirage verdict and writes the HTML report to
# a mountable /app/out directory.
FROM python:3.12-slim

WORKDIR /app

# contracts changes least often -> earliest layer for better build caching.
COPY packages/contracts ./packages/contracts
RUN pip install --no-cache-dir ./packages/contracts

COPY services/validation-engine ./services/validation-engine
COPY services/replay-engine ./services/replay-engine
COPY services/research-engine ./services/research-engine
COPY services/schema-worker ./services/schema-worker
COPY services/orderbook-lab ./services/orderbook-lab
COPY services/dataset_registry ./services/dataset_registry
RUN pip install --no-cache-dir \
    ./services/validation-engine \
    ./services/replay-engine \
    ./services/research-engine \
    ./services/schema-worker \
    ./services/orderbook-lab \
    ./services/dataset_registry

COPY apps/demo ./apps/demo
RUN pip install --no-cache-dir ./apps/demo

COPY apps/api ./apps/api
RUN pip install --no-cache-dir ./apps/api

# Pin the dataset location and pre-generate + verify it at build time, so the image
# ships a checksum-verified dataset and the demo runs fully offline.
ENV QUANTSTREAM_DATA_DIR=/app/data/demo
RUN quantstream-fetch-dataset --offline

RUN mkdir -p /app/out

# Default: run the demo once. The compose `api` service overrides this to serve HTTP.
CMD ["quantstream-demo", "--output", "/app/out/quantstream-report.html"]
