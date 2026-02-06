#!/usr/bin/env python3
"""
Cerberus: AI Agent Platform for Business Automation
The three-headed guardian of your back-office operations.

Built on top of ai-orchestrator for maximum power with minimal code.
"""

import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

# Add ai-orchestrator to path
AI_ORCHESTRATOR_PATH = Path.home() / "ai-orchestrator"
sys.path.insert(0, str(AI_ORCHESTRATOR_PATH))

# Import from ai-orchestrator core
from core import (
    get_router, select_model,
    get_memory, remember, recall, log_action,
    get_observer, trace, log_error,
    get_integrations, notify,
    get_apex_engine,
    get_domain_router
)
from core.smart_router import SmartModelRouter
from core.apex_engine import APEXEngine
from tools.mac_apps_api import MailAPI, CalendarAPI, MessagesAPI


class AgentType(Enum):
    EMAIL_MANAGER = "email_manager"
    DATA_ENTRY = "data_entry"
    DOC_PROCESSOR = "doc_processor"
    CUSTOM = "custom"


@dataclass
class AgentConfig:
    """Configuration for a Cerberus agent."""
    name: str
    type: AgentType
    enabled: bool = True
    config_path: Optional[Path] = None
    settings: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> "AgentConfig":
        """Load agent config from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(
            name=data.get("name", path.stem),
            type=AgentType(data.get("type", "custom")),
            enabled=data.get("enabled", True),
            config_path=path,
            settings=data.get("settings", {})
        )


@dataclass
class Client:
    """Client information for tracking projects."""
    id: str
    name: str
    email: str
    projects: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class Cerberus:
    """
    Main Cerberus platform class.
    Orchestrates AI agents for business automation.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.base_path = Path.home() / "cerberus"
        self.agents_path = self.base_path / "agents"
        self.config_path = config_path or self.base_path / "config.yaml"

        # Initialize ai-orchestrator components
        self.router = get_router()
        self.apex = get_apex_engine()
        self.memory = get_memory()
        self.observer = get_observer()

        # Load agents
        self.agents: Dict[str, AgentConfig] = {}
        self._load_agents()

        # Initialize APIs
        self.mail = MailAPI()
        self.calendar = CalendarAPI()
        self.messages = MessagesAPI()

        print("🐕 Cerberus initialized - 3 heads ready to guard your operations")

    def _load_agents(self):
        """Load all agent configurations from YAML files."""
        if not self.agents_path.exists():
            return

        for yaml_file in self.agents_path.glob("*.yaml"):
            try:
                config = AgentConfig.from_yaml(yaml_file)
                self.agents[config.name] = config
                print(f"  ✓ Loaded agent: {config.name} ({config.type.value})")
            except Exception as e:
                print(f"  ✗ Failed to load {yaml_file}: {e}")

    def run_agent(self, agent_name: str, task: str, **kwargs) -> Dict[str, Any]:
        """
        Run a specific agent with a task.

        Args:
            agent_name: Name of the agent to run
            task: The task to perform
            **kwargs: Additional parameters for the agent

        Returns:
            Result dictionary with status and output
        """
        if agent_name not in self.agents:
            return {"status": "error", "message": f"Agent '{agent_name}' not found"}

        agent_config = self.agents[agent_name]

        if not agent_config.enabled:
            return {"status": "error", "message": f"Agent '{agent_name}' is disabled"}

        # Log the action (convert to JSON-safe)
        try:
            log_action(f"Running agent: {agent_name}", {"task": task, "agent": agent_name})
        except Exception:
            pass  # Ignore logging errors

        # Route to appropriate agent type
        if agent_config.type == AgentType.EMAIL_MANAGER:
            return self._run_email_agent(agent_config, task, **kwargs)
        elif agent_config.type == AgentType.DATA_ENTRY:
            return self._run_data_entry_agent(agent_config, task, **kwargs)
        elif agent_config.type == AgentType.DOC_PROCESSOR:
            return self._run_doc_processor_agent(agent_config, task, **kwargs)
        else:
            return self._run_custom_agent(agent_config, task, **kwargs)

    def _run_email_agent(self, config: AgentConfig, task: str, **kwargs) -> Dict[str, Any]:
        """Run email management agent."""
        from agents.email_manager import EmailManagerAgent
        agent = EmailManagerAgent(config, self)
        return agent.execute(task, **kwargs)

    def _run_data_entry_agent(self, config: AgentConfig, task: str, **kwargs) -> Dict[str, Any]:
        """Run data entry agent."""
        from agents.data_entry import DataEntryAgent
        agent = DataEntryAgent(config, self)
        return agent.execute(task, **kwargs)

    def _run_doc_processor_agent(self, config: AgentConfig, task: str, **kwargs) -> Dict[str, Any]:
        """Run document processor agent."""
        from agents.doc_processor import DocProcessorAgent
        agent = DocProcessorAgent(config, self)
        return agent.execute(task, **kwargs)

    def _run_custom_agent(self, config: AgentConfig, task: str, **kwargs) -> Dict[str, Any]:
        """Run custom agent using APEX engine."""
        # Use APEX for complex custom tasks
        result = self.apex.execute(task, context=config.settings)
        return {"status": "success", "output": result}

    def ask(self, question: str, model: Optional[str] = None) -> str:
        """
        Ask the AI a question using the smart router.

        Args:
            question: The question to ask
            model: Optional specific model to use

        Returns:
            The AI's response
        """
        selected_model = model or select_model(question)
        # Here we'd make the actual API call
        # For now, return a placeholder
        return f"[Would query {selected_model} with: {question}]"

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents."""
        return [
            {
                "name": name,
                "type": config.type.value,
                "enabled": config.enabled,
                "settings": config.settings
            }
            for name, config in self.agents.items()
        ]

    def status(self) -> Dict[str, Any]:
        """Get current Cerberus status."""
        return {
            "status": "running",
            "agents_loaded": len(self.agents),
            "agents": self.list_agents(),
            "ai_orchestrator": "connected",
            "timestamp": datetime.now().isoformat()
        }


def main():
    """CLI interface for Cerberus."""
    import argparse

    parser = argparse.ArgumentParser(description="Cerberus: AI Agent Platform")
    parser.add_argument("command", nargs="?", default="status",
                       choices=["status", "list", "run", "demo"],
                       help="Command to run")
    parser.add_argument("--agent", "-a", help="Agent name for run command")
    parser.add_argument("--task", "-t", help="Task for the agent")

    args = parser.parse_args()

    cerberus = Cerberus()

    if args.command == "status":
        status = cerberus.status()
        print(json.dumps(status, indent=2))

    elif args.command == "list":
        agents = cerberus.list_agents()
        print("\n📋 Registered Agents:")
        for agent in agents:
            status = "✓" if agent["enabled"] else "✗"
            print(f"  {status} {agent['name']} ({agent['type']})")

    elif args.command == "run":
        if not args.agent or not args.task:
            print("Error: --agent and --task required for run command")
            sys.exit(1)
        result = cerberus.run_agent(args.agent, args.task)
        print(json.dumps(result, indent=2))

    elif args.command == "demo":
        print("\n🎬 Cerberus Demo Mode")
        print("=" * 40)

        # Show available agents
        agents = cerberus.list_agents()
        if agents:
            print("\nAvailable agents:")
            for agent in agents:
                print(f"  • {agent['name']}: {agent['type']}")
        else:
            print("\nNo agents configured yet.")
            print("Create YAML configs in ~/cerberus/agents/")


if __name__ == "__main__":
    main()
