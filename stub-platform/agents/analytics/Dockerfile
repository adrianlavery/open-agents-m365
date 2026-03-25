# Build context is stub-platform/ — allows COPY of both agents/analytics/ and shared/.
FROM python:3.11-slim

WORKDIR /app

COPY agents/analytics/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /app/shared/
COPY agents/__init__.py /app/agents/__init__.py
COPY agents/analytics/ /app/agents/analytics/

ENV PYTHONPATH=/app

EXPOSE 8003

CMD ["uvicorn", "agents.analytics.main:app", "--host", "0.0.0.0", "--port", "8003"]
