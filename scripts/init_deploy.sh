#!/bin/bash
set -e

echo "Starting deployment initialization..."

# Create necessary directories
python -m app.init_db --ensure-dirs

# Initialize the database if it doesn't exist
if [ ! -f "/data/healthtrack.db" ]; then
    echo "Database file not found, initializing database..."
    python -m app.init_db --create-only
    echo "Database initialization complete."
else
    echo "Database file already exists, skipping initialization."
fi

echo "Deployment initialization complete." 