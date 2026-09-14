FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.lock .
RUN pip install --no-cache-dir --require-hashes -r requirements.lock

# Copy application code (.dockerignore keeps .env, .git and caches out)
COPY . .

# Don't buffer stdout/stderr so `docker logs` shows output immediately
ENV PYTHONUNBUFFERED=1

# Default run command. docker-compose overrides this to run DB migrations first.
CMD ["sh", "-c", "alembic upgrade head && python -m bot.main"]
