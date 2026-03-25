# Build context is stub-platform/ — allows COPY of both agents/media/ and shared/.
FROM python:3.11-slim

WORKDIR /app

COPY agents/media/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /app/shared/
COPY agents/__init__.py /app/agents/__init__.py
COPY agents/media/ /app/agents/media/

ENV PYTHONPATH=/app

EXPOSE 8002

CMD ["uvicorn", "agents.media.main:app", "--host", "0.0.0.0", "--port", "8002"]
