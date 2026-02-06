#!/usr/bin/env python3
"""
Document Processor Agent for Cerberus
Handles document summarization, extraction, filing, and report generation.
"""

import os
import sys
import json
import shutil
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass

from .base import CerberusAgent

# Add ai-orchestrator to path
AI_ORCHESTRATOR_PATH = Path.home() / "ai-orchestrator"
sys.path.insert(0, str(AI_ORCHESTRATOR_PATH))


@dataclass
class DocumentSummary:
    """Summary of a processed document."""
    file_path: str
    title: str
    summary: str
    key_points: List[str]
    category: str
    page_count: int
    word_count: int
    processed_at: str


class DocProcessorAgent(CerberusAgent):
    """
    Processes documents automatically.

    Capabilities:
    - Summarize long documents
    - Extract key information
    - Auto-file to correct folders
    - Generate reports
    - Convert between formats
    - Merge/split documents
    """

    def __init__(self, config, cerberus_instance):
        super().__init__(config, cerberus_instance)

        # Filing structure
        self.file_categories = self.settings.get("categories", {
            "invoices": "~/Documents/Invoices",
            "contracts": "~/Documents/Contracts",
            "reports": "~/Documents/Reports",
            "receipts": "~/Documents/Receipts",
            "personal": "~/Documents/Personal",
            "other": "~/Documents/Other"
        })

        # Ensure directories exist
        for category, path in self.file_categories.items():
            Path(path).expanduser().mkdir(parents=True, exist_ok=True)

        # Summary length preferences
        self.summary_length = self.settings.get("summary_length", "medium")

    def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a document processing task.

        Supported tasks:
        - summarize: Summarize a document
        - extract: Extract specific information
        - file: Auto-file document to correct folder
        - report: Generate a report
        - analyze: Analyze document content
        """
        task_lower = task.lower()

        if "summarize" in task_lower or "summary" in task_lower:
            return self.summarize_document(**kwargs)
        elif "extract" in task_lower:
            return self.extract_info(**kwargs)
        elif "file" in task_lower or "organize" in task_lower:
            return self.auto_file(**kwargs)
        elif "report" in task_lower:
            return self.generate_report(**kwargs)
        elif "analyze" in task_lower:
            return self.analyze_document(**kwargs)
        else:
            return self.handle_custom_task(task, **kwargs)

    def _read_document(self, file_path: str) -> tuple[str, int]:
        """
        Read document content.

        Returns:
            Tuple of (content, word_count)
        """
        path = Path(file_path).expanduser()

        if not path.exists():
            self.error(f"File not found: {file_path}")
            return "", 0

        suffix = path.suffix.lower()
        content = ""

        if suffix == ".txt" or suffix == ".md":
            content = path.read_text()
        elif suffix == ".pdf":
            # Try pdftotext
            import subprocess
            try:
                result = subprocess.run(
                    ["pdftotext", str(path), "-"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    content = result.stdout
            except FileNotFoundError:
                content = f"[PDF document: {path.name}]"
        elif suffix == ".docx":
            # Would use python-docx in production
            content = f"[Word document: {path.name}]"
        else:
            try:
                content = path.read_text()
            except:
                content = f"[Binary file: {path.name}]"

        word_count = len(content.split())
        return content, word_count

    def summarize_document(self, file_path: Optional[str] = None,
                          text: Optional[str] = None,
                          length: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Summarize a document.

        Args:
            file_path: Path to document
            text: Raw text to summarize
            length: Summary length (short/medium/long)
        """
        if file_path:
            content, word_count = self._read_document(file_path)
            source = file_path
        elif text:
            content = text
            word_count = len(text.split())
            source = "text_input"
        else:
            return {"status": "error", "message": "No document or text provided"}

        length = length or self.summary_length

        length_instructions = {
            "short": "in 2-3 sentences",
            "medium": "in a short paragraph (4-6 sentences)",
            "long": "in 2-3 paragraphs with key details"
        }

        prompt = f"""Summarize the following document {length_instructions.get(length, 'concisely')}:

{content[:4000]}

Also extract 3-5 key points as a bullet list."""

        response = self.ask_ai(prompt)

        # Parse response to separate summary and key points
        summary = response
        key_points = []

        if "•" in response or "-" in response or "1." in response:
            # Try to extract bullet points
            lines = response.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith(("•", "-", "*", "1", "2", "3", "4", "5")):
                    key_points.append(line.lstrip("•-*0123456789. "))

        doc_summary = DocumentSummary(
            file_path=source,
            title=Path(source).stem if file_path else "Text Input",
            summary=summary,
            key_points=key_points[:5],
            category="uncategorized",
            page_count=max(1, word_count // 500),  # Rough estimate
            word_count=word_count,
            processed_at=datetime.now().isoformat()
        )

        self.log(f"Summarized document: {source} ({word_count} words)")

        return {
            "status": "success",
            "summary": doc_summary.summary,
            "key_points": doc_summary.key_points,
            "word_count": word_count,
            "source": source
        }

    def extract_info(self, file_path: Optional[str] = None,
                    text: Optional[str] = None,
                    info_types: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """
        Extract specific information from a document.

        Args:
            file_path: Path to document
            text: Raw text
            info_types: Types of info to extract (dates, names, amounts, etc.)
        """
        if file_path:
            content, _ = self._read_document(file_path)
            source = file_path
        elif text:
            content = text
            source = "text_input"
        else:
            return {"status": "error", "message": "No document or text provided"}

        info_types = info_types or ["dates", "names", "amounts", "locations", "organizations"]

        prompt = f"""Extract the following information from this document:
{', '.join(info_types)}

Document:
{content[:3000]}

Return as JSON with each info type as a key and a list of found values.
Example: {{"dates": ["2024-01-15", "2024-02-01"], "amounts": ["$500", "$1,200"]}}"""

        response = self.ask_ai(prompt)

        # Parse JSON
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                extracted = json.loads(response[json_start:json_end])
            else:
                extracted = {"raw": response}
        except json.JSONDecodeError:
            extracted = {"raw": response}

        return {
            "status": "success",
            "extracted": extracted,
            "source": source,
            "info_types": info_types
        }

    def auto_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        Automatically file a document to the correct folder.

        Args:
            file_path: Path to document to file
        """
        path = Path(file_path).expanduser()

        if not path.exists():
            return {"status": "error", "message": f"File not found: {file_path}"}

        # Read document to determine category
        content, _ = self._read_document(file_path)

        categories_str = ", ".join(self.file_categories.keys())
        prompt = f"""Categorize this document into one of these categories: {categories_str}

Document name: {path.name}
Content preview: {content[:500]}

Return ONLY the category name, nothing else."""

        category = self.ask_ai(prompt).strip().lower()

        # Validate category
        if category not in self.file_categories:
            category = "other"

        # Get destination folder
        dest_folder = Path(self.file_categories[category]).expanduser()
        dest_folder.mkdir(parents=True, exist_ok=True)

        # Move or copy file
        dest_path = dest_folder / path.name

        # Handle duplicate names
        if dest_path.exists():
            stem = path.stem
            suffix = path.suffix
            counter = 1
            while dest_path.exists():
                dest_path = dest_folder / f"{stem}_{counter}{suffix}"
                counter += 1

        shutil.copy2(path, dest_path)

        self.log(f"Filed {path.name} to {category}")

        return {
            "status": "success",
            "original": str(path),
            "destination": str(dest_path),
            "category": category
        }

    def generate_report(self, documents: Optional[List[str]] = None,
                       report_type: str = "summary",
                       title: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Generate a report from one or more documents.

        Args:
            documents: List of document paths
            report_type: Type of report (summary, analysis, comparison)
            title: Report title
        """
        if not documents:
            return {"status": "error", "message": "No documents provided"}

        # Read all documents
        all_content = []
        for doc in documents:
            content, word_count = self._read_document(doc)
            all_content.append({
                "file": doc,
                "content": content[:2000],
                "words": word_count
            })

        # Build report prompt
        docs_summary = "\n\n".join([
            f"Document: {d['file']}\nContent: {d['content'][:500]}..."
            for d in all_content
        ])

        if report_type == "summary":
            prompt = f"""Generate a summary report from these documents:

{docs_summary}

Create a professional report with:
1. Executive Summary
2. Key Findings
3. Recommendations (if applicable)"""

        elif report_type == "comparison":
            prompt = f"""Compare these documents and generate a comparison report:

{docs_summary}

Highlight similarities, differences, and notable points."""

        else:
            prompt = f"""Analyze these documents and generate a report:

{docs_summary}

Provide insights, patterns, and key takeaways."""

        report = self.ask_ai(prompt)

        report_title = title or f"Report - {datetime.now().strftime('%Y-%m-%d')}"

        return {
            "status": "success",
            "title": report_title,
            "report": report,
            "documents_analyzed": len(documents),
            "report_type": report_type
        }

    def analyze_document(self, file_path: Optional[str] = None,
                        text: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Perform deep analysis of a document.

        Args:
            file_path: Path to document
            text: Raw text
        """
        if file_path:
            content, word_count = self._read_document(file_path)
            source = file_path
        elif text:
            content = text
            word_count = len(text.split())
            source = "text_input"
        else:
            return {"status": "error", "message": "No document or text provided"}

        prompt = f"""Analyze this document thoroughly:

{content[:4000]}

Provide:
1. Document type and purpose
2. Main topics covered
3. Tone and style
4. Key entities mentioned (people, organizations, places)
5. Any action items or next steps implied
6. Overall assessment"""

        analysis = self.ask_ai(prompt)

        return {
            "status": "success",
            "analysis": analysis,
            "source": source,
            "word_count": word_count,
            "analyzed_at": datetime.now().isoformat()
        }

    def handle_custom_task(self, task: str, **kwargs) -> Dict[str, Any]:
        """Handle a custom document processing task using AI."""
        prompt = f"""You are a document processing assistant. The user wants to: {task}

Available actions:
- Summarize documents
- Extract specific information
- Auto-file documents to folders
- Generate reports
- Analyze document content

Explain what you would do to help with this request."""

        response = self.ask_ai(prompt)

        return {
            "status": "success",
            "task": task,
            "ai_response": response
        }
