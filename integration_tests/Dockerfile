FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install curl (for service readiness checks) and other required testing dependencies
RUN apt-get update && apt-get install -y curl && \
    pip install --no-cache-dir pytest requests httpx redis pandas fastapi ta pyyaml websockets

# Copy the current directory content into the container's working directory
COPY . .

# Set PYTHONPATH environment variable to point to the /app directory
ENV PYTHONPATH=/app

# Run tests located in integration_tests directory
CMD ["pytest", "integration_tests/"]
