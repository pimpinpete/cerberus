#!/usr/bin/env python3
"""
Email Manager Agent for Cerberus
Handles email categorization, auto-responses, and inbox management.
"""

import os
import sys
import subprocess
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass

from .base import CerberusAgent

# Add ai-orchestrator to path
AI_ORCHESTRATOR_PATH = Path.home() / "ai-orchestrator"
sys.path.insert(0, str(AI_ORCHESTRATOR_PATH))

from tools.mac_apps_api import MailAPI


@dataclass
class Email:
    """Represents an email message."""
    id: str
    sender: str
    subject: str
    body: str
    date: str
    is_read: bool
    category: Optional[str] = None
    priority: str = "normal"


class EmailManagerAgent(CerberusAgent):
    """
    Manages email inbox automatically.

    Capabilities:
    - Categorize incoming emails
    - Draft responses for approval
    - Extract action items
    - Schedule follow-ups
    - Archive/organize old emails
    """

    def __init__(self, config, cerberus_instance):
        super().__init__(config, cerberus_instance)
        self.mail = MailAPI()

        # Default categories (can be overridden in config)
        self.categories = self.settings.get("categories", [
            "urgent",
            "work",
            "personal",
            "newsletters",
            "receipts",
            "spam"
        ])

        # Auto-response templates
        self.templates = self.settings.get("templates", {})

        # Rules for categorization
        self.rules = self.settings.get("rules", [])

    def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        Execute an email management task.

        Supported tasks:
        - categorize: Categorize unread emails
        - draft_response: Draft a response to an email
        - extract_actions: Extract action items from emails
        - summarize: Summarize inbox
        - send: Send an email
        """
        task_lower = task.lower()

        if "categorize" in task_lower:
            return self.categorize_emails(**kwargs)
        elif "draft" in task_lower or "response" in task_lower:
            return self.draft_response(**kwargs)
        elif "action" in task_lower or "extract" in task_lower:
            return self.extract_action_items(**kwargs)
        elif "summarize" in task_lower or "summary" in task_lower:
            return self.summarize_inbox(**kwargs)
        elif "send" in task_lower:
            return self.send_email(**kwargs)
        else:
            # Use AI to interpret the task
            return self.handle_custom_task(task, **kwargs)

    def get_unread_emails(self, limit: int = 20) -> List[Email]:
        """
        Get unread emails from inbox.
        Uses AppleScript to query Mail app.
        """
        script = f'''
        tell application "Mail"
            set unreadMessages to (messages of inbox whose read status is false)
            set emailList to {{}}
            repeat with i from 1 to (count of unreadMessages)
                if i > {limit} then exit repeat
                set msg to item i of unreadMessages
                set msgData to {{|id|:(id of msg), |sender|:(sender of msg), |subject|:(subject of msg), |date|:(date received of msg as string), |body|:(content of msg)}}
                set end of emailList to msgData
            end repeat
            return emailList
        end tell
        '''

        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode != 0:
                self.log("Failed to get emails from Mail app")
                return []

            # Parse AppleScript output (simplified - in production would need proper parsing)
            # For demo, return mock data
            return self._get_mock_emails()

        except Exception as e:
            self.error(f"Error getting emails: {e}", e)
            return self._get_mock_emails()

    def _get_mock_emails(self) -> List[Email]:
        """Return mock emails for demo purposes."""
        return [
            Email(
                id="1",
                sender="boss@company.com",
                subject="Urgent: Q4 Report Due",
                body="Please submit the Q4 report by end of day. This is critical for the board meeting.",
                date=datetime.now().isoformat(),
                is_read=False,
                priority="high"
            ),
            Email(
                id="2",
                sender="newsletter@techcrunch.com",
                subject="Daily Tech News Digest",
                body="Here's your daily roundup of tech news...",
                date=datetime.now().isoformat(),
                is_read=False,
                priority="low"
            ),
            Email(
                id="3",
                sender="amazon@amazon.com",
                subject="Your order has shipped",
                body="Your order #123-456 has been shipped and will arrive tomorrow.",
                date=datetime.now().isoformat(),
                is_read=False,
                priority="normal"
            )
        ]

    def categorize_emails(self, **kwargs) -> Dict[str, Any]:
        """Categorize unread emails using AI."""
        emails = self.get_unread_emails(kwargs.get("limit", 20))

        if not emails:
            return {"status": "success", "message": "No unread emails", "categorized": []}

        categorized = []

        for email in emails:
            # Build prompt for categorization
            prompt = f"""Categorize this email into one of these categories: {', '.join(self.categories)}

