FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY services/ohlcv_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY . .

CMD ["uvicorn", "services.ohlcv_api.main:app", "--host", "0.0.0.0", "--port", "8010"]
