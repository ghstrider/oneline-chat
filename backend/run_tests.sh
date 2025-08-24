#!/bin/bash

# Script to run all integration tests for Oneline Chat

set -e  # Exit on error

echo "========================================="
echo "Oneline Chat - Running Integration Tests"
echo "========================================="
echo ""

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not running on localhost:5432"
    echo "Please start PostgreSQL before running tests."
    exit 1
fi

echo "✅ PostgreSQL is running"
echo ""

# Check if test database exists, create if not
echo "Checking test database..."
if psql -h localhost -p 5432 -U "${DB_USER:-ankushsingh}" -lqt | cut -d \| -f 1 | grep -qw test_db; then
    echo "✅ Test database exists"
else
    echo "Creating test database..."
    createdb -h localhost -p 5432 -U "${DB_USER:-ankushsingh}" test_db
    echo "✅ Test database created"
fi
echo ""

# Set test environment variables
export APP_ENV=test
export LOG_LEVEL=WARNING
export TEST_DATABASE_URL="postgresql://${DB_USER:-ankushsingh}@localhost:5432/test_db"

# Run integration tests
echo "Running integration tests..."
echo "----------------------------"
python -m pytest tests/test_integration_local.py tests/test_chat_router.py \
    -v \
    --tb=short \
    --no-cov \
    -m integration \
    --color=yes

echo ""
echo "========================================="
echo "✅ All integration tests completed!"
echo "========================================="