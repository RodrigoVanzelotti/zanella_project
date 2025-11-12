FROM python:3.11-slim

WORKDIR /app

# Install UV
RUN pip install --no-cache-dir uv

# Copy project files (uv.lock and pyproject.toml for dependency resolution)
COPY pyproject.toml uv.lock README.md /app/
COPY app /app/app
COPY config /app/config

# Use UV to sync dependencies into project venv
RUN uv sync --frozen

ENV PYTHONUNBUFFERED=1

EXPOSE 8000
# Development image: run with auto-reload using UV-managed environment
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
