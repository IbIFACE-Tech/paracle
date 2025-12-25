# Instructions globales pour les agents PARACLE

## Contexte

Ce repository contient le framework PARACLE (Protocol for Agent Reasoning, Architecture, Context and Lifecycle Engineering), un système de gestion de projet IA-Native.

## Source de Vérité : Le `.parac/`

> **Principe fondamental** : Le répertoire `.parac/` est la source unique de vérité pour la gouvernance, la mémoire, et la coordination des agents.

Avant toute action, consulte :

- `.parac/memory/context/current_state.yaml` - État actuel du projet
- `.parac/roadmap/roadmap.yaml` - Roadmap et phases
- `.parac/GOVERNANCE.md` - Règles de gouvernance

## Agents disponibles

### Agents GitHub (`.github/agents/`)

- **FrameworkArchitectAgent** : Expert en architecture de frameworks et gestion de projet
- **DocumentationWriterAgent** : Expert en documentation technique et technical writing

### Agents PARAC (`.parac/agents/specs/`)

- **PM** (`pm.md`) : Project Manager - Coordination, roadmap, tracking
- **Architect** (`architect.md`) : Architecture decisions, system design
- **Coder** (`coder.md`) : Implementation, code quality, standards
- **Tester** (`tester.md`) : Test strategy, quality assurance
- **Reviewer** (`reviewer.md`) : Code review, best practices enforcement
- **Documenter** (`documenter.md`) : Technical documentation, clarity

**Important** : Les agents PARAC sont des personas que tu peux adopter en fonction de la tâche. Consulte leurs specs dans `.parac/agents/specs/` pour connaître leurs responsabilités et standards.

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