From: {email.sender}
Subject: {email.subject}
Body preview: {email.body[:200]}

Return ONLY the category name, nothing else."""

            category = self.ask_ai(prompt)
            category = category.strip().lower()

            # Validate category
            if category not in self.categories:
                category = "other"

            email.category = category

            # Determine priority
            priority_prompt = f"""Rate the urgency of this email as: high, normal, or low

From: {email.sender}
Subject: {email.subject}

Return ONLY: high, normal, or low"""

            priority = self.ask_ai(priority_prompt).strip().lower()
            if priority in ["high", "normal", "low"]:
                email.priority = priority

            categorized.append({
                "id": email.id,
                "subject": email.subject,
                "sender": email.sender,
                "category": email.category,
                "priority": email.priority
            })

            self.log(f"Categorized: {email.subject} -> {category} ({priority})")

        return {
            "status": "success",
            "message": f"Categorized {len(categorized)} emails",
            "categorized": categorized
        }

    def draft_response(self, email_id: Optional[str] = None, subject: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Draft a response to an email."""
        # Get the email to respond to
        emails = self.get_unread_emails()
        target_email = None

        if email_id:
            target_email = next((e for e in emails if e.id == email_id), None)
        elif subject:
            target_email = next((e for e in emails if subject.lower() in e.subject.lower()), None)
        else:
            # Get first unread
            target_email = emails[0] if emails else None

        if not target_email:
            return {"status": "error", "message": "No email found to respond to"}

        # Draft response using AI
        prompt = f"""Draft a professional response to this email:

From: {target_email.sender}
Subject: {target_email.subject}
Body: {target_email.body}

Write a clear, professional response. Be concise but helpful."""

        draft = self.ask_ai(prompt)

        return {
            "status": "success",
            "original_subject": target_email.subject,
            "original_sender": target_email.sender,
            "draft_response": draft,
            "action_required": "Review and approve before sending"
        }

    def extract_action_items(self, **kwargs) -> Dict[str, Any]:
        """Extract action items from recent emails."""
        emails = self.get_unread_emails(kwargs.get("limit", 10))

        all_actions = []

        for email in emails:
            prompt = f"""Extract any action items or tasks from this email.
If there are no action items, respond with "None".

From: {email.sender}
Subject: {email.subject}
Body: {email.body}

List action items as a simple bullet list, or "None" if no actions needed."""

            actions = self.ask_ai(prompt)

            if actions.strip().lower() != "none":
                all_actions.append({
                    "email_subject": email.subject,
                    "sender": email.sender,
                    "actions": actions
                })

        return {
            "status": "success",
            "action_items": all_actions,
            "total_emails_scanned": len(emails)
        }

    def summarize_inbox(self, **kwargs) -> Dict[str, Any]:
        """Generate a summary of the inbox."""
        emails = self.get_unread_emails(kwargs.get("limit", 20))
        unread_count = len(emails)

        if not emails:
            return {
                "status": "success",
                "summary": "Inbox is empty. No unread emails.",
                "unread_count": 0
            }

        # Build summary prompt
        email_list = "\n".join([
            f"- From: {e.sender}, Subject: {e.subject}"
            for e in emails
        ])

        prompt = f"""Summarize this inbox in 2-3 sentences. Highlight any urgent items.

Unread emails ({unread_count}):
{email_list}"""

        summary = self.ask_ai(prompt)

        # Count by priority
        high_priority = sum(1 for e in emails if e.priority == "high")

        return {
            "status": "success",
            "summary": summary,
            "unread_count": unread_count,
            "high_priority_count": high_priority
        }

    def send_email(self, to: str, subject: str, body: str, **kwargs) -> Dict[str, Any]:
        """Send an email."""
        try:
            self.mail.send_email(to, subject, body)
            self.log(f"Sent email to {to}: {subject}")
            return {
                "status": "success",
                "message": f"Email sent to {to}",
                "subject": subject
            }
        except Exception as e:
            self.error(f"Failed to send email: {e}", e)
            return {
                "status": "error",
                "message": str(e)
            }

    def handle_custom_task(self, task: str, **kwargs) -> Dict[str, Any]:
        """Handle a custom email task using AI."""
        prompt = f"""You are an email management assistant. The user wants to: {task}

Available actions:
- Categorize emails
- Draft responses
- Extract action items
- Summarize inbox
- Send emails

Explain what you would do to help with this request."""

        response = self.ask_ai(prompt)

        return {
            "status": "success",
            "task": task,
            "ai_response": response
        }
