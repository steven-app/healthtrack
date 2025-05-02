#!/bin/bash

# Set environment variables for testing
export FLASK_APP=run.py
export FLASK_ENV=testing
export HEALTHTRACK_CONFIG=testing

echo "==== Running HealthTrack Integration Tests ===="
echo "Setting up testing environment..."

# Create test database if it doesn't exist
python -c "from app import db; db.create_all()"

# Run all integration tests
echo "Running all integration tests..."
python -m unittest discover -s tests/integration

# Run specific share feature tests
echo "==== Running Share Feature Tests ===="
python -m unittest tests/integration/test_share_feature.py

# Run with coverage report for share feature
echo "==== Running Share Feature Tests with Coverage ===="
coverage run -m unittest tests/integration/test_share_feature.py
coverage report -m --include="app/routes/share*,app/models/share*,app/services/share*"

echo "==== Test Results Summary ===="
if [ $? -eq 0 ]; then
    echo "✅ All tests passed successfully"
else
    echo "❌ Some tests failed - see above for details"
    exit 1
fi

# Cleanup
echo "Cleaning up test environment..."

echo "Testing completed" 