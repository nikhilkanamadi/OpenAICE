FROM python:3.11-slim AS base

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.2

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-interaction --no-ansi

# Copy application code
COPY openaice/ ./openaice/
COPY policies/ ./policies/
COPY configs/ ./configs/
COPY examples/ ./examples/

EXPOSE 8000

ENTRYPOINT ["python", "-m", "openaice.cli.cli"]
CMD ["serve", "--config", "configs/sample-k8s.yaml"]
