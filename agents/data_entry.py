#!/usr/bin/env python3
"""
Data Entry Agent for Cerberus
Handles automated data extraction and entry into spreadsheets/databases.
"""

import os
import sys
import json
import csv
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass

from .base import CerberusAgent

# Add ai-orchestrator to path
AI_ORCHESTRATOR_PATH = Path.home() / "ai-orchestrator"
sys.path.insert(0, str(AI_ORCHESTRATOR_PATH))


@dataclass
class ExtractedData:
    """Represents data extracted from a document."""
    source: str
    fields: Dict[str, Any]
    confidence: float
    timestamp: str


class DataEntryAgent(CerberusAgent):
    """
    Automates data entry tasks.

    Capabilities:
    - Watch folders for new documents
    - Extract data from PDFs/images (OCR)
    - Populate spreadsheets (CSV, Google Sheets)
    - Validate and flag errors
    - Transform data formats
    """

    def __init__(self, config, cerberus_instance):
        super().__init__(config, cerberus_instance)

        # Watch folders
        self.watch_folders = self.settings.get("watch_folders", [])

        # Output destinations
        self.output_path = Path(self.settings.get("output_path", "~/cerberus/data"))
        self.output_path = self.output_path.expanduser()
        self.output_path.mkdir(parents=True, exist_ok=True)

        # Field mappings
        self.field_mappings = self.settings.get("field_mappings", {})

        # Validation rules
        self.validation_rules = self.settings.get("validation_rules", {})

    def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a data entry task.

        Supported tasks:
        - extract: Extract data from a document
        - watch: Watch folder for new files
        - populate: Populate spreadsheet with data
        - validate: Validate data against rules
        - transform: Transform data format
        """
        task_lower = task.lower()

        if "extract" in task_lower:
            return self.extract_data(**kwargs)
        elif "watch" in task_lower:
            return self.watch_folder(**kwargs)
        elif "populate" in task_lower or "spreadsheet" in task_lower:
            return self.populate_spreadsheet(**kwargs)
        elif "validate" in task_lower:
            return self.validate_data(**kwargs)
        elif "transform" in task_lower:
            return self.transform_data(**kwargs)
        else:
            return self.handle_custom_task(task, **kwargs)

    def extract_data(self, file_path: Optional[str] = None, text: Optional[str] = None,
                     fields: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """
        Extract structured data from a document or text.

        Args:
            file_path: Path to document (PDF, image, etc.)
            text: Raw text to extract from
            fields: List of fields to extract

        Returns:
            Extracted data dictionary
        """
        if file_path:
            text = self._read_document(file_path)

        if not text:
            return {"status": "error", "message": "No text provided for extraction"}

        # Default fields if none specified
        if not fields:
            fields = ["name", "email", "phone", "address", "date", "amount"]

        # Build extraction prompt
        fields_str = ", ".join(fields)
        prompt = f"""Extract the following fields from this text: {fields_str}

Text:
{text[:2000]}

