#!/usr/bin/env python3
"""
Agent Action Logger

Utility pour logger automatiquement les actions des agents dans .parac/memory/logs/
"""

from datetime import datetime
from pathlib import Path
from typing import Literal

ActionType = Literal[
    "IMPLEMENTATION",
    "TEST",
    "REVIEW",
    "DOCUMENTATION",
    "DECISION",
    "PLANNING",
    "REFACTORING",
    "BUGFIX",
    "UPDATE",
]

AgentType = Literal[
    "PMAgent",
    "ArchitectAgent",
    "CoderAgent",
    "TesterAgent",
    "ReviewerAgent",
    "DocumenterAgent",
    "SystemAgent",
]


class AgentLogger:
    """Logger pour les actions d'agents"""

    def __init__(self, parac_dir: Path | None = None):
        if parac_dir is None:
            # Chercher le .parac dans le répertoire courant ou parent
            current = Path.cwd()
            while current != current.parent:
                if (current / ".parac").exists():
                    parac_dir = current / ".parac"
                    break
                current = current.parent
            else:
                raise FileNotFoundError("Cannot find .parac directory")

        self.parac_dir = parac_dir
        self.logs_dir = parac_dir / "memory" / "logs"
        self.actions_log = self.logs_dir / "agent_actions.log"
        self.decisions_log = self.logs_dir / "decisions.log"

        # Créer les dossiers si nécessaire
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def log_action(
        self,
        agent: AgentType,
        action: ActionType,
        description: str,
        timestamp: datetime | None = None,
    ) -> None:
        """
        Log une action d'agent

        Args:
            agent: Type d'agent (PMAgent, CoderAgent, etc.)
            action: Type d'action (IMPLEMENTATION, TEST, etc.)
            description: Description de l'action
            timestamp: Timestamp (par défaut: maintenant)
        """
        if timestamp is None:
            timestamp = datetime.now()

        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp_str}] [{agent}] [{action}] {description}\n"

        # Ajouter au log principal
        with open(self.actions_log, "a", encoding="utf-8") as f:
            f.write(log_entry)

        print(f"✓ Logged: {log_entry.strip()}")

    def log_decision(
        self,
        agent: AgentType,
        decision: str,
        rationale: str,
        impact: str,
        timestamp: datetime | None = None,
    ) -> None:
        """
        Log une décision importante

        Args:
            agent: Type d'agent
            decision: Description de la décision
            rationale: Justification
            impact: Impact attendu
            timestamp: Timestamp (par défaut: maintenant)
        """
        if timestamp is None:
            timestamp = datetime.now()

        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp_str}] [{agent}] [DECISION] {decision} | {rationale} | {impact}\n"

        # Ajouter au log de décisions
        with open(self.decisions_log, "a", encoding="utf-8") as f:
            f.write(log_entry)

        # Aussi dans le log principal
        self.log_action(agent, "DECISION", decision, timestamp)

        print(f"✓ Decision logged: {decision}")

    def get_recent_actions(self, count: int = 10) -> list[str]:
        """Récupère les N dernières actions"""
        if not self.actions_log.exists():
            return []

        with open(self.actions_log, encoding="utf-8") as f:
            lines = f.readlines()

        return lines[-count:]

    def get_agent_actions(self, agent: AgentType) -> list[str]:
        """Récupère toutes les actions d'un agent spécifique"""
        if not self.actions_log.exists():
            return []

        with open(self.actions_log, encoding="utf-8") as f:
            lines = f.readlines()

        return [line for line in lines if f"[{agent}]" in line]


# CLI usage
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Log agent actions")
    parser.add_argument("agent", help="Agent name (e.g., CoderAgent)")
    parser.add_argument("action", help="Action type (e.g., IMPLEMENTATION)")
    parser.add_argument("description", help="Action description")
    parser.add_argument(
        "--decision",
        action="store_true",
        help="Log as decision (requires --rationale and --impact)",
    )
    parser.add_argument("--rationale", help="Decision rationale")
    parser.add_argument("--impact", help="Decision impact")

    args = parser.parse_args()

    logger = AgentLogger()

    if args.decision:
        if not args.rationale or not args.impact:
            print("Error: --decision requires --rationale and --impact")
            exit(1)
        logger.log_decision(args.agent, args.description, args.rationale, args.impact)
    else:
        logger.log_action(args.agent, args.action, args.description)
