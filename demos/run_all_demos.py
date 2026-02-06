#!/usr/bin/env python3
"""
Run All Cerberus Agent Demos
Showcase the full capabilities of the Cerberus platform.
"""

import sys
from pathlib import Path

# Add cerberus to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from demo_email import demo_email_agent
from demo_data_entry import demo_data_entry_agent
from demo_docs import demo_doc_processor


def main():
    """Run all Cerberus demos."""
    print("\n" + "="*70)
    print("🐕🐕🐕 CERBERUS PLATFORM - FULL DEMO SUITE 🐕🐕🐕")
    print("AI Agents for Business Automation")
    print("="*70)

    print("\nThis demo will showcase three AI agents:")
    print("  1. Email Manager - Inbox automation")
    print("  2. Data Entry - Document extraction & spreadsheets")
    print("  3. Document Processor - Summarization & filing")

    print("\n" + "-"*70)
    input("Press Enter to start the Email Manager demo...")
    demo_email_agent()

    print("\n" + "-"*70)
    input("Press Enter to start the Data Entry demo...")
    demo_data_entry_agent()

    print("\n" + "-"*70)
    input("Press Enter to start the Document Processor demo...")
    demo_doc_processor()

    print("\n" + "="*70)
    print("ALL DEMOS COMPLETE!")
    print("="*70)
    print("""
Cerberus is ready to automate your back-office operations.

Next steps:
  1. Configure agents in ~/cerberus/agents/*.yaml
  2. Run: python ~/cerberus/cerberus.py status
  3. Use: python ~/cerberus/cerberus.py run --agent <name> --task <task>

For custom agents or integrations, contact us!
""")


if __name__ == "__main__":
    main()
