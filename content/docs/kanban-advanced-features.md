# Kanban Advanced Features Guide

This guide documents all advanced features added to `paracle_kanban` to make it a powerful project management system.

## Overview

The enhanced Kanban system now includes:

1. **Swimlanes** - Horizontal task grouping
2. **WIP Limits** - Work-in-progress enforcement
3. **Dependencies** - Task dependency management with validation
4. **Comments** - Task comments and activity tracking
5. **Notifications** - Event-based notifications
6. **Templates** - Reusable task patterns
7. **Time Tracking** - Estimated vs actual hours
8. **Custom Fields** - Flexible metadata
9. **Labels** - Visual categorization with colors
10. **Sprints** - Sprint/milestone association
11. **Subtasks** - Parent-child task relationships
12. **Advanced Filtering** - Sophisticated search and sort
13. **Analytics** - Velocity, burndown, forecasting
14. **Recurring Tasks** - Automated task creation

---

## 1. Swimlanes

Swimlanes provide horizontal grouping of tasks, typically by team, project, or feature area.

### Board Configuration

```python
from paracle_kanban import Board

board = Board(
    name="Development Board",
    swimlanes=["Frontend Team", "Backend Team", "Infrastructure"]
)
```

### Assigning Tasks to Swimlanes

```python
from paracle_kanban import Task

task = Task(
    board_id=board.id,
    title="Implement API endpoint",
    swimlane="Backend Team"
)
```

---

## 2. WIP Limits

WIP (Work In Progress) limits prevent bottlenecks by limiting tasks per column.

### Setting WIP Limits

```python
board = Board(
    name="Sprint Board",
    wip_limits={
        "in_progress": 3,    # Max 3 tasks in progress
        "review": 5,         # Max 5 tasks in review
        "todo": 10          # Max 10 tasks ready
    }
)
```

### Validating WIP Limits

```python
from paracle_kanban import WIPLimitValidator, TaskStatus

validator = WIPLimitValidator(board)

# Check if can add task to column
can_move, message = validator.can_move_task(
    task,
    TaskStatus.IN_PROGRESS,
    current_tasks_in_progress
)

if not can_move:
    print(f"Cannot move: {message}")
```

### WIP Status Report

```python
# Get WIP status for all columns
status = validator.get_wip_status(tasks_by_status)

for column, info in status.items():
    print(f"{column}: {info['current']}/{info['limit']}")
    if not info['within_limit']:
        print(f"  ⚠️  OVER LIMIT!")
```

---

## 3. Dependencies

Validate task dependencies and prevent circular references.

### Adding Dependencies

```python
task = Task(
    board_id=board.id,
    title="Implement authentication",
    depends_on=["task_api_design", "task_database_schema"]
)
```

### Validating Dependencies

```python
from paracle_kanban import DependencyValidator, CircularDependencyError

validator = DependencyValidator(all_tasks_dict)

try:
    errors = validator.validate_dependencies(task)
    if errors:
        print("Validation errors:", errors)
except CircularDependencyError as e:
    print(f"Circular dependency: {e}")
```

### Dependency Chain

```python
# Get full dependency chain
chain = validator.get_dependency_chain(task.id)
print("Dependency chain:", " → ".join(chain))

# Check if can complete
can_complete, incomplete = validator.can_complete_task(task.id)
if not can_complete:
    print(f"Blocked by: {incomplete}")
```

---

## 4. Comments & Activity

Track comments and activity history for collaboration.

### Adding Comments

```python
from paracle_kanban import TaskComment

comment = TaskComment(
    task_id=task.id,
    author="coder_agent",
    content="Implementation complete, ready for review",
    mentions=["reviewer_agent"]
)
```

### Threading Comments

```python
reply = TaskComment(
    task_id=task.id,
    author="reviewer_agent",
    content="Looks good, just one minor issue",
    parent_id=comment.id
)
```

### Activity Tracking

```python
from paracle_kanban import TaskActivity

activity = TaskActivity(
    task_id=task.id,
    user="coder_agent",
    action="status_change",
    old_value="in_progress",
    new_value="review",
    details="Moved to review after implementation"
)
```

---

## 5. Notifications

Event-based notification system for task changes.

### Setting Up Notifications

```python
from paracle_kanban import (
    NotificationManager,
    NotificationRule,
    NotificationEvent,
    NotificationChannel
)

manager = NotificationManager()

# Create notification rule
rule = NotificationRule(
    name="High Priority Assignments",
    events=[NotificationEvent.TASK_ASSIGNED],
    conditions={"priority": "critical"},
    recipients=["team_lead", "product_manager"],
    channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK]
)

manager.add_rule(rule)
```

### Emitting Events

```python
# Emit event when task assigned
notifications = manager.emit(
    NotificationEvent.TASK_ASSIGNED,
    task_id=task.id,
    data={
        "title": task.title,
        "assignee": task.assigned_to,
        "priority": task.priority.value
    }
)
```

