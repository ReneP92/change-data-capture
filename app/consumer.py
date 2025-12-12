"""Kafka consumer for CDC events."""

import json
import signal
from typing import Dict, Any, Optional

from kafka import KafkaConsumer
from kafka.errors import KafkaError

from app.config import settings
from app.contracts import validator
from app.logger import get_logger

logger = get_logger(__name__)


class CDCConsumer:
    """Consumer for Change Data Capture events from Kafka."""

    def __init__(self):
        """Initialize Kafka consumer."""
        self.consumer: Optional[KafkaConsumer] = None
        self.running = False

    def _setup_consumer(self) -> KafkaConsumer:
        """Set up Kafka consumer with proper configuration."""
        return KafkaConsumer(
            settings.kafka_topic,
            bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
            group_id=settings.kafka_consumer_group,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            key_deserializer=lambda m: m.decode("utf-8") if m else None,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            consumer_timeout_ms=1000,
        )

    def _handle_signal(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info("Received shutdown signal, stopping consumer...")
        self.running = False

    def _process_event(self, message: Dict[str, Any]) -> None:
        """
        Process a single CDC event.

        Args:
            message: Kafka message value containing CDC event
        """
        try:
            # Extract operation type
            op = message.get("op", "unknown")
            before = message.get("before")
            after = message.get("after")
            source = message.get("source", {})

            logger.info(
                "CDC event received",
                operation=op,
                table=source.get("table"),
                database=source.get("db"),
                schema=source.get("schema"),
            )

            # Process based on operation type
            if op == "c":  # Create/Insert
                self._handle_insert(after, source)
            elif op == "u":  # Update
                self._handle_update(before, after, source)
            elif op == "d":  # Delete
                self._handle_delete(before, source)
            elif op == "r":  # Read (snapshot)
                self._handle_read(after, source)
            else:
                logger.warning(f"Unknown operation type: {op}")

        except Exception as e:
            logger.error(
                "Error processing CDC event",
                error=str(e),
                message=message,
                exc_info=True,
            )

    def _handle_insert(self, data: Optional[Dict[str, Any]], source: Dict[str, Any]) -> None:
        """Handle insert operation."""
        if not data:
            logger.warning("Insert operation with no data")
            return

        # Validate against data contract
        is_valid, error = validator.validate(data)
        if not is_valid:
            logger.error(
                "Data contract validation failed for insert",
                error=error,
                data=data,
            )
            return

        logger.info(
            "Processing insert",
            user_id=data.get("id"),
            email=data.get("email"),
        )
        # Here you would typically:
        # - Transform the data
        # - Write to destination system
        # - Update metrics
        # - Send notifications, etc.

    def _handle_update(
        self,
        before: Optional[Dict[str, Any]],
        after: Optional[Dict[str, Any]],
        source: Dict[str, Any],
    ) -> None:
        """Handle update operation."""
        if not after:
            logger.warning("Update operation with no after data")
            return

        # Validate against data contract
        is_valid, error = validator.validate(after)
        if not is_valid:
            logger.error(
                "Data contract validation failed for update",
                error=error,
                data=after,
            )
            return

        # Identify changed fields
        changed_fields = []
        if before:
            for key, value in after.items():
                if key not in before or before[key] != value:
                    changed_fields.append(key)

        logger.info(
            "Processing update",
            user_id=after.get("id"),
            email=after.get("email"),
            changed_fields=changed_fields,
        )

    def _handle_delete(self, data: Optional[Dict[str, Any]], source: Dict[str, Any]) -> None:
        """Handle delete operation."""
        if not data:
            logger.warning("Delete operation with no data")
            return

        logger.info(
            "Processing delete",
            user_id=data.get("id"),
            email=data.get("email"),
        )

    def _handle_read(self, data: Optional[Dict[str, Any]], source: Dict[str, Any]) -> None:
        """Handle read operation (from snapshot)."""
        if not data:
            logger.warning("Read operation with no data")
            return

        # Validate against data contract
        is_valid, error = validator.validate(data)
        if not is_valid:
            logger.error(
                "Data contract validation failed for read",
                error=error,
                data=data,
            )
            return

        logger.info(
            "Processing read (snapshot)",
            user_id=data.get("id"),
            email=data.get("email"),
        )

    def start(self) -> None:
        """Start consuming CDC events."""
        logger.info(
            "Starting CDC consumer",
            topic=settings.kafka_topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            consumer_group=settings.kafka_consumer_group,
        )

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        try:
            self.consumer = self._setup_consumer()
            self.running = True

            logger.info("CDC consumer started successfully")

            while self.running:
                try:
                    # Poll for messages with timeout
                    message_pack = self.consumer.poll(timeout_ms=1000)

                    for topic_partition, messages in message_pack.items():
                        for message in messages:
                            self._process_event(message.value)

                except KafkaError as e:
                    logger.error(f"Kafka error: {e}", exc_info=True)
                except Exception as e:
                    logger.error(f"Unexpected error: {e}", exc_info=True)

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the consumer gracefully."""
        logger.info("Stopping CDC consumer...")
        self.running = False

        if self.consumer:
            self.consumer.close()
            logger.info("CDC consumer stopped")

