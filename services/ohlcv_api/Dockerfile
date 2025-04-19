FROM python:3.11-slim

WORKDIR /app

COPY services/ohlcv_api/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "services.ohlcv_api.main:app", "--host", "0.0.0.0", "--port", "8010"]
