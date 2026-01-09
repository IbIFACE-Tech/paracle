"""Project management tools for PM agent."""

import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from paracle_tools.builtin.base import BaseTool

logger = logging.getLogger("paracle.tools.pm")


class TaskTrackingTool(BaseTool):
    """Track tasks, issues, and project progress.

    Supports:
    - Task creation and updates
    - Status tracking
    - Priority management
    - Progress reporting
    """

    def __init__(self):
        super().__init__(
            name="task_tracking",
            description="Track and manage tasks",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform",
                        "enum": ["create", "update", "list", "report"],
                    },
                    "title": {
                        "type": "string",
                        "description": "Task title (for create action)",
                    },
                    "description": {
                        "type": "string",
                        "description": "Task description (for create action)",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Task priority (for create action)",
                        "enum": ["low", "medium", "high", "critical"],
                        "default": "medium",
                    },
                    "task_id": {
                        "type": "string",
                        "description": "Task ID (for update action)",
                    },
                    "status": {
                        "type": "string",
                        "description": "Task status (for update/list actions)",
                        "enum": ["todo", "in_progress", "done", "blocked"],
                    },
                    "period": {
                        "type": "string",
                        "description": "Report period (for report action)",
                        "enum": ["day", "week", "month"],
                        "default": "week",
                    },
                },
                "required": ["action"],
            },
        )

    async def _execute(self, action: str, **kwargs) -> dict[str, Any]:
        """Perform task tracking action.

        Args:
            action: Action to perform (create, update, list, report)
            **kwargs: Action-specific parameters

        Returns:
            Task tracking results
        """
        if action == "create":
            return await self._create_task(**kwargs)
        elif action == "update":
            return await self._update_task(**kwargs)
        elif action == "list":
            return await self._list_tasks(**kwargs)
        elif action == "report":
            return await self._generate_report(**kwargs)
        else:
            return {"error": f"Unsupported action: {action}"}

    async def _create_task(
        self, title: str, description: str = "", priority: str = "medium", **kwargs
    ) -> dict[str, Any]:
        """Create a new task."""
        task = {
            "id": f"TASK-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "title": title,
            "description": description,
            "priority": priority,
            "status": "todo",
            "created": datetime.now().isoformat(),
        }

        return {
            "action": "create",
            "task": task,
            "message": f"Task created: {task['id']}",
        }

    async def _update_task(self, task_id: str, **updates) -> dict[str, Any]:
        """Update an existing task."""
        return {
            "action": "update",
            "task_id": task_id,
            "updates": updates,
            "message": f"Task {task_id} updated",
        }

    async def _list_tasks(
        self, status: str = None, priority: str = None, **kwargs
    ) -> dict[str, Any]:
        """List tasks with optional filters."""
        # In real implementation, would read from .parac/memory/context/current_state.yaml
        # or a task tracking file

        filters = {}
        if status:
            filters["status"] = status
        if priority:
            filters["priority"] = priority

        return {
            "action": "list",
            "filters": filters,
            "tasks": [],  # Would return actual tasks
            "message": "Task list retrieved",
        }

    async def _generate_report(self, period: str = "week", **kwargs) -> dict[str, Any]:
        """Generate progress report."""
        return {
            "action": "report",
            "period": period,
            "summary": {
                "completed": 0,
                "in_progress": 0,
                "blocked": 0,
                "total": 0,
            },
            "message": f"{period.title()} report generated",
        }


