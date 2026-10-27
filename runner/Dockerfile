# check=skip=InvalidDefaultArgInFrom
# Build context: the repository root. The Python and uv versions are arguments
# with no default on purpose; they come from mise.toml (`mise current`) and
# runner/local.py and runner/worker/cloudflare.config.ts pass them.
# A default would be a second copy that drifts.
#   docker build -f runner/Dockerfile -t qg-runner \
#     --build-arg PYTHON_VERSION=$(mise current python) \
#     --build-arg UV_VERSION=$(mise current uv) .
ARG PYTHON_VERSION
ARG UV_VERSION

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM python:${PYTHON_VERSION}-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends tini \
 && rm -rf /var/lib/apt/lists/*

# The versions come from uv.lock, group `runner` of pyproject.toml. The file
# system is read-only at run time, so the bytecode is compiled here.
COPY pyproject.toml uv.lock /tmp/lock/
RUN --mount=from=uv,source=/uv,target=/usr/local/bin/uv \
    uv export --project /tmp/lock --frozen --no-emit-project --no-default-groups \
        --only-group runner -o /tmp/requirements.txt \
 && uv pip install --system --no-cache --compile-bytecode --require-hashes -r /tmp/requirements.txt \
 && rm -r /tmp/lock /tmp/requirements.txt

COPY runner/ /app/
COPY qgcheck/ /app/qgcheck/
COPY exercises/ /app/exercises/
RUN python -m compileall -q /app/qgcheck

# The learner can write nothing except their working directory in /scratch.
RUN mkdir /scratch && chmod 755 /scratch /tmp /var/tmp /app

WORKDIR /app
EXPOSE 8080
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "/app/server.py"]
