# syntax=docker/dockerfile:1
# Agent-facing OpenEnv server. Contains public task files only: no private specs, no
# verifier, no task-family builders, no oracle. Build from the repository root:
#   docker build -f containers/env.Dockerfile -t invoiceops-env .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    INVOICEOPS_TASK_ROOT=/srv/tasks INVOICEOPS_EXPORT_DIR=/exports

WORKDIR /build
COPY pyproject.toml uv.lock ./
COPY src ./src
# Install exactly the locked versions (core + openenv extra, no dev tools).
# An optional build secret "ca_bundle" supplies an extra CA certificate for networks that
# inspect TLS; it is used only during this step and is not stored in the image.
RUN --mount=type=secret,id=ca_bundle,required=false \
    if [ -f /run/secrets/ca_bundle ]; then \
      export PIP_CERT=/run/secrets/ca_bundle SSL_CERT_FILE=/run/secrets/ca_bundle; fi \
 && pip install "uv==0.11.32" \
 && uv export --frozen --no-dev --extra openenv --no-emit-project -o /tmp/requirements.txt \
 && pip install -r /tmp/requirements.txt && pip install --no-deps . && pip uninstall -y uv \
 && SITE=$(python -c "import invoiceops, pathlib; print(pathlib.Path(invoiceops.__file__).parent)") \
 && rm -rf "$SITE/verification" "$SITE/families" "$SITE/agents" "$SITE/evaluation" \
           "$SITE/tasks/build.py" "$SITE/tasks/quality.py" "$SITE/cli.py" "$SITE/adapters/trl_env.py" \
 && rm -rf /build

COPY tasks /srv/tasks
RUN find /srv/tasks -name private.json -delete \
 && useradd --create-home --uid 10001 agentenv \
 && mkdir -p /exports && chown agentenv /exports

USER agentenv
WORKDIR /home/agentenv
EXPOSE 8000
CMD ["uvicorn", "invoiceops.adapters.openenv_app:app", "--host", "0.0.0.0", "--port", "8000"]
