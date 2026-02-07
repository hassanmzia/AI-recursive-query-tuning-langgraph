FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/media/uploads /app/static

EXPOSE 8042

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput 2>/dev/null; python manage.py initialize_vectorstore; exec gunicorn core.asgi:application -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8042 --workers 2 --timeout 300"]
