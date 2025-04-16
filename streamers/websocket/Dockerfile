FROM python:3.10-slim

WORKDIR /app

COPY streamers/websocket/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set PYTHONPATH
ENV PYTHONPATH=/app

CMD ["python", "streamers/websocket/websocket_data.py"]
