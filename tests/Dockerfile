FROM python:3.11-slim

WORKDIR /app

# Install necessary dependencies including fastapi and yaml
RUN apt-get update && apt-get install -y curl && \
    pip install --no-cache-dir pytest requests httpx redis pandas fastapi pyyaml websockets ta

# Copy the test files
COPY ./tests /app/tests

# Run unit tests
CMD ["pytest", "tests/"]
