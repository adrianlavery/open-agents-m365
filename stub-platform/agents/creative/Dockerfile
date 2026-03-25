# Build context is stub-platform/ — allows COPY of both agents/creative/ and shared/.
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer-cache friendly)
COPY agents/creative/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared package — "from shared.auth_middleware import ..." resolves via PYTHONPATH=/app
COPY shared/ /app/shared/

# Copy agents package scaffolding + creative service
COPY agents/__init__.py /app/agents/__init__.py
COPY agents/creative/ /app/agents/creative/

# PYTHONPATH=/app makes both "shared.*" and "agents.creative.*" importable.
# Uvicorn is invoked in package mode so "from . import responses" resolves correctly.
ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["uvicorn", "agents.creative.main:app", "--host", "0.0.0.0", "--port", "8001"]