Return as JSON with the field names as keys. Use null for missing fields.
Example: {{"name": "John Doe", "email": "john@example.com", "phone": null}}"""

        response = self.ask_ai(prompt)

        # Parse JSON response
        try:
            # Try to extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                extracted = json.loads(json_str)
            else:
                extracted = {"raw_response": response}
        except json.JSONDecodeError:
            extracted = {"raw_response": response}

        result = ExtractedData(
            source=file_path or "text_input",
            fields=extracted,
            confidence=0.9,  # Would be calculated based on AI confidence
            timestamp=datetime.now().isoformat()
        )

        self.log(f"Extracted {len(extracted)} fields from {result.source}")

        return {
            "status": "success",
            "extracted": extracted,
            "source": result.source,
            "confidence": result.confidence
        }

    def _read_document(self, file_path: str) -> str:
        """Read text from a document."""
        path = Path(file_path).expanduser()

        if not path.exists():
            self.error(f"File not found: {file_path}")
            return ""

        suffix = path.suffix.lower()

        if suffix == ".txt":
            return path.read_text()

        elif suffix == ".pdf":
            # Use pdftotext if available
            try:
                result = subprocess.run(
                    ["pdftotext", str(path), "-"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    return result.stdout
            except FileNotFoundError:
                pass

            # Fallback: use AI to describe what we need
            return f"[PDF file: {path.name} - OCR needed]"

        elif suffix in [".png", ".jpg", ".jpeg"]:
            # Use tesseract for OCR if available
            try:
                result = subprocess.run(
                    ["tesseract", str(path), "stdout"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    return result.stdout
            except FileNotFoundError:
                pass

            return f"[Image file: {path.name} - OCR needed]"

        elif suffix == ".csv":
            return path.read_text()

        elif suffix == ".json":
            return path.read_text()

        else:
            return path.read_text()

    def watch_folder(self, folder_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Watch a folder for new files and process them.

        In production, this would set up a file watcher.
        For demo, it scans the folder once.
        """
        folder = Path(folder_path or self.watch_folders[0] if self.watch_folders else "~/Downloads").expanduser()

        if not folder.exists():
            return {"status": "error", "message": f"Folder not found: {folder}"}

        # Get recent files (last 24 hours for demo)
        recent_files = []
        for file in folder.iterdir():
            if file.is_file() and file.suffix.lower() in [".pdf", ".txt", ".csv", ".png", ".jpg"]:
                recent_files.append(str(file))

        self.log(f"Found {len(recent_files)} processable files in {folder}")

        return {
            "status": "success",
            "folder": str(folder),
            "files_found": len(recent_files),
            "files": recent_files[:10]  # Limit to 10 for display
        }

    def populate_spreadsheet(self, data: Optional[Dict] = None,
                            output_file: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Populate a spreadsheet with extracted data.

        Args:
            data: Data to write (dict or list of dicts)
            output_file: Output file path (CSV)
        """
        if not data:
            return {"status": "error", "message": "No data provided"}

        output = Path(output_file) if output_file else self.output_path / f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output = output.expanduser()

        # Ensure data is a list
        if isinstance(data, dict):
            data = [data]

        # Write CSV
        if data:
            fieldnames = list(data[0].keys())
            with open(output, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            self.log(f"Wrote {len(data)} rows to {output}")

            return {
                "status": "success",
                "output_file": str(output),
                "rows_written": len(data)
            }

        return {"status": "error", "message": "No data to write"}

    def validate_data(self, data: Dict, rules: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """
        Validate data against rules.

        Args:
            data: Data to validate
            rules: Validation rules (optional, uses config if not provided)
        """
        rules = rules or self.validation_rules
        errors = []
        warnings = []

        for field, value in data.items():
            field_rules = rules.get(field, {})

            # Required check
            if field_rules.get("required") and not value:
                errors.append(f"Missing required field: {field}")

            # Type check
            expected_type = field_rules.get("type")
            if expected_type and value:
                if expected_type == "email" and "@" not in str(value):
                    errors.append(f"Invalid email format: {field}")
                elif expected_type == "phone" and not str(value).replace("-", "").replace(" ", "").isdigit():
                    warnings.append(f"Possible invalid phone: {field}")
                elif expected_type == "number":
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        errors.append(f"Expected number for {field}")

            # Pattern check
            pattern = field_rules.get("pattern")
            if pattern and value:
                import re
                if not re.match(pattern, str(value)):
                    errors.append(f"Field {field} doesn't match pattern")

        is_valid = len(errors) == 0

        return {
            "status": "success",
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "fields_checked": len(data)
        }

    def transform_data(self, data: Dict, mappings: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """
        Transform data from one format to another.

        Args:
            data: Source data
            mappings: Field mappings (old_name -> new_name)
        """
        mappings = mappings or self.field_mappings
        transformed = {}

        for old_key, value in data.items():
            new_key = mappings.get(old_key, old_key)
            transformed[new_key] = value

        return {
            "status": "success",
            "original": data,
            "transformed": transformed,
            "mappings_applied": len([k for k in data.keys() if k in mappings])
        }

    def handle_custom_task(self, task: str, **kwargs) -> Dict[str, Any]:
        """Handle a custom data entry task using AI."""
        prompt = f"""You are a data entry automation assistant. The user wants to: {task}

Available actions:
- Extract data from documents (PDF, images, text)
- Watch folders for new files
- Populate spreadsheets (CSV)
- Validate data against rules
- Transform data formats

Explain what you would do to help with this request."""

        response = self.ask_ai(prompt)

        return {
            "status": "success",
            "task": task,
            "ai_response": response
        }
