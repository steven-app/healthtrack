FROM python:3.10.12 AS builder

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# Install system dependencies required to build WeasyPrint
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libpq-dev \
    libxml2 \
    libxslt1.1 \
    libjpeg-dev \
    zlib1g-dev \
    libpango1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libharfbuzz0b \
    fontconfig \
    libgirepository-1.0-1 \
    libgtk-3-0 \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu \
    fonts-freefont-ttf \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN python -m venv .venv
COPY requirements.txt ./
RUN .venv/bin/pip install --upgrade pip && .venv/bin/pip install -r requirements.txt

FROM python:3.10.12-slim
WORKDIR /app

# Install runtime dependencies for WeasyPrint
RUN apt-get update && apt-get install -y \
    libpango1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libharfbuzz0b \
    fontconfig \
    libgirepository-1.0-1 \
    libgtk-3-0 \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu \
    fonts-freefont-ttf \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Add non-root user
RUN useradd -m appuser
RUN mkdir /instance && chown -R appuser:appuser /instance
USER appuser


COPY --from=builder /app/.venv .venv/
COPY . .

ENV PATH="/app/.venv/bin:$PATH"

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "-w", "4", "-t", "600", "run:app"]
