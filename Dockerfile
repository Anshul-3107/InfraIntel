FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Libraries OpenCV needs at run time
RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU-only PyTorch first (much smaller than the default CUDA build)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY backend ./backend
COPY ml ./ml

# Collect static files (admin, REST framework) for WhiteNoise.
# The key here is a throwaway used only for this build step.
RUN DJANGO_SECRET_KEY=build-only python backend/manage.py collectstatic --noinput

# Run as a normal user, not root
RUN useradd --create-home appuser \
    && mkdir -p /app/backend/media \
    && chown -R appuser /app/backend/media
USER appuser

WORKDIR /app/backend
EXPOSE 8000
CMD ["gunicorn", "infraintel.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "180"]