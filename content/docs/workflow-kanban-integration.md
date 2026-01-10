# Workflow ↔ Kanban Integration Guide

## Vue d'ensemble

Paracle offre une **intégration bidirectionnelle** entre les workflows (processus automatisés) et les tâches Kanban (gestion de travail), permettant :

1. **Workflow → Kanban** : Suivre l'exécution d'un workflow dans un tableau Kanban
2. **Kanban → Workflow** : Déclencher un workflow quand une tâche change d'état
3. **Synchronisation d'état** : Les statuts sont automatiquement synchronisés
4. **Liens multiples** : Une tâche peut référencer plusieurs workflows et vice-versa

## Différences clés

| Aspect           | Workflow                     | Kanban Task                      |
| ---------------- | ---------------------------- | -------------------------------- |
| **Nature**       | Éphémère (1 exécution)       | Persistant (tracking long terme) |
| **État**         | ExecutionStatus              | TaskStatus                       |
| **Durée**        | Minutes à heures             | Jours à semaines                 |
| **Stockage**     | `.parac/runs/` (archives)    | SQLite (persistant)              |
| **Modification** | Impossible pendant exécution | Dynamique                        |

**Point clé** : La **différence principale** est que la tâche Kanban a un **état persistant** qui doit être suivi, alors que le workflow est éphémère.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                BIDIRECTIONAL INTEGRATION                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐           ┌──────────────────┐       │
│  │   Workflow       │◄─────────►│  Kanban Task     │       │
│  │   (Ephemeral)    │           │  (Persistent)    │       │
│  └──────────────────┘           └──────────────────┘       │
│           │                              │                  │
│           ├─ execution_id                ├─ task_id        │
│           ├─ workflow_id                 ├─ board_id       │
│           ├─ status (running)            ├─ status (todo)  │
│           └─ metadata                    └─ metadata       │
│                       ▲                  ▼                  │
│              ┌─────────────────────────────┐               │
│              │   TaskWorkflowSync          │               │
│              │   (Synchronization Layer)   │               │
│              └─────────────────────────────┘               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Mapping des statuts

### Workflow → Kanban

| ExecutionStatus   | TaskStatus  |
| ----------------- | ----------- |
| PENDING           | TODO        |
| RUNNING           | IN_PROGRESS |
| AWAITING_APPROVAL | REVIEW      |
| COMPLETED         | DONE        |
| FAILED            | BLOCKED     |
| CANCELLED         | ARCHIVED    |
| TIMEOUT           | BLOCKED     |

### Kanban → Workflow

| TaskStatus  | ExecutionStatus   |
| ----------- | ----------------- |
| BACKLOG     | PENDING           |
| TODO        | PENDING           |
| IN_PROGRESS | RUNNING           |
| REVIEW      | AWAITING_APPROVAL |
| BLOCKED     | FAILED            |
| DONE        | COMPLETED         |
| ARCHIVED    | CANCELLED         |

## Cas d'usage

### 1. Suivre un workflow dans Kanban

**Scénario** : Un workflow long s'exécute, vous voulez suivre sa progression dans votre tableau Kanban.

```python
from paracle_orchestration.context import ExecutionContext, ExecutionStatus
from paracle_orchestration.kanban_integration import track_workflow_in_kanban

# Créer un contexte d'exécution
context = ExecutionContext(
    workflow_id="feature_development",
    execution_id="exec_001",
    inputs={"feature": "user_auth"},
    status=ExecutionStatus.RUNNING,
)

# Créer automatiquement une tâche pour suivre ce workflow
task = track_workflow_in_kanban(
    context=context,
    board_id="sprint_1"
)

print(f"✅ Tracking task created: {task.id}")
print(f"   Status: {task.status.value}")  # → IN_PROGRESS
```

### 2. Déclencher un workflow depuis une tâche

**Scénario** : Une tâche Kanban passe à IN_PROGRESS, vous voulez déclencher un workflow automatiquement.

