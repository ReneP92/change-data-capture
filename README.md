# Change Data Capture (CDC) Application

A production-ready Python application that uses Debezium for Change Data Capture on a PostgreSQL source database. The application implements data contracts for schema validation and provides a CLI tool for managing test data.

## Architecture

- **Source Database**: PostgreSQL with logical replication enabled
- **CDC Engine**: Debezium (via Kafka Connect)
- **Message Broker**: Apache Kafka
- **Monitoring UI**: Kafka UI (accessible at http://localhost:8080)
- **Consumer**: Python application that processes CDC events with data contract validation

## Features

- ✅ Real-time change data capture from PostgreSQL
- ✅ Data contract validation using JSON Schema
- ✅ Structured logging with JSON output
- ✅ Production-ready error handling and graceful shutdown
- ✅ Dockerized deployment
- ✅ CLI tool for managing test data
- ✅ Easy monitoring through Kafka UI

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local CLI usage)
- Make (optional, for convenience commands)

## Quick Start

### 1. Start the Infrastructure

```bash
make up
```

This will start:
- PostgreSQL (port 5432)
- Zookeeper (port 2181)
- Kafka (port 9092)
- Kafka Connect with Debezium (port 8083)
- Kafka UI (port 8080)
- CDC Consumer application

### 2. Access the Monitoring UI

Open your browser and navigate to:
- **Kafka UI**: http://localhost:8080
  - View Kafka topics, messages, and consumer groups
  - Monitor Debezium connector status
  - Inspect CDC events in real-time

### 3. Use the CLI to Add Test Data

```bash
# Add a single user with random data
python -m app.cli add --random

# Add a specific user
python -m app.cli add --email "john@example.com" --name "John Doe" --age 30

# Generate multiple random users
python -m app.cli generate --count 5

# List users
python -m app.cli list

# Update a user
python -m app.cli update --id 1 --name "Jane Doe" --status "inactive"

# Delete a user
python -m app.cli delete --id 1
```

### 4. Monitor CDC Events

- Check Kafka UI at http://localhost:8080
- View the `sourcedb.public.users` topic
- Check consumer logs: `make logs-consumer`

## Project Structure

```
change-data-capture/
├── app/
│   ├── __init__.py
│   ├── main.py              # Main entry point
│   ├── consumer.py          # Kafka consumer for CDC events
│   ├── contracts.py         # Data contract validation
│   ├── config.py            # Configuration management
│   ├── logger.py            # Structured logging setup
│   └── cli.py               # CLI tool for test data
├── config/
│   └── schemas/
│       └── user_schema.json  # Data contract schema
├── init-scripts/
│   └── 01-init.sql          # Database initialization
├── debezium-config/
│   └── debezium-postgres-connector.json  # Debezium connector config
├── docker-compose.yml       # Docker services configuration
├── Dockerfile               # Consumer application Docker image
├── requirements.txt         # Python dependencies
├── Makefile                # Convenience commands
└── README.md               # This file
```

## Data Contracts

The application implements data contracts using JSON Schema. The schema for user data is defined in `config/schemas/user_schema.json`. All CDC events are validated against this schema before processing.

### Schema Features

- Type validation
- Required field enforcement
- Enum validation for status field
- Email format validation
- Range validation for age
- Timestamp format validation

## Configuration

Configuration is managed through environment variables. Copy `.env.example` to `.env` and adjust as needed:

```bash
cp .env.example .env
```

Key configuration options:
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker addresses
- `KAFKA_TOPIC`: Topic to consume from
- `POSTGRES_*`: PostgreSQL connection details
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `DATA_CONTRACT_SCHEMA_PATH`: Path to schema file

## Make Commands

```bash
make up              # Start all services
make down            # Stop all services
make restart         # Restart all services
make logs            # View all logs
make logs-consumer   # View consumer logs only
make setup-connector # Set up Debezium connector
make status          # Check service status
make clean           # Remove all containers and volumes
make test-cli        # Run CLI test commands
```

## Manual Operations

### Set up Debezium Connector Manually

```bash
curl -i -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d @debezium-config/debezium-postgres-connector.json
```

### Check Connector Status

```bash
curl http://localhost:8083/connectors/debezium-postgres-connector/status | python -m json.tool
```

### List Kafka Topics

```bash
docker exec cdc-kafka kafka-topics --bootstrap-server localhost:9092 --list
```

### View Messages in a Topic

```bash
docker exec cdc-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic sourcedb.public.users \
  --from-beginning
```

## Development

### Running Locally (without Docker)

1. Ensure PostgreSQL, Kafka, and Kafka Connect are running
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.env`
4. Run the consumer:
   ```bash
   python -m app.main
   ```

### Adding New Tables

1. Add the table to PostgreSQL
2. Update `debezium-config/debezium-postgres-connector.json`:
   ```json
   "table.include.list": "public.users,public.new_table"
   ```
3. Create a data contract schema in `config/schemas/`
4. Restart the connector

## Best Practices Implemented

- ✅ **Data Contracts**: Schema validation for all CDC events
- ✅ **Structured Logging**: JSON-formatted logs for easy parsing
- ✅ **Error Handling**: Comprehensive error handling with graceful degradation
- ✅ **Configuration Management**: Environment-based configuration with validation
- ✅ **Dockerization**: Complete containerization for easy deployment
- ✅ **Monitoring**: Built-in UI for monitoring CDC pipeline
- ✅ **CLI Tools**: Easy-to-use CLI for testing and data management
- ✅ **Documentation**: Comprehensive README and code comments

## Troubleshooting

### Connector Not Starting

1. Check Kafka Connect logs: `docker-compose logs kafka-connect`
2. Verify PostgreSQL is accessible from Kafka Connect
3. Ensure logical replication is enabled in PostgreSQL

### No Events Being Captured

1. Verify the connector is running: `make status`
2. Check if the table has `REPLICA IDENTITY FULL` set
3. Ensure changes are being made to the table
4. Check Kafka topic: `docker exec cdc-kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic sourcedb.public.users --from-beginning`

### Consumer Not Receiving Events

1. Check consumer logs: `make logs-consumer`
2. Verify Kafka connectivity
3. Check consumer group offset: View in Kafka UI

## License

MIT
