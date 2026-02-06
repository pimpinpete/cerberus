#!/usr/bin/env python3
"""
Base Agent Class for Cerberus
All agents inherit from this class.
"""

import os
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

# Add ai-orchestrator to path
AI_ORCHESTRATOR_PATH = Path.home() / "ai-orchestrator"
sys.path.insert(0, str(AI_ORCHESTRATOR_PATH))

from core import (
    get_router, select_model,
    get_observer, trace, log_error,
    log_action
)


class CerberusAgent(ABC):
    """
    Base class for all Cerberus agents.

    Provides:
    - AI model access via smart router
    - Logging and observability
    - Configuration management
    - Execution lifecycle
    """

    def __init__(self, config, cerberus_instance):
        """
        Initialize agent.

        Args:
            config: AgentConfig object
            cerberus_instance: Reference to parent Cerberus instance
        """
        self.config = config
        self.cerberus = cerberus_instance
        self.name = config.name
        self.settings = config.settings
        self.router = get_router()
        self.observer = get_observer()

        # Execution state
        self.last_run: Optional[datetime] = None
        self.run_count: int = 0
        self.errors: List[Dict[str, Any]] = []

    @abstractmethod
    def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        Execute the agent's main task.

        Args:
            task: Description of task to perform
            **kwargs: Additional parameters

        Returns:
            Result dictionary with status and output
        """
        pass

    def ask_ai(self, prompt: str, context: Optional[str] = None) -> str:
        """
        Ask the AI for help with a task.

        Args:
            prompt: The question/task for the AI
            context: Optional additional context

        Returns:
            AI response string
        """
        full_prompt = prompt
        if context:
            full_prompt = f"Context: {context}\n\nTask: {prompt}"

        model_config = select_model(full_prompt)
        model_name = model_config.name if hasattr(model_config, 'name') else str(model_config)
        try:
            log_action(f"Agent {self.name} querying AI", {"model": model_name, "prompt_length": len(full_prompt)})
        except Exception:
            pass  # Ignore logging errors

        # Use Claude CLI for actual inference
        import subprocess
        result = subprocess.run(
            ["claude", "-p", full_prompt],
            capture_output=True, text=True, timeout=60
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            log_error(f"AI query failed: {result.stderr}")
            return f"Error: {result.stderr}"

    def log(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log an action for observability."""
        try:
            log_action(f"[{self.name}] {message}", data or {})
        except Exception:
            pass  # Ignore logging errors

    def error(self, message: str, exception: Optional[Exception] = None):
        """Log an error."""
        error_data = {"agent": self.name, "message": message}
        if exception:
            error_data["exception"] = str(exception)

        self.errors.append({
            "timestamp": datetime.now().isoformat(),
            **error_data
        })
        log_error(message, error_data)

    def _pre_execute(self, task: str):
        """Called before execute."""
        self.last_run = datetime.now()
        self.run_count += 1
        self.log(f"Starting task: {task[:50]}...")

    def _post_execute(self, result: Dict[str, Any]):
        """Called after execute."""
        status = result.get("status", "unknown")
        self.log(f"Task completed with status: {status}")

    def run(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        Full execution lifecycle wrapper.

        Handles pre/post hooks, error catching.
        """
        try:
            self._pre_execute(task)
            result = self.execute(task, **kwargs)
            self._post_execute(result)
            return result
        except Exception as e:
            self.error(f"Execution failed: {str(e)}", e)
            return {
                "status": "error",
                "message": str(e),
                "agent": self.name
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            "name": self.name,
            "type": self.config.type.value,
            "run_count": self.run_count,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "error_count": len(self.errors),
            "enabled": self.config.enabled
        }