```python
from paracle_kanban.task import Task, TaskStatus
from paracle_orchestration.kanban_integration import TaskWorkflowSync

# Créer une tâche
task = Task(
    board_id="backlog",
    title="Deploy to production",
    status=TaskStatus.TODO,
)

# Lier un workflow à cette tâche
TaskWorkflowSync.link_workflow_to_task(task, "deployment_workflow")

# Quand la tâche passe à IN_PROGRESS
task.move_to(TaskStatus.IN_PROGRESS)

# → Déclencher le workflow (dans votre code)
workflow_id = task.metadata["primary_workflow_id"]
# Execute workflow...
```

### 3. Synchroniser les statuts automatiquement

**Scénario** : Le workflow progresse, le statut de la tâche se met à jour automatiquement.

```python
from paracle_orchestration.kanban_integration import TaskWorkflowSync

# Le workflow progresse
context.status = ExecutionStatus.AWAITING_APPROVAL

# Synchroniser vers la tâche
updated = TaskWorkflowSync.sync_workflow_to_task(task, context)

if updated:
    print(f"✅ Task updated to: {task.status.value}")  # → REVIEW
else:
    print("⚠️ Transition not allowed or no change")
```

### 4. Une tâche, plusieurs workflows

**Scénario** : Une release complexe nécessite plusieurs workflows séquentiels.

```python
# Une tâche "Release v1.0.0"
task = Task(
    board_id="releases",
    title="Release v1.0.0",
    status=TaskStatus.TODO,
)

# Lier plusieurs workflows
workflows = [
    "version_bump",
    "changelog_generation",
    "build_release",
    "deploy_production"
]

for wf_id in workflows:
    TaskWorkflowSync.link_workflow_to_task(task, wf_id)

# Tous les workflows sont référencés dans la tâche
print(f"Task has {len(task.metadata['workflows'])} linked workflows")
```

## API Reference

### TaskWorkflowSync

Classe principale pour la synchronisation bidirectionnelle.

#### Méthodes

```python
# Lier workflow à tâche
TaskWorkflowSync.link_workflow_to_task(
    task: Task,
    workflow_id: str,
    execution_id: str | None = None
) -> None

# Lier tâche à workflow
TaskWorkflowSync.link_task_to_workflow(
    context: ExecutionContext,
    task_id: str
) -> None

# Synchroniser workflow → tâche
TaskWorkflowSync.sync_workflow_to_task(
    task: Task,
    context: ExecutionContext
) -> bool  # Returns True if updated

# Créer une tâche depuis workflow
TaskWorkflowSync.create_task_from_workflow(
    workflow_id: str,
    execution_id: str,
    context: ExecutionContext,
    board_id: str
) -> Task

# Extraire infos workflow depuis tâche
TaskWorkflowSync.get_workflow_info_from_task(
    task: Task
) -> dict[str, Any]

# Extraire infos tâche depuis workflow
TaskWorkflowSync.get_task_info_from_workflow(
    context: ExecutionContext
) -> dict[str, Any]
```

### Helper Functions

```python
# Créer automatiquement une tâche de tracking
track_workflow_in_kanban(
    context: ExecutionContext,
    board_id: str,
    task_manager: Any = None
) -> Task

# Exécuter un workflow depuis une tâche
execute_workflow_from_task(
    task: Task,
    workflow_engine: Any,
    workflow_id: str | None = None
) -> ExecutionContext
```

## Métadonnées

### Dans Task.metadata

```python
{
    "workflows": [
        {
            "workflow_id": "feature_dev",
            "execution_id": "exec_001",
            "linked_at": "2026-01-10T12:00:00Z"
        }
    ],
    "primary_workflow_id": "feature_dev",
    "last_sync_at": "2026-01-10T12:05:00Z",
    "last_sync_from": "exec_001",
    "pending_status": "done",  # Si transition bloquée
    "status_sync_blocked": true,  # Si transition impossible
    "synced_from_workflow": {
        "execution_id": "exec_001",
        "workflow_id": "feature_dev",
        "old_status": "in_progress",
        "new_status": "done",
        "synced_at": "2026-01-10T12:05:00Z"
    }
}
```

### Dans ExecutionContext.metadata

