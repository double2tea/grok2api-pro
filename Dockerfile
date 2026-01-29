FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps kept minimal; most wheels are prebuilt.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# Create data directory
RUN mkdir -p /app/data /app/logs

# Set default environment variables
ENV API_KEY="" \
    PROXY_URL="" \
    PORT=8000 \
    X_STATSIG_ID="ZTpUeXBlRXJyb3I6IENhbm5vdCByZWFkIHByb3BlcnRpZXMgb2YgdW5kZWZpbmVkIChyZWFkaW5nICdjaGlsZE5vZGVzJyk="

EXPOSE 8000

# Direct start without entrypoint script
CMD ["python", "main.py"]
