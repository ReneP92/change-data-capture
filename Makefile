.PHONY: help up down restart logs clean setup-connector test-cli

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Start all services
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@make setup-connector

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	make down
	make up

logs: ## Show logs from all services
	docker-compose logs -f

logs-consumer: ## Show logs from CDC consumer
	docker-compose logs -f cdc-consumer

setup-connector: ## Set up Debezium connector
	@echo "Setting up Debezium connector..."
	@curl -i -X POST http://localhost:8083/connectors \
		-H "Content-Type: application/json" \
		-d @debezium-config/debezium-postgres-connector.json || true
	@echo ""
	@echo "Connector setup complete. Check status at http://localhost:8083/connectors/debezium-postgres-connector/status"

clean: ## Remove all containers, volumes, and networks
	docker-compose down -v
	docker system prune -f

test-cli: ## Run CLI commands to test CDC
	@echo "Testing CDC with CLI..."
	python -m app.cli generate --count 3
	python -m app.cli list

status: ## Check status of all services
	@echo "=== Service Status ==="
	@docker-compose ps
	@echo ""
	@echo "=== Kafka Topics ==="
	@docker exec cdc-kafka kafka-topics --bootstrap-server localhost:9092 --list || echo "Kafka not ready"
	@echo ""
	@echo "=== Debezium Connectors ==="
	@curl -s http://localhost:8083/connectors | python -m json.tool || echo "Kafka Connect not ready"

query-data: ## Opens Harlequin for data inspection.
	@echo "Opening Harlequin IDE..."
	@harlequin -a postgres "postgres://postgres:postgres@localhost:5432/sourcedb"

view-messages: ## Shows messages in queue
	@echo "Viewing messages in topic..."
	@docker exec cdc-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic sourcedb.public.users \
  --from-beginning
