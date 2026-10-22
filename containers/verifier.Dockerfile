# syntax=docker/dockerfile:1
# Trusted verifier. Holds the private task specs and grades episode exports produced by the
# agent-facing server. Run with exports mounted read-only and no network:
#   docker run --rm --network none -v $PWD/exports:/exports:ro -v $PWD/results:/results \
#     invoiceops-verifier
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

WORKDIR /build
COPY pyproject.toml uv.lock ./
COPY src ./src
# An optional build secret "ca_bundle" supplies an extra CA certificate for networks that
# inspect TLS; it is used only during this step and is not stored in the image.
RUN --mount=type=secret,id=ca_bundle,required=false \
    if [ -f /run/secrets/ca_bundle ]; then \
      export PIP_CERT=/run/secrets/ca_bundle SSL_CERT_FILE=/run/secrets/ca_bundle; fi \
 && pip install "uv==0.11.32" \
 && uv export --frozen --no-dev --no-emit-project -o /tmp/requirements.txt \
 && pip install -r /tmp/requirements.txt && pip install --no-deps . && pip uninstall -y uv \
 && rm -rf /build

COPY tasks /srv/tasks
RUN useradd --create-home --uid 10002 verifier && mkdir -p /results && chown verifier /results
USER verifier
WORKDIR /home/verifier
ENTRYPOINT ["invoiceops", "--root", "/srv/tasks", "verify-exports", "--exports", "/exports", "--out", "/results"]
