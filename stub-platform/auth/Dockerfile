# Build context is stub-platform/ — allows COPY of both auth/ and shared/ files.
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer-cache friendly)
COPY auth/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy auth service source (clients.py + main.py → /app/)
# "from clients import REGISTERED_CLIENTS" resolves because /app is the working dir.
COPY shared/ /app/shared/
COPY auth/ /app/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
