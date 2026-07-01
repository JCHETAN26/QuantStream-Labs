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
RUN pip install --no-cache-dir \
    ./services/validation-engine \
    ./services/replay-engine \
    ./services/research-engine

COPY apps/demo ./apps/demo
RUN pip install --no-cache-dir ./apps/demo

RUN mkdir -p /app/out

CMD ["quantstream-demo", "--output", "/app/out/quantstream-report.html"]
