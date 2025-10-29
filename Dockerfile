FROM public.ecr.aws/docker/library/python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements-minimal.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy project files
COPY backend/ .

# Run migrations and collect static files
RUN python manage.py migrate --noinput || echo "No migrations to run"
RUN python manage.py collectstatic --noinput || echo "No static files to collect"

# Create superuser
RUN echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123') if not User.objects.filter(username='admin').exists() else None" | python manage.py shell || echo "Superuser creation skipped"

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Use Gunicorn instead of runserver
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "finance_assist.wsgi:application"]
