#!/usr/bin/env python3
"""
Data Entry Agent Demo
Shows data extraction, validation, and spreadsheet population.
"""

import sys
import json
from pathlib import Path

# Add cerberus to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cerberus import Cerberus


def demo_data_entry_agent():
    """Run the Data Entry agent demo."""
    print("\n" + "="*60)
    print("🐕 CERBERUS - Data Entry Agent Demo")
    print("="*60 + "\n")

    # Initialize Cerberus
    print("Initializing Cerberus...")
    cerberus = Cerberus()

    # Sample invoice text for demo
    sample_invoice = """
    INVOICE #INV-2024-001

    From: ABC Company Ltd
    123 Business Street
    New York, NY 10001
    Email: billing@abccompany.com
    Phone: (555) 123-4567

    Bill To:
    John Smith
    john.smith@email.com
    456 Customer Ave
    Los Angeles, CA 90001

    Date: January 15, 2024
    Due Date: February 15, 2024

    Items:
    - Consulting Services: $2,500.00
    - Software License: $500.00
    - Support (12 months): $1,200.00

    Subtotal: $4,200.00
    Tax (8%): $336.00
    Total Due: $4,536.00

    Payment Terms: Net 30
    """

    # Demo 1: Extract Data from Text
    print("\n📄 Demo 1: Data Extraction")
    print("-" * 40)
    result = cerberus.run_agent(
        "data_entry",
        "extract data",
        text=sample_invoice,
        fields=["name", "email", "phone", "amount", "date", "address"]
    )
    print("Extracted fields:")
    for key, value in result.get("extracted", {}).items():
        if key != "raw_response":
            print(f"  • {key}: {value}")

    # Demo 2: Validate Data
    print("\n✓ Demo 2: Data Validation")
    print("-" * 40)
    test_data = {
        "name": "John Smith",
        "email": "john.smith@email.com",
        "phone": "(555) 123-4567",
        "amount": "$4,536.00"
    }
    result = cerberus.run_agent(
        "data_entry",
        "validate data",
        data=test_data,
        rules={
            "email": {"type": "email", "required": True},
            "phone": {"type": "phone", "required": True},
            "amount": {"type": "number", "required": True}
        }
    )
    print(f"Valid: {result.get('is_valid', False)}")
    if result.get("errors"):
        print("Errors:")
        for error in result["errors"]:
            print(f"  ✗ {error}")
    if result.get("warnings"):
        print("Warnings:")
        for warning in result["warnings"]:
            print(f"  ⚠ {warning}")

    # Demo 3: Watch Folder
    print("\n📁 Demo 3: Folder Watching")
    print("-" * 40)
    result = cerberus.run_agent(
        "data_entry",
        "watch folder",
        folder_path="~/Downloads"
    )
    print(f"Folder: {result.get('folder', 'N/A')}")
    print(f"Files found: {result.get('files_found', 0)}")
    files = result.get("files", [])[:5]
    for f in files:
        print(f"  • {Path(f).name}")

    # Demo 4: Transform Data
    print("\n🔄 Demo 4: Data Transformation")
    print("-" * 40)
    source_data = {
        "first_name": "John",
        "last_name": "Smith",
        "email_address": "john@example.com",
        "phone_number": "555-1234"
    }
    result = cerberus.run_agent(
        "data_entry",
        "transform data",
        data=source_data,
        mappings={
            "first_name": "firstName",
            "last_name": "lastName",
            "email_address": "email",
            "phone_number": "phone"
        }
    )
    print("Original → Transformed:")
    for old, new in zip(source_data.keys(), result.get("transformed", {}).keys()):
        print(f"  {old} → {new}")

    # Demo 5: Populate Spreadsheet
    print("\n📊 Demo 5: Spreadsheet Population")
    print("-" * 40)
    sample_data = [
        {"name": "John Smith", "email": "john@example.com", "amount": 4536.00},
        {"name": "Jane Doe", "email": "jane@example.com", "amount": 2150.00},
        {"name": "Bob Wilson", "email": "bob@example.com", "amount": 3275.50}
    ]
    result = cerberus.run_agent(
        "data_entry",
        "populate spreadsheet",
        data=sample_data
    )
    print(f"Output: {result.get('output_file', 'N/A')}")
    print(f"Rows written: {result.get('rows_written', 0)}")

    print("\n" + "="*60)
    print("Demo Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    demo_data_entry_agent()
