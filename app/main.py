"""Main entry point for CDC consumer application."""

from app.consumer import CDCConsumer
from app.logger import get_logger

logger = get_logger(__name__)


def main():
    """Main application entry point."""
    logger.info("Starting Change Data Capture Consumer Application")

    consumer = CDCConsumer()
    consumer.start()


if __name__ == "__main__":
    main()