### Custom Event Handlers

```python
def on_task_completed(event, task_id, data):
    print(f"Task {data['title']} completed!")

manager.subscribe(NotificationEvent.STATUS_CHANGED, on_task_completed)
```

---

## 6. Task Templates

Reusable task patterns for common workflows.

### Using Built-in Templates

```python
from paracle_kanban import TemplateManager

manager = TemplateManager()

# List available templates
templates = manager.list_templates()
for template in templates:
    print(f"{template.name}: {template.description}")

# Create task from template
bug_template = manager.get_template("bug_report")
task = bug_template.create_task(
    board_id=board.id,
    variables={
        "summary": "Login page not loading",
        "description": "Users cannot access login",
        "steps": "1. Navigate to /login\n2. Page shows 500 error",
        "expected": "Login page loads",
        "actual": "500 Internal Server Error",
        "environment": "Chrome 119, Windows 11"
    }
)
```

### Creating Custom Templates

```python
from paracle_kanban import TaskTemplate, TaskType, TaskPriority

template = TaskTemplate(
    name="Security Review",
    title_template="Security: {component}",
    description_template=(
        "## Component\n{component}\n\n"
        "## Security Checklist\n"
        "- Input validation\n"
        "- Authentication\n"
        "- Authorization\n"
        "- Data encryption"
    ),
    task_type=TaskType.CHORE,
    priority=TaskPriority.HIGH,
    estimated_hours=4.0,
    tags=["security", "audit"],
    labels=[{"name": "security", "color": "#ff0000"}],
    category="security"
)

manager.add_template(template)
```

---

## 7. Time Tracking

Track estimated vs actual hours for better planning.

### Setting Estimates

```python
task = Task(
    board_id=board.id,
    title="Implement search feature",
    estimated_hours=8.0,
    actual_hours=0.0
)
```

### Updating Actual Time

```python
task.actual_hours = 6.5  # Completed in 6.5 hours

# Check variance
variance = task.actual_hours - (task.estimated_hours or 0)
if variance > 0:
    print(f"Over estimate by {variance} hours")
```

### Time Metrics

```python
# Get cycle time (started → completed)
cycle_time = task.cycle_time()
print(f"Cycle time: {cycle_time} hours")

# Get lead time (created → completed)
lead_time = task.lead_time()
print(f"Lead time: {lead_time} hours")
```

---

## 8. Custom Fields

Structured custom fields with validation.

### Board Field Definitions

```python
board = Board(
    name="Project Board",
    custom_field_definitions={
        "environment": {
            "type": "select",
            "options": ["dev", "staging", "production"],
            "required": True
        },
        "customer": {
            "type": "text",
            "required": False
        },
        "budget": {
            "type": "number",
            "min": 0,
            "max": 100000
        }
    }
)
```

### Using Custom Fields

```python
task = Task(
    board_id=board.id,
    title="Deploy feature",
    custom_fields={
        "environment": "production",
        "customer": "Acme Corp",
        "budget": 5000
    }
)
```

---

## 9. Labels & Colors

Visual categorization with colored labels.

### Adding Labels

```python
task = Task(
    board_id=board.id,
    title="Critical bug fix",
    labels=[
        {"name": "urgent", "color": "#ff0000"},
        {"name": "bug", "color": "#d73a4a"},
        {"name": "customer-facing", "color": "#ff9900"}
    ]
)
```

---

## 10. Sprints & Story Points

Associate tasks with sprints and estimate with story points.

### Sprint Planning

```python
task = Task(
    board_id=board.id,
    title="User profile page",
    sprint_id="sprint_2024_12",
    story_points=5
)
```

### Sprint Configuration

```python
board = Board(
    name="Agile Board",
    sprint_config={
        "duration_weeks": 2,
        "start_day": "monday",
        "velocity_target": 40  # story points per sprint
    }
)
```

---

## 11. Advanced Filtering

Sophisticated task filtering and search.

### Basic Filtering

```python
from paracle_kanban import TaskFilter, TaskStatus, TaskPriority

filter = TaskFilter(all_tasks)

# Filter by multiple criteria
filtered = filter.filter(
    status=[TaskStatus.IN_PROGRESS, TaskStatus.REVIEW],
    priority=TaskPriority.HIGH,
    assigned_to="coder_agent",
    tags=["api", "backend"]
)
```

### Advanced Filters

```python
# Overdue tasks
overdue = filter.filter(overdue=True)

# Tasks due soon (next 7 days)
due_soon = filter.get_due_soon(days=7)

# Tasks with dependencies
with_deps = filter.filter(has_dependencies=True)

# Blocked tasks
blocked = filter.filter(is_blocked=True)

# Custom filter function
high_priority_backend = filter.filter(
    custom_filter=lambda t: (
        t.priority == TaskPriority.HIGH and
        "backend" in t.tags
    )
)
```

