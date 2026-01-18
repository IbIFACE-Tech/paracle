"""Task notifications and event system.

This module provides notification functionality for task changes,
enabling real-time updates and integration with external systems.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any

from paracle_domain.models import generate_id
from pydantic import BaseModel, Field


class NotificationChannel(str, Enum):
    """Notification delivery channels."""

    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"
    IN_APP = "in_app"


class NotificationEvent(str, Enum):
    """Task events that trigger notifications."""

    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_DELETED = "task_deleted"
    TASK_ASSIGNED = "task_assigned"
    TASK_UNASSIGNED = "task_unassigned"
    STATUS_CHANGED = "status_changed"
    COMMENT_ADDED = "comment_added"
    DUE_DATE_APPROACHING = "due_date_approaching"
    DUE_DATE_PASSED = "due_date_passed"
    DEPENDENCY_COMPLETED = "dependency_completed"
    TASK_BLOCKED = "task_blocked"
    TASK_UNBLOCKED = "task_unblocked"


class Notification(BaseModel):
    """Notification model.

    Attributes:
        id: Unique notification identifier
        event: Event that triggered notification
        task_id: Task related to notification
        recipient: User/agent to notify
        channel: Delivery channel
        title: Notification title
        message: Notification message
        data: Additional data
        created_at: When notification was created
        sent_at: When notification was sent
        read_at: When notification was read
        status: Delivery status
    """

    id: str = Field(default_factory=lambda: generate_id("notification"))
    event: NotificationEvent
    task_id: str
    recipient: str
    channel: NotificationChannel
    title: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: datetime | None = None
    read_at: datetime | None = None
    status: str = "pending"  # pending, sent, failed, read

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class NotificationRule(BaseModel):
    """Notification rule configuration.

    Attributes:
        id: Unique rule identifier
        name: Rule name
        events: Events to watch
        conditions: Conditions for triggering
        recipients: Who to notify
        channels: How to notify
        enabled: Whether rule is active
    """

    id: str = Field(default_factory=lambda: generate_id("rule"))
    name: str
    events: list[NotificationEvent]
    conditions: dict[str, Any] = Field(default_factory=dict)
    recipients: list[str]
    channels: list[NotificationChannel]
    enabled: bool = True

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class NotificationManager:
    """Manages notifications and event subscriptions."""

    def __init__(self) -> None:
        """Initialize notification manager."""
        self.rules: list[NotificationRule] = []
        self.handlers: dict[str, list[Callable]] = {}
        self.notifications: list[Notification] = []

    def add_rule(self, rule: NotificationRule) -> None:
        """Add notification rule.

        Args:
            rule: Notification rule to add
        """
        self.rules.append(rule)

    def remove_rule(self, rule_id: str) -> None:
        """Remove notification rule.

        Args:
            rule_id: ID of rule to remove
        """
        self.rules = [r for r in self.rules if r.id != rule_id]

    def subscribe(self, event: NotificationEvent, handler: Callable) -> None:
        """Subscribe to an event.

        Args:
            event: Event to subscribe to
            handler: Handler function to call
        """
        if event not in self.handlers:
            self.handlers[event] = []
        self.handlers[event].append(handler)

    def emit(
        self, event: NotificationEvent, task_id: str, data: dict[str, Any]
    ) -> list[Notification]:
        """Emit an event and create notifications.

        Args:
            event: Event that occurred
            task_id: Task ID
            data: Event data

        Returns:
            List of created notifications
        """
        notifications = []

        # Process rules
        for rule in self.rules:
            if not rule.enabled or event not in rule.events:
                continue

            # Check conditions
            if not self._check_conditions(rule.conditions, data):
                continue

            # Create notifications
            for recipient in rule.recipients:
                for channel in rule.channels:
                    notification = Notification(
                        event=event,
                        task_id=task_id,
                        recipient=recipient,
                        channel=channel,
                        title=f"Task {event.value}",
                        message=self._format_message(event, data),
                        data=data,
                    )
                    notifications.append(notification)
                    self.notifications.append(notification)

        # Call handlers
        if event in self.handlers:
            for handler in self.handlers[event]:
                try:
                    handler(event, task_id, data)
                except Exception as e:
                    print(f"Handler error: {e}")

        return notifications

    def _check_conditions(
        self, conditions: dict[str, Any], data: dict[str, Any]
    ) -> bool:
        """Check if conditions are met.

        Args:
            conditions: Conditions to check
            data: Event data

        Returns:
            True if conditions are met, False otherwise
        """
        for key, value in conditions.items():
            if key not in data or data[key] != value:
                return False
        return True

    def _format_message(self, event: NotificationEvent, data: dict[str, Any]) -> str:
        """Format notification message.

        Args:
            event: Event type
            data: Event data

        Returns:
            Formatted message
        """
        templates = {
            NotificationEvent.TASK_CREATED: ("Task '{title}' was created"),
            NotificationEvent.TASK_ASSIGNED: ("Task '{title}' was assigned to you"),
            NotificationEvent.STATUS_CHANGED: (
                "Task '{title}' status changed to {new_status}"
            ),
            NotificationEvent.DUE_DATE_APPROACHING: ("Task '{title}' is due soon"),
        }

        template = templates.get(event, "Task '{title}' was updated")
        return template.format(**data)

    def mark_as_sent(self, notification_id: str) -> None:
        """Mark notification as sent.

        Args:
            notification_id: Notification ID
        """
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.sent_at = datetime.utcnow()
                notification.status = "sent"
                break

    def mark_as_read(self, notification_id: str) -> None:
        """Mark notification as read.

        Args:
            notification_id: Notification ID
        """
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.read_at = datetime.utcnow()
                notification.status = "read"
                break
