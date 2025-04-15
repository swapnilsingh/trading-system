FROM python:3.10-slim

WORKDIR /app

COPY requirements-jetson.txt .
RUN pip install --no-cache-dir -r requirements-jetson.txt

COPY . .

CMD ["uvicorn", "indicator_api.indicator_service:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "warning", "--no-access-log"]
