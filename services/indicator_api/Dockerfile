FROM python:3.10-slim

WORKDIR /app

# Copy root-level project files
COPY services/indicator_api/requirements.txt .
COPY services/indicator_api/requirements-gpu.txt .

# Choose based on ARG
ARG GPU=false
RUN if [ "$GPU" = "true" ]; then \
      pip install --no-cache-dir -r requirements-gpu.txt; \
    else \
      pip install --no-cache-dir -r requirements.txt; \
    fi

# Copy entire project
COPY . .

# Set PYTHONPATH
ENV PYTHONPATH=/app

CMD ["uvicorn", "services.indicator_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
