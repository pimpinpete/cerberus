#!/usr/bin/env python3
"""
Email Manager Agent Demo
Shows email categorization, response drafting, and action extraction.
"""

import sys
import json
from pathlib import Path

# Add cerberus to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cerberus import Cerberus


def demo_email_agent():
    """Run the Email Manager agent demo."""
    print("\n" + "="*60)
    print("🐕 CERBERUS - Email Manager Agent Demo")
    print("="*60 + "\n")

    # Initialize Cerberus
    print("Initializing Cerberus...")
    cerberus = Cerberus()

    # Demo 1: Inbox Summary
    print("\n📬 Demo 1: Inbox Summary")
    print("-" * 40)
    result = cerberus.run_agent("email_manager", "summarize inbox")
    print(f"Summary: {result.get('summary', 'N/A')}")
    print(f"Unread: {result.get('unread_count', 0)} emails")
    print(f"High Priority: {result.get('high_priority_count', 0)}")

    # Demo 2: Categorize Emails
    print("\n📂 Demo 2: Email Categorization")
    print("-" * 40)
    result = cerberus.run_agent("email_manager", "categorize emails", limit=5)
    for email in result.get("categorized", []):
        print(f"  • {email['subject'][:40]}...")
        print(f"    Category: {email['category']} | Priority: {email['priority']}")

    # Demo 3: Draft Response
    print("\n✍️  Demo 3: Draft Response")
    print("-" * 40)
    result = cerberus.run_agent("email_manager", "draft response", subject="Q4 Report")
    if result.get("draft_response"):
        print(f"To: {result.get('original_sender', 'Unknown')}")
        print(f"Re: {result.get('original_subject', 'Unknown')}")
        print(f"\nDraft:\n{result.get('draft_response', '')[:300]}...")

    # Demo 4: Extract Action Items
    print("\n✅ Demo 4: Action Items")
    print("-" * 40)
    result = cerberus.run_agent("email_manager", "extract action items", limit=5)
    for item in result.get("action_items", []):
        print(f"\nFrom: {item['sender']}")
        print(f"Subject: {item['email_subject']}")
        print(f"Actions:\n{item['actions']}")

    print("\n" + "="*60)
    print("Demo Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    demo_email_agent()
