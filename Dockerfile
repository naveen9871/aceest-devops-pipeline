# Stage 1: Build & Install dependencies
FROM python:3.12-slim AS builder
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

COPY . .

# Stage 2: Production Image
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Create a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy dependencies and application code from the builder stage
COPY --from=builder /root/.local /home/appuser/.local
COPY --from=builder /app /app

RUN chown -R appuser:appuser /app && chown -R appuser:appuser /home/appuser/.local

USER appuser
ENV PATH=/home/appuser/.local/bin:$PATH

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "debug", "app:app"]
