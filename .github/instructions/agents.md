# Instructions globales pour les agents PARACLE

## Contexte

Ce repository contient le framework PARACLE (Protocol for Agent Reasoning, Architecture, Context and Lifecycle Engineering), un système de gestion de projet IA-Native.

## Agents disponibles

- **FrameworkArchitectAgent** : Expert en architecture de frameworks et gestion de projet
- **DocumentationWriterAgent** : Expert en documentation technique et technical writing

## Conventions

### Format des messages inter-agents

```json
{
  "from": "AgentSource",
  "to": "AgentDestination",
  "type": "MESSAGE_TYPE",
  "task_id": "TASK-XXX",
  "summary": "Résumé court",
  "details": "Détails complets si nécessaire"
}
```

### Types de messages standards

| Type                   | Description                   |
| ---------------------- | ----------------------------- |
| `ASSIGN_TASK`          | Assigner une tâche à un agent |
| `PROPOSE_CHANGE`       | Proposer une modification     |
| `REQUEST_REVIEW`       | Demander une revue            |
| `REQUEST_CHANGES`      | Demander des modifications    |
| `APPROVED`             | Valider une proposition       |
| `REJECTED`             | Rejeter une proposition       |
| `TASK_COMPLETED`       | Signaler une tâche terminée   |
| `REQUEST_ANALYSIS`     | Demander une analyse          |
| `PROPOSE_ARCHITECTURE` | Proposer une architecture     |

## Règles générales

1. **Traçabilité** : Toute décision importante doit être documentée
2. **Incrémental** : Privilégier les petits changements validables
3. **Communication** : Utiliser les messages structurés pour les échanges
4. **Qualité** : Appliquer les standards définis dans chaque agent
