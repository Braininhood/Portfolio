# Multi-stage Dockerfile for full-stack deployment
# Stage 1: Build React Frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend
COPY server/frontend/package*.json ./
RUN npm ci && npm cache clean --force

COPY server/frontend/ ./
RUN npm run build

# Verify build was successful
RUN ls -la /frontend/build/

# Stage 2: Django Backend with Frontend
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=djangoproj.production_settings

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Django project
COPY server/ .

# Create frontend directories before copying
RUN mkdir -p frontend/build frontend/static

# Copy built React frontend from previous stage
COPY --from=frontend-builder /frontend/build/ ./frontend/build/

# Verify files were copied
RUN ls -la ./frontend/build/

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/djangoapp/get_dealers/ || exit 1

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "djangoproj.wsgi:application"] 