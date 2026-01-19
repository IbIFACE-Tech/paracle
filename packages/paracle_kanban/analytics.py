"""Kanban analytics and metrics.

This module provides advanced analytics for Kanban boards,
including velocity, cycle time, burndown/burnup, and forecasting.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from paracle_kanban.task import Task, TaskStatus


class KanbanAnalytics:
    """Advanced analytics for Kanban boards."""

    def __init__(self, tasks: list[Task]) -> None:
        """Initialize analytics with task list.

        Args:
            tasks: Tasks to analyze
        """
        self.tasks = tasks

    def velocity_metrics(self, days: int = 30) -> dict[str, Any]:
        """Calculate velocity metrics.

        Args:
            days: Number of days to analyze

        Returns:
            Velocity metrics
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(days=days)

        completed = [
            t for t in self.tasks if t.completed_at and t.completed_at >= cutoff
        ]

        total_story_points = sum(t.story_points for t in completed if t.story_points)
        total_tasks = len(completed)
        avg_cycle_time = self._avg_cycle_time(completed)

        return {
            "period_days": days,
            "tasks_completed": total_tasks,
            "story_points_completed": total_story_points,
            "tasks_per_day": total_tasks / days if days > 0 else 0,
            "story_points_per_day": (total_story_points / days if days > 0 else 0),
            "avg_cycle_time_hours": avg_cycle_time,
        }

    def _avg_cycle_time(self, tasks: list[Task]) -> float:
        """Calculate average cycle time for tasks.

        Args:
            tasks: Tasks to analyze

        Returns:
            Average cycle time in hours
        """
        cycle_times = [t.cycle_time() for t in tasks if t.cycle_time()]
        return sum(cycle_times) / len(cycle_times) if cycle_times else 0

    def throughput(self, days: int = 30, group_by: str = "day") -> dict[str, int]:
        """Calculate throughput over time.

        Args:
            days: Number of days to analyze
            group_by: Grouping period (day, week, month)

        Returns:
            Throughput by period
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(days=days)

        completed = [
            t for t in self.tasks if t.completed_at and t.completed_at >= cutoff
        ]

        throughput: dict[str, int] = {}

        for task in completed:
            if not task.completed_at:
                continue

            if group_by == "day":
                key = task.completed_at.strftime("%Y-%m-%d")
            elif group_by == "week":
                key = task.completed_at.strftime("%Y-W%W")
            elif group_by == "month":
                key = task.completed_at.strftime("%Y-%m")
            else:
                key = task.completed_at.strftime("%Y-%m-%d")

            throughput[key] = throughput.get(key, 0) + 1

        return throughput

    def burndown_data(self, sprint_id: str | None = None) -> dict[str, Any]:
        """Generate burndown chart data.

        Args:
            sprint_id: Sprint to analyze (all tasks if None)

        Returns:
            Burndown chart data
        """
        tasks = self.tasks
        if sprint_id:
            tasks = [t for t in tasks if t.sprint_id == sprint_id]

        total_points = sum(t.story_points for t in tasks if t.story_points)
        remaining_points = sum(
            t.story_points for t in tasks if t.story_points and not t.is_complete()
        )

        # Group by completion date
        completed_by_date: dict[str, int] = {}
        for task in tasks:
            if task.completed_at and task.story_points:
                date_key = task.completed_at.strftime("%Y-%m-%d")
                completed_by_date[date_key] = (
                    completed_by_date.get(date_key, 0) + task.story_points
                )

        return {
            "total_story_points": total_points,
            "remaining_story_points": remaining_points,
            "completed_story_points": total_points - remaining_points,
            "completion_percentage": (
                (total_points - remaining_points) / total_points * 100
                if total_points > 0
                else 0
            ),
            "completed_by_date": completed_by_date,
        }

    def cumulative_flow(self, days: int = 30) -> dict[str, dict[str, int]]:
        """Generate cumulative flow diagram data.

        Args:
            days: Number of days to analyze

        Returns:
            CFD data by date and status
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(days=days)

        # This is a simplified version - real CFD needs historical data
        cfd: dict[str, dict[str, int]] = {}

        # Group tasks by status
        for task in self.tasks:
            if task.created_at < cutoff:
                continue

            date_key = task.created_at.strftime("%Y-%m-%d")
            status = task.status.value

            if date_key not in cfd:
                cfd[date_key] = {}

            cfd[date_key][status] = cfd[date_key].get(status, 0) + 1

        return cfd

    def lead_time_distribution(self) -> dict[str, Any]:
        """Analyze lead time distribution.

        Returns:
            Lead time statistics
        """
        completed = [t for t in self.tasks if t.is_complete() and t.lead_time()]

        if not completed:
            return {
                "count": 0,
                "min": 0,
                "max": 0,
                "avg": 0,
                "median": 0,
                "p50": 0,
                "p85": 0,
                "p95": 0,
            }

        lead_times = sorted([t.lead_time() for t in completed if t.lead_time()])
        count = len(lead_times)

        return {
            "count": count,
            "min": min(lead_times),
            "max": max(lead_times),
            "avg": sum(lead_times) / count,
            "median": lead_times[count // 2],
            "p50": lead_times[int(count * 0.5)],
            "p85": lead_times[int(count * 0.85)],
            "p95": lead_times[int(count * 0.95)],
        }

    def bottleneck_analysis(self) -> dict[str, Any]:
        """Identify bottlenecks in the workflow.

        Returns:
            Bottleneck analysis
        """
        # Count tasks by status
        by_status: dict[TaskStatus, list[Task]] = {}
        for task in self.tasks:
            if not task.is_complete():
                if task.status not in by_status:
                    by_status[task.status] = []
                by_status[task.status].append(task)

        # Identify columns with most tasks
        bottlenecks = []
        for status, tasks in by_status.items():
            if len(tasks) > 5:  # Arbitrary threshold
                avg_time_in_status = self._avg_time_in_status(tasks, status)
                bottlenecks.append(
                    {
                        "status": status.value,
                        "task_count": len(tasks),
                        "avg_time_hours": avg_time_in_status,
                        "tasks": [t.id for t in tasks[:5]],  # Top 5
                    }
                )

        return {
            "bottlenecks": sorted(
                bottlenecks, key=lambda x: x["task_count"], reverse=True
            ),
            "total_wip": sum(len(tasks) for tasks in by_status.values()),
        }

    def _avg_time_in_status(self, tasks: list[Task], status: TaskStatus) -> float:
        """Calculate average time tasks spend in a status.

        Args:
            tasks: Tasks to analyze
            status: Status to check

        Returns:
            Average time in hours
        """
        # Simplified - would need status change history
        now = datetime.utcnow()
        times = []

        for task in tasks:
            if task.status == status:
                if status == TaskStatus.IN_PROGRESS and task.started_at:
                    time_in_status = (now - task.started_at).total_seconds() / 3600
                    times.append(time_in_status)
                elif task.updated_at:
                    time_in_status = (now - task.updated_at).total_seconds() / 3600
                    times.append(time_in_status)

        return sum(times) / len(times) if times else 0

    def forecast(
        self, remaining_story_points: int, days_history: int = 30
    ) -> dict[str, Any]:
        """Forecast completion based on velocity.

        Args:
            remaining_story_points: Story points remaining
            days_history: Days of history to use for velocity

        Returns:
            Forecast data
        """
        velocity = self.velocity_metrics(days=days_history)
        points_per_day = velocity["story_points_per_day"]

        if points_per_day == 0:
            return {
                "remaining_story_points": remaining_story_points,
                "estimated_days": None,
                "estimated_completion_date": None,
                "confidence": "low",
            }

        estimated_days = remaining_story_points / points_per_day
        completion_date = datetime.utcnow() + timedelta(days=estimated_days)

        return {
            "remaining_story_points": remaining_story_points,
            "velocity_points_per_day": points_per_day,
            "estimated_days": estimated_days,
            "estimated_completion_date": completion_date.strftime("%Y-%m-%d"),
            "confidence": "medium" if days_history >= 14 else "low",
        }
