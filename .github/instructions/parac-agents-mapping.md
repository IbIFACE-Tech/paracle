# Mapping des Agents PARAC vers GitHub Copilot

Ce fichier définit comment les agents PARAC sont exposés aux assistants IA (Copilot, Claude, etc.).

## Agents PARAC Disponibles

Les agents définis dans `.parac/agents/specs/` sont disponibles comme **personas** pour les assistants IA.

### Liste des Agents

| Agent ID     | Fichier Spec                        | Rôle             | Activation                                  |
| ------------ | ----------------------------------- | ---------------- | ------------------------------------------- |
| `pm`         | `.parac/agents/specs/pm.md`         | Project Manager  | Sur demande ou pour tâches de planification |
| `architect`  | `.parac/agents/specs/architect.md`  | System Architect | Pour décisions architecturales              |
| `coder`      | `.parac/agents/specs/coder.md`      | Developer        | Pour implémentation de code                 |
| `tester`     | `.parac/agents/specs/tester.md`     | QA Engineer      | Pour stratégie de tests                     |
| `reviewer`   | `.parac/agents/specs/reviewer.md`   | Code Reviewer    | Pour revue de code                          |
| `documenter` | `.parac/agents/specs/documenter.md` | Tech Writer      | Pour documentation                          |

## Comment Utiliser les Agents

### Pour GitHub Copilot

Les agents sont des **personas** que Copilot peut adopter. Quand l'utilisateur demande une tâche, Copilot :

1. Lit la spec de l'agent dans `.parac/agents/specs/{agent}.md`
2. Adopte les responsabilités et standards de cet agent
3. Applique le workflow défini dans la spec
4. Met à jour `.parac/` selon les règles de l'agent

### Pour Claude / ChatGPT

Même principe : les agents sont des personas à adopter selon le contexte.

**Exemple** :

```markdown
User: "Implémente une nouvelle feature pour les workflows"

Claude adopte le rôle "Coder" :
1. Lit `.parac/agents/specs/coder.md`
2. Consulte `.parac/memory/context/current_state.yaml`
3. Implémente selon les standards Python + Pydantic + Hexagonal
4. Ajoute tests
5. Met à jour `.parac/memory/context/current_state.yaml`
```

## Workflow Standard

```
User Request
    ↓
Identifier Agent
    ↓
Lire .parac/agents/specs/
    ↓
Consulter .parac/memory/
    ↓
Adopter Persona
    ↓
Exécuter Tâche
    ↓
Mettre à jour .parac/
```

## Règles de Communication Inter-Agents

Quand un agent doit consulter un autre agent (ex: Coder demande à Architect) :

```json
{
  "from": "CoderAgent",
  "to": "ArchitectAgent",
  "type": "REQUEST_GUIDANCE",
  "task_id": "PARAC-123",
  "summary": "Need architecture guidance for webhook system",
  "details": "Should we use event sourcing or simple pub/sub?"
}
```

Le format est défini dans `.parac/GOVERNANCE.md`.

## Intégration avec `.github/agents/`

Les agents GitHub existants (FrameworkArchitectAgent, DocumentationWriterAgent) sont **complémentaires** aux agents PARAC :

- **Agents GitHub** : Agents spécialisés pour ce projet spécifique
- **Agents PARAC** : Personas génériques réutilisables

Les deux peuvent être utilisés ensemble. Par exemple :

```markdown
User: "Design the new orchestration engine"

→ FrameworkArchitectAgent + ArchitectAgent (PARAC)
```

## Activation Automatique

Les assistants IA devraient automatiquement détecter le besoin d'un agent en fonction du type de requête :

| Type de Requête                            | Agent Activé |
| ------------------------------------------ | ------------ |
| "Planifie...", "Mets à jour la roadmap..." | PM           |
| "Design...", "Architecture de..."          | Architect    |
| "Implémente...", "Ajoute une feature..."   | Coder        |
| "Teste...", "Ajoute des tests pour..."     | Tester       |
| "Review...", "Vérifie le code..."          | Reviewer     |
| "Documente...", "Écris la doc de..."       | Documenter   |

## Contexte Partagé

Tous les agents ont accès au même contexte via `.parac/` :

- `.parac/memory/context/current_state.yaml` - État actuel
- `.parac/roadmap/roadmap.yaml` - Roadmap
- `.parac/roadmap/decisions.md` - Décisions architecturales
- `.parac/memory/knowledge/` - Connaissances du projet

Ceci assure la cohérence entre les agents.
