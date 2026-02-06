#!/usr/bin/env python3
"""
Document Processor Agent Demo
Shows document summarization, extraction, and auto-filing.
"""

import sys
import json
from pathlib import Path

# Add cerberus to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cerberus import Cerberus


def demo_doc_processor():
    """Run the Document Processor agent demo."""
    print("\n" + "="*60)
    print("🐕 CERBERUS - Document Processor Agent Demo")
    print("="*60 + "\n")

    # Initialize Cerberus
    print("Initializing Cerberus...")
    cerberus = Cerberus()

    # Sample document for demo
    sample_document = """
    QUARTERLY BUSINESS REPORT
    Q4 2024

    Executive Summary
    -----------------
    This quarter marked significant growth across all business units.
    Revenue increased by 23% compared to Q3, primarily driven by
    our new enterprise product line. Customer acquisition costs
    decreased by 15% due to improved marketing efficiency.

    Key Achievements:
    • Launched Enterprise Pro product - 150 new customers
    • Expanded to European market - offices in London and Berlin
    • Hired 45 new employees, bringing total headcount to 230
    • Achieved SOC 2 Type II certification

    Financial Highlights:
    • Total Revenue: $12.5M (up from $10.2M in Q3)
    • Operating Expenses: $8.3M
    • Net Profit: $4.2M
    • Cash Position: $25M

    Challenges:
    • Supply chain delays affected hardware delivery times
    • Increased competition in mid-market segment
    • Need for additional engineering resources

    Q1 2025 Priorities:
    1. Launch mobile application by March 15
    2. Expand sales team by 20%
    3. Complete Series B fundraising
    4. Establish APAC presence

    Contact: CEO John Anderson, john@company.com
    Board Meeting: February 15, 2025 at 10:00 AM
    Location: 500 Tech Drive, San Francisco, CA
    """

    # Demo 1: Document Summary
    print("\n📝 Demo 1: Document Summarization")
    print("-" * 40)
    result = cerberus.run_agent(
        "doc_processor",
        "summarize document",
        text=sample_document,
        length="medium"
    )
    print(f"Summary:\n{result.get('summary', 'N/A')[:500]}...")
    print(f"\nKey Points:")
    for point in result.get("key_points", [])[:5]:
        print(f"  • {point}")

    # Demo 2: Information Extraction
    print("\n🔍 Demo 2: Information Extraction")
    print("-" * 40)
    result = cerberus.run_agent(
        "doc_processor",
        "extract info",
        text=sample_document,
        info_types=["dates", "amounts", "names", "organizations", "locations"]
    )
    extracted = result.get("extracted", {})
    for info_type, values in extracted.items():
        if info_type != "raw" and values:
            print(f"\n{info_type.title()}:")
            if isinstance(values, list):
                for v in values[:5]:
                    print(f"  • {v}")
            else:
                print(f"  {values}")

    # Demo 3: Document Analysis
    print("\n🧠 Demo 3: Deep Analysis")
    print("-" * 40)
    result = cerberus.run_agent(
        "doc_processor",
        "analyze document",
        text=sample_document
    )
    print(result.get("analysis", "N/A")[:600] + "...")

    # Demo 4: Report Generation
    print("\n📊 Demo 4: Report Generation")
    print("-" * 40)

    # Create a sample file for the demo
    sample_file = Path.home() / "cerberus" / "demos" / "sample_report.txt"
    sample_file.write_text(sample_document)

    result = cerberus.run_agent(
        "doc_processor",
        "generate report",
        documents=[str(sample_file)],
        report_type="summary",
        title="Q4 2024 Analysis Report"
    )
    print(f"Report Title: {result.get('title', 'N/A')}")
    print(f"Documents Analyzed: {result.get('documents_analyzed', 0)}")
    print(f"\nGenerated Report:\n{result.get('report', 'N/A')[:500]}...")

    # Cleanup
    sample_file.unlink(missing_ok=True)

    print("\n" + "="*60)
    print("Demo Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    demo_doc_processor()