class MilestoneManagementTool(BaseTool):
    """Manage project milestones and roadmap.

    Features:
    - Milestone tracking
    - Progress calculation
    - Roadmap updates
    - Phase management
    """

    def __init__(self):
        super().__init__(
            name="milestone_management",
            description="Manage project milestones and roadmap",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform",
                        "enum": ["check", "update", "sync", "report"],
                    },
                    "milestone_id": {
                        "type": "string",
                        "description": "Milestone ID (for update action)",
                    },
                    "status": {
                        "type": "string",
                        "description": "Milestone status (for update action)",
                        "enum": ["planned", "in_progress", "completed", "delayed"],
                    },
                },
                "required": ["action"],
            },
        )

    async def _execute(self, action: str, **kwargs) -> dict[str, Any]:
        """Perform milestone management action.

        Args:
            action: Action to perform (check, update, sync, report)
            **kwargs: Action-specific parameters

        Returns:
            Milestone management results
        """
        if action == "check":
            return await self._check_progress(**kwargs)
        elif action == "update":
            return await self._update_milestone(**kwargs)
        elif action == "sync":
            return await self._sync_roadmap(**kwargs)
        elif action == "report":
            return await self._milestone_report(**kwargs)
        else:
            return {"error": f"Unsupported action: {action}"}

    async def _check_progress(self, **kwargs) -> dict[str, Any]:
        """Check current progress against roadmap."""
        try:
            # Read current state
            state_path = Path(".parac/memory/context/current_state.yaml")
            if state_path.exists():
                with open(state_path, encoding="utf-8") as f:
                    state = yaml.safe_load(f)

                return {
                    "action": "check",
                    "current_phase": state.get("current_phase", {}),
                    "progress": state.get("current_phase", {}).get("progress", 0),
                    "status": state.get("current_phase", {}).get("status", "unknown"),
                }
            else:
                return {"error": "current_state.yaml not found"}
        except Exception as e:
            return {"error": str(e)}

    async def _update_milestone(
        self, milestone_id: str, status: str, **kwargs
    ) -> dict[str, Any]:
        """Update milestone status."""
        return {
            "action": "update",
            "milestone_id": milestone_id,
            "status": status,
            "message": f"Milestone {milestone_id} updated to {status}",
        }

    async def _sync_roadmap(self, **kwargs) -> dict[str, Any]:
        """Sync roadmap with current state."""
        try:
            # Run paracle sync command
            result = subprocess.run(
                ["paracle", "sync", "--roadmap"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            return {
                "action": "sync",
                "success": result.returncode == 0,
                "output": result.stdout,
            }
        except FileNotFoundError:
            return {"error": "paracle command not found"}
        except Exception as e:
            return {"error": str(e)}

    async def _milestone_report(self, **kwargs) -> dict[str, Any]:
        """Generate milestone report."""
        try:
            roadmap_path = Path(".parac/roadmap/roadmap.yaml")
            if roadmap_path.exists():
                with open(roadmap_path, encoding="utf-8") as f:
                    roadmap = yaml.safe_load(f)

                phases = roadmap.get("phases", [])

                return {
                    "action": "report",
                    "total_phases": len(phases),
                    "phases": phases,
                }
            else:
                return {"error": "roadmap.yaml not found"}
        except Exception as e:
            return {"error": str(e)}


class TeamCoordinationTool(BaseTool):
    """Coordinate team activities and communication.

    Features:
    - Agent coordination
    - Workflow orchestration
    - Status updates
    - Team notifications
    """

    def __init__(self):
        super().__init__(
            name="team_coordination",
            description="Coordinate team activities and assignments",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform",
                        "enum": ["assign", "notify", "status", "coordinate"],
                    },
                    "task_id": {
                        "type": "string",
                        "description": "Task ID (for assign action)",
                    },
                    "agent": {
                        "type": "string",
                        "description": "Agent to assign task to (for assign action)",
                    },
                    "recipient": {
                        "type": "string",
                        "description": "Notification recipient (for notify action)",
                    },
                    "message": {
                        "type": "string",
                        "description": "Notification message (for notify action)",
                    },
                    "workflow_id": {
                        "type": "string",
                        "description": "Workflow ID (for coordinate action)",
                    },
                },
                "required": ["action"],
            },
        )

    async def _execute(self, action: str, **kwargs) -> dict[str, Any]:
        """Perform team coordination action.

        Args:
            action: Action to perform (assign, notify, status, coordinate)
            **kwargs: Action-specific parameters

        Returns:
            Team coordination results
        """
        if action == "assign":
            return await self._assign_task(**kwargs)
        elif action == "notify":
            return await self._send_notification(**kwargs)
        elif action == "status":
            return await self._get_team_status(**kwargs)
        elif action == "coordinate":
            return await self._coordinate_workflow(**kwargs)
        else:
            return {"error": f"Unsupported action: {action}"}

    async def _assign_task(self, task_id: str, agent: str, **kwargs) -> dict[str, Any]:
        """Assign task to agent."""
        return {
            "action": "assign",
            "task_id": task_id,
            "agent": agent,
            "message": f"Task {task_id} assigned to {agent}",
        }

    async def _send_notification(
        self, recipient: str, message: str, **kwargs
    ) -> dict[str, Any]:
        """Send notification."""
        return {
            "action": "notify",
            "recipient": recipient,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "status": "sent",
        }

    async def _get_team_status(self, **kwargs) -> dict[str, Any]:
        """Get team status."""
        try:
            # Read agent manifest
            manifest_path = Path(".parac/agents/manifest.yaml")
            if manifest_path.exists():
                with open(manifest_path, encoding="utf-8") as f:
                    manifest = yaml.safe_load(f)

                agents = manifest.get("agents", [])

                return {
                    "action": "status",
                    "total_agents": len(agents),
                    "agents": [
                        {
                            "id": a.get("id"),
                            "name": a.get("name"),
                            "role": a.get("role"),
                        }
                        for a in agents
                    ],
                }
            else:
                return {"error": "manifest.yaml not found"}
        except Exception as e:
            return {"error": str(e)}

    async def _coordinate_workflow(self, workflow_id: str, **kwargs) -> dict[str, Any]:
        """Coordinate workflow execution."""
        return {
            "action": "coordinate",
            "workflow_id": workflow_id,
            "status": "coordinating",
            "message": f"Coordinating workflow {workflow_id}",
        }


# Tool instances
task_tracking = TaskTrackingTool()
milestone_management = MilestoneManagementTool()
team_coordination = TeamCoordinationTool()

__all__ = [
    "TaskTrackingTool",
    "MilestoneManagementTool",
    "TeamCoordinationTool",
    "task_tracking",
    "milestone_management",
    "team_coordination",
]
