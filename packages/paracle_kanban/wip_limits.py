"""WIP (Work In Progress) limit validation.

This module provides WIP limit enforcement for Kanban columns,
helping teams maintain lean workflows and prevent bottlenecks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from paracle_kanban.board import Board
    from paracle_kanban.task import Task, TaskStatus


class WIPLimitError(Exception):
    """Raised when WIP limit would be exceeded."""

    pass


class WIPLimitValidator:
    """Validates WIP limits for board columns."""

    def __init__(self, board: Board) -> None:
        """Initialize validator with board configuration.

        Args:
            board: Board with WIP limits configured
        """
        self.board = board

    def check_wip_limit(
        self,
        status: TaskStatus,
        tasks: list[Task],
        raise_on_exceed: bool = False,
    ) -> tuple[bool, int, int]:
        """Check if adding a task would exceed WIP limit.

        Args:
            status: Column/status to check
            tasks: Current tasks in the column
            raise_on_exceed: Raise exception if limit exceeded

        Returns:
            Tuple of (within_limit, current_count, limit)

        Raises:
            WIPLimitError: If raise_on_exceed=True and limit exceeded
        """
        # Get WIP limit for this status
        status_str = status.value if hasattr(status, "value") else str(status)
        limit = self.board.wip_limits.get(status_str)

        if limit is None:
            # No limit configured
            return True, len(tasks), -1

        current_count = len(tasks)
        within_limit = current_count < limit

        if not within_limit and raise_on_exceed:
            raise WIPLimitError(
                f"WIP limit exceeded for {status_str}: "
                f"{current_count + 1} > {limit}"
            )

        return within_limit, current_count, limit

    def get_wip_status(self, tasks: dict[str, list[Task]]) -> dict[str, dict]:
        """Get WIP status for all columns.

        Args:
            tasks: Tasks grouped by status

        Returns:
            Dictionary with WIP status per column
        """
        status_info = {}

        for status_str, task_list in tasks.items():
            limit = self.board.wip_limits.get(status_str)
            current = len(task_list)

            status_info[status_str] = {
                "current": current,
                "limit": limit,
                "within_limit": limit is None or current <= limit,
                "percentage": ((current / limit * 100) if limit else 0),
            }

        return status_info

    def suggest_wip_limits(
        self, tasks: dict[str, list[Task]], team_size: int = 5
    ) -> dict[str, int]:
        """Suggest WIP limits based on current workload and team size.

        Uses common Kanban practices:
        - TODO: 2x team size
        - IN_PROGRESS: 1.5x team size
        - REVIEW: 1x team size
        - Other: 1.5x team size

        Args:
            tasks: Current tasks by status
            team_size: Number of team members

        Returns:
            Suggested WIP limits per status
        """
        suggestions = {}

        for status_str in tasks.keys():
            if status_str in ["todo", "backlog"]:
                suggestions[status_str] = team_size * 2
            elif status_str == "in_progress":
                suggestions[status_str] = int(team_size * 1.5)
            elif status_str == "review":
                suggestions[status_str] = team_size
            elif status_str in ["done", "archived"]:
                # No limit for completed items
                continue
            else:
                suggestions[status_str] = int(team_size * 1.5)

        return suggestions

    def get_overloaded_columns(self, tasks: dict[str, list[Task]]) -> list[dict]:
        """Identify columns that are over WIP limit.

        Args:
            tasks: Tasks grouped by status

        Returns:
            List of overloaded columns with details
        """
        overloaded = []

        for status_str, task_list in tasks.items():
            limit = self.board.wip_limits.get(status_str)
            if limit is None:
                continue

            current = len(task_list)
            if current > limit:
                overloaded.append(
                    {
                        "status": status_str,
                        "current": current,
                        "limit": limit,
                        "excess": current - limit,
                        "percentage": (current / limit * 100),
                    }
                )

        return overloaded

    def can_move_task(
        self,
        task: Task,
        new_status: TaskStatus,
        tasks_in_status: list[Task],
    ) -> tuple[bool, str]:
        """Check if task can be moved to new status.

        Args:
            task: Task to move
            new_status: Target status
            tasks_in_status: Current tasks in target status

        Returns:
            Tuple of (can_move, reason)
        """
        status_str = (
            new_status.value if hasattr(new_status, "value") else str(new_status)
        )
        limit = self.board.wip_limits.get(status_str)

        if limit is None:
            return True, "No WIP limit configured"

        current_count = len(tasks_in_status)

        # Check if task is already in this status
        if task.status == new_status:
            return True, "Task already in this status"

        # Check if moving would exceed limit
        if current_count >= limit:
            return False, (
                f"WIP limit would be exceeded: " f"{current_count + 1} > {limit}"
            )

        return True, f"Within limit: {current_count + 1} <= {limit}"