### Sorting

```python
# Sort by priority (critical first)
sorted_tasks = filter.sort(
    tasks=filtered,
    key="priority",
    reverse=True
)

# Sort by due date
by_due_date = filter.sort(key="due_date")
```

### Grouping

```python
# Group by status
by_status = filter.group_by(key="status")

# Group by assignee
by_assignee = filter.group_by(key="assignee")

# Group by swimlane
by_swimlane = filter.group_by(key="swimlane")
```

---

## 12. Analytics & Metrics

Advanced analytics for velocity, burndown, and forecasting.

### Velocity Metrics

```python
from paracle_kanban import KanbanAnalytics

analytics = KanbanAnalytics(all_tasks)

# Calculate velocity (last 30 days)
velocity = analytics.velocity_metrics(days=30)
print(f"Tasks per day: {velocity['tasks_per_day']}")
print(f"Story points per day: {velocity['story_points_per_day']}")
print(f"Avg cycle time: {velocity['avg_cycle_time_hours']} hours")
```

### Burndown Chart

```python
# Get burndown data for sprint
burndown = analytics.burndown_data(sprint_id="sprint_2024_12")

print(f"Total points: {burndown['total_story_points']}")
print(f"Remaining: {burndown['remaining_story_points']}")
print(f"Progress: {burndown['completion_percentage']}%")
```

### Throughput Analysis

```python
# Tasks completed per day
throughput = analytics.throughput(days=30, group_by="day")

for date, count in throughput.items():
    print(f"{date}: {count} tasks")
```

### Lead Time Distribution

```python
# Analyze lead time statistics
lead_time = analytics.lead_time_distribution()

print(f"Average: {lead_time['avg']:.1f} hours")
print(f"Median: {lead_time['median']:.1f} hours")
print(f"95th percentile: {lead_time['p95']:.1f} hours")
```

### Bottleneck Analysis

```python
# Identify workflow bottlenecks
bottlenecks = analytics.bottleneck_analysis()

for bottleneck in bottlenecks['bottlenecks']:
    print(f"{bottleneck['status']}: {bottleneck['task_count']} tasks")
    print(f"  Avg time: {bottleneck['avg_time_hours']:.1f} hours")
```

### Forecasting

```python
# Forecast completion
forecast = analytics.forecast(
    remaining_story_points=50,
    days_history=30
)

print(f"Estimated days: {forecast['estimated_days']:.1f}")
print(f"Completion date: {forecast['estimated_completion_date']}")
print(f"Confidence: {forecast['confidence']}")
```

---

## 13. Recurring Tasks

Automatically create recurring tasks.

### Setting Up Recurrence

```python
task = Task(
    board_id=board.id,
    title="Daily standup",
    recurrence="daily",  # or "weekly", "monthly"
    template_id="standup_template"
)

# Cron-style recurrence
task = Task(
    board_id=board.id,
    title="Weekly backup",
    recurrence="cron:0 2 * * 0"  # Every Sunday at 2 AM
)
```

---

## CLI Usage Examples

```bash
# Create board with swimlanes and WIP limits
paracle board create "Sprint Board" \\
  --swimlanes "Frontend,Backend,DevOps" \\
  --wip-limit in_progress:3 \\
  --wip-limit review:5

# Create task from template
paracle task create-from-template <board_id> bug_report \\
  --var summary:"Login broken" \\
  --var description:"Cannot log in"

# Filter tasks
paracle task list <board_id> \\
  --status in_progress,review \\
  --priority high \\
  --overdue

# Show analytics
paracle board analytics <board_id> --days 30

# Check WIP status
paracle board wip-status <board_id>

# Validate dependencies
paracle task validate-deps <task_id>
```

---

## Migration Guide

Existing tasks are fully compatible. New fields are optional:

- `swimlane`: defaults to `None`
- `due_date`: defaults to `None`
- `estimated_hours`: defaults to `None`
- `actual_hours`: defaults to `0.0`
- `labels`: defaults to `[]`
- `custom_fields`: defaults to `{}`
- `sprint_id`: defaults to `None`
- `story_points`: defaults to `None`
- `parent_task_id`: defaults to `None`
- `recurrence`: defaults to `None`
- `template_id`: defaults to `None`

Database schema will be updated automatically on first use.

---

## Summary

These enhancements make `paracle_kanban` a production-ready project management system with:

- ✅ **Visual Organization** (swimlanes, labels)
- ✅ **Process Control** (WIP limits, dependencies)
- ✅ **Collaboration** (comments, notifications)
- ✅ **Efficiency** (templates, recurring tasks)
- ✅ **Planning** (time tracking, story points, sprints)
- ✅ **Insights** (analytics, forecasting, bottlenecks)
- ✅ **Flexibility** (custom fields, filters, views)

Total additions: **~2,500 lines of production code** across 7 new modules.
