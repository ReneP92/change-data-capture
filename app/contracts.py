"""Data contract validation for CDC events."""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import jsonschema
from jsonschema import ValidationError

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


class DataContractValidator:
    """Validates CDC events against data contracts."""

    def __init__(self, schema_path: Optional[Path] = None):
        """Initialize validator with schema."""
        self.schema_path = schema_path or settings.schema_file_path
        self.schema = self._load_schema()
        self.validator = jsonschema.Draft7Validator(self.schema)

    def _load_schema(self) -> Dict[str, Any]:
        """Load JSON schema from file."""
        try:
            with open(self.schema_path, "r") as f:
                schema = json.load(f)
            logger.info(f"Loaded data contract schema from {self.schema_path}")
            return schema
        except FileNotFoundError:
            logger.error(f"Schema file not found: {self.schema_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in schema file: {e}")
            raise

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate data against contract.

        Args:
            data: Data to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.validator.validate(data)
            return True, None
        except ValidationError as e:
            error_msg = f"Validation error: {e.message} at {'.'.join(str(p) for p in e.path)}"
            logger.warning(f"Data contract validation failed: {error_msg}")
            return False, error_msg

    def validate_with_details(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data and return detailed results.

        Args:
            data: Data to validate

        Returns:
            Dictionary with validation results
        """
        errors = list(self.validator.iter_errors(data))
        is_valid = len(errors) == 0

        return {
            "valid": is_valid,
            "errors": [
                {
                    "message": error.message,
                    "path": list(error.path),
                    "schema_path": list(error.schema_path),
                }
                for error in errors
            ],
        }


# Global validator instance
validator = DataContractValidator()

