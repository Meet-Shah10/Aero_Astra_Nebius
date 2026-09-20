# AERO-ASTRA — Backend (Python / FastAPI)
# Runs on CPU only; LLM calls go to Nebius Token Factory.

FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend ./backend

# Ensure project root is on sys.path so `from backend.xxx import ...` works
ENV PYTHONPATH=/app

EXPOSE 8000

# Run from project root so module imports resolve correctly
CMD ["python", "backend/api.py"]
