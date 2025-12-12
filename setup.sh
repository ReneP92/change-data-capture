#!/bin/bash

# Setup script for CDC Application

set -e

echo "🚀 Setting up Change Data Capture Application..."

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from defaults..."
    cat > .env << EOF
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=sourcedb.public.users

# Postgres Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=sourcedb

# Application Configuration
LOG_LEVEL=INFO
DATA_CONTRACT_SCHEMA_PATH=config/schemas/user_schema.json
EOF
    echo "✅ Created .env file"
else
    echo "ℹ️  .env file already exists, skipping..."
fi

# Create logs directory
mkdir -p logs
echo "✅ Created logs directory"

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 15

# Set up Debezium connector
echo "🔌 Setting up Debezium connector..."
max_retries=5
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    if curl -f -s http://localhost:8083/connectors > /dev/null 2>&1; then
        echo "✅ Kafka Connect is ready"
        break
    else
        retry_count=$((retry_count + 1))
        echo "⏳ Waiting for Kafka Connect... (attempt $retry_count/$max_retries)"
        sleep 5
    fi
done

if [ $retry_count -eq $max_retries ]; then
    echo "❌ Kafka Connect did not become ready. Please check logs: docker-compose logs kafka-connect"
    exit 1
fi

# Register Debezium connector
if curl -f -s -X POST http://localhost:8083/connectors \
    -H "Content-Type: application/json" \
    -d @debezium-config/debezium-postgres-connector.json > /dev/null 2>&1; then
    echo "✅ Debezium connector registered"
else
    echo "⚠️  Connector may already exist or there was an error. Checking status..."
    curl -s http://localhost:8083/connectors/debezium-postgres-connector/status | python3 -m json.tool 2>/dev/null || echo "Please check connector status manually"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📊 Access Kafka UI at: http://localhost:8080"
echo "🔌 Kafka Connect API at: http://localhost:8083"
echo ""
echo "📝 Next steps:"
echo "  1. Use the CLI to add test data: python -m app.cli add --random"
echo "  2. Monitor events in Kafka UI: http://localhost:8080"
echo "  3. Check consumer logs: make logs-consumer"
echo ""