```python
{
    "kanban_tasks": [
        {
            "task_id": "task_001",
            "linked_at": "2026-01-10T12:00:00Z"
        }
    ],
    "primary_task_id": "task_001"
}
```

## Pattern recommandé : Hybrid Workflow

Combinez les deux systèmes pour un workflow de développement complet :

```python
async def feature_development_flow(feature_title: str):
    """Pattern complet : Kanban + Workflow."""

    # 1. Créer une tâche Kanban (backlog)
    task = board.create_task(
        title=feature_title,
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
    )

    # 2. Lier un workflow
    workflow_id = "feature_development"
    TaskWorkflowSync.link_workflow_to_task(task, workflow_id)

    # 3. Humain déplace la tâche → IN_PROGRESS
    task.move_to(TaskStatus.IN_PROGRESS)

    # 4. Déclencher le workflow automatiquement
    context = await workflow_engine.execute(
        workflow_id,
        inputs={"feature": feature_title}
    )

    # 5. Lier bidirectionnellement
    TaskWorkflowSync.link_task_to_workflow(context, task.id)

    # 6. Synchroniser les statuts pendant l'exécution
    def on_workflow_progress(status: ExecutionStatus):
        context.status = status
        TaskWorkflowSync.sync_workflow_to_task(task, context)

    # 7. À la fin, le statut est synchronisé
    context.complete({"files_created": [...]})
    TaskWorkflowSync.sync_workflow_to_task(task, context)

    # Résultat : task.status == DONE
    return task, context
```

## Gestion des edge cases

### Transition impossible

Si le workflow veut changer le statut de la tâche mais la transition n'est pas valide :

```python
# Tâche déjà DONE
task.status = TaskStatus.DONE

# Workflow RUNNING veut syncer → IN_PROGRESS
context.status = ExecutionStatus.RUNNING
updated = TaskWorkflowSync.sync_workflow_to_task(task, context)

# updated == False
# task.metadata["status_sync_blocked"] == True
# task.metadata["pending_status"] == "in_progress"
```

### Multiples workflows concurrents

```python
# Plusieurs workflows liés à la même tâche
task.metadata["workflows"] = [
    {"workflow_id": "wf1", "execution_id": "exec1"},
    {"workflow_id": "wf2", "execution_id": "exec2"},
]

# La synchronisation utilise le dernier workflow actif
# Pour éviter les conflits, définissez une priorité ou un ordre
```

## CLI Commands

```bash
# Créer une tâche et la lier à un workflow
paracle board create "Implement feature" --workflow feature_dev

# Lister les tâches avec workflows liés
paracle board list --show-workflows

# Voir les détails d'une tâche et ses workflows
paracle board show task_001

# Exécuter un workflow depuis une tâche
paracle workflow run --from-task task_001
```

## Exemples complets

Voir `examples/24_workflow_kanban_integration.py` pour 6 démos complètes :

1. **Workflow → Kanban** : Créer une tâche de tracking
2. **Kanban → Workflow** : Déclencher depuis une tâche
3. **Multiples workflows** : Une tâche, plusieurs workflows
4. **Edge cases** : Gérer les transitions impossibles
5. **Sync bidirectionnelle** : Synchronisation complète
6. **Pattern production** : Intégration réelle avec board

## Best Practices

1. ✅ **Toujours lier bidirectionnellement** pour la traçabilité complète
2. ✅ **Vérifier can_transition_to()** avant la synchronisation
3. ✅ **Utiliser metadata** pour stocker le contexte additionnel
4. ✅ **Définir un workflow "primary"** si plusieurs sont liés
5. ✅ **Logger les synchronisations** pour audit

## Conclusion

L'intégration Workflow ↔ Kanban permet de :

- 📊 **Suivre** les workflows longs dans Kanban
- 🚀 **Déclencher** des workflows depuis des tâches
- 🔄 **Synchroniser** automatiquement les statuts
- 🔗 **Lier** tâches et workflows bidirectionnellement
- 📝 **Maintenir** un état persistant pour les tâches

**La différence clé** : Le workflow est **éphémère**, la tâche Kanban est **persistante** avec un état qui doit être suivi. L'intégration permet de combiner les deux mondes ! 🎯
