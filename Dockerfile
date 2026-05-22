# Lightweight Python image for local/production-like API containers
FROM python:3.12-slim

# All application code and uvicorn run from /app (flat layout: main.py, database.py, ...)
WORKDIR /app

# Install dependencies first — Docker reuses this layer when only source code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy FastAPI application (app/ folder contents → /app)
COPY app/ .

EXPOSE 8000

# Flat imports use "from database import ...", so the app module is main:app (not app.main:app)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
