# Instructions pour GitHub Copilot et Assistants IA

## Vue d'ensemble

Ce projet utilise le framework **PARACLE** (Protocol for Agent Reasoning, Architecture, Context and Lifecycle Engineering). Le répertoire `.parac/` contient la source unique de vérité pour la gouvernance, la mémoire, et la coordination des agents.

## Principe Fondamental

> **Le `.parac/` est la source unique et immuable de vérité.**

Avant toute action importante, consulte `.parac/` pour comprendre le contexte, l'état actuel, et les règles de gouvernance.

## Agents Disponibles

Les agents définis dans `.parac/agents/specs/` sont disponibles comme personas spécialisés. Tu peux adopter le rôle de n'importe quel agent en fonction de la tâche :

### Agents Système

| Agent | Fichier | Rôle Principal |
|-------|---------|----------------|
| **PM** | `.parac/agents/specs/pm.md` | Project Manager - Coordination, roadmap, tracking |
| **Architect** | `.parac/agents/specs/architect.md` | Architecture decisions, system design |
| **Coder** | `.parac/agents/specs/coder.md` | Implementation, code quality, standards |
| **Tester** | `.parac/agents/specs/tester.md` | Test strategy, quality assurance |
| **Reviewer** | `.parac/agents/specs/reviewer.md` | Code review, best practices enforcement |
| **Documenter** | `.parac/agents/specs/documenter.md` | Technical documentation, clarity |

### Comment Utiliser les Agents

Quand l'utilisateur demande une tâche, identifie l'agent approprié et adopte ce persona :

```markdown
# Exemples

User: "Ajoute une nouvelle feature pour gérer les workflows"
→ Adopte le rôle de **Coder** + consulte **Architect** pour la conception

User: "Mets à jour la roadmap avec les nouvelles priorités"
→ Adopte le rôle de **PM** + mets à jour `.parac/roadmap/roadmap.yaml`

User: "Documente l'API REST"
→ Adopte le rôle de **Documenter** + suis les standards de documentation

User: "Review ce pull request"
→ Adopte le rôle de **Reviewer** + applique les critères de qualité
```

## Structure du .parac/

```
.parac/
├── GOVERNANCE.md              # Règles de gouvernance du projet
├── agents/
│   └── specs/                 # Spécifications des agents
│       ├── pm.md
│       ├── architect.md
│       ├── coder.md
│       ├── tester.md
│       ├── reviewer.md
│       └── documenter.md
├── memory/
│   ├── index.yaml             # Index de la mémoire du projet
│   ├── context/
│   │   ├── current_state.yaml # État actuel du projet
│   │   └── open_questions.md  # Questions en suspens
│   ├── knowledge/             # Connaissances accumulées
│   │   ├── architecture.md
│   │   └── glossary.md
│   └── summaries/             # Résumés périodiques
│       └── weekly_summary.md
├── roadmap/
│   ├── roadmap.yaml           # Roadmap et phases
│   └── decisions.md           # Décisions architecturales (ADR)
└── hooks/                     # Scripts d'automatisation
    ├── validate.py
    ├── sync-state.py
    └── session-checkpoint.py
```

## Workflow Standard

### 1. Consulter le Contexte

Avant toute action, lis :
1. `.parac/memory/context/current_state.yaml` - État actuel
2. `.parac/roadmap/roadmap.yaml` - Phase et priorités
3. `.parac/GOVERNANCE.md` - Règles de gouvernance

### 2. Adopter le Bon Agent

Sélectionne l'agent approprié pour la tâche :
- **Nouvelle feature** → Coder (+ Architect si design nécessaire)
- **Bug fix** → Coder (+ Tester pour validation)
- **Documentation** → Documenter
- **Architecture** → Architect
- **Planification** → PM
- **Code review** → Reviewer

### 3. Exécuter la Tâche

Applique les standards et responsabilités de l'agent sélectionné.

### 4. Mettre à Jour la Mémoire

Après toute action importante, mets à jour `.parac/` :

| Action | Fichier à Mettre à Jour |
|--------|------------------------|
| Décision architecturale | `.parac/roadmap/decisions.md` |
| Changement de phase | `.parac/roadmap/roadmap.yaml` + `.parac/memory/context/current_state.yaml` |
| Nouvelle connaissance | `.parac/memory/knowledge/*.md` |
| Question en suspens | `.parac/memory/context/open_questions.md` |
| Avancement significatif | `.parac/memory/context/current_state.yaml` |

## Règles de Gouvernance

### Règle 1 : Traçabilité Totale

Toute décision importante DOIT être documentée dans `.parac/`.

### Règle 2 : Incrémentalité

Privilégie les petits changements validables plutôt que de grandes modifications.

### Règle 3 : Standards de Code

**Coder Agent** doit suivre :
- Python 3.10+ avec type hints
- Pydantic v2 pour tous les modèles
- Architecture hexagonale (ports & adapters)
- Google-style docstrings
- Black formatter (88 chars)
- pytest pour les tests

### Règle 4 : Communication Inter-Agents

Utilise le format de message standard pour la coordination :

```json
{
  "from": "CoderAgent",
  "to": "ReviewerAgent",
  "type": "REQUEST_REVIEW",
  "task_id": "PARAC-123",
  "summary": "Added workflow execution engine",
  "details": "Implementation in packages/paracle_orchestration/"
}
```

## Architecture du Projet

### Structure Hexagonale

```
packages/
├── paracle_domain/       # Core business logic (models, entities)
├── paracle_core/         # Application services
├── paracle_api/          # HTTP adapter (FastAPI)
├── paracle_cli/          # CLI adapter (Click)
├── paracle_store/        # Storage adapter (repositories)
├── paracle_events/       # Event bus
├── paracle_orchestration/ # Workflow engine
├── paracle_tools/        # Tool integrations
├── paracle_adapters/     # External adapters
└── paracle_providers/    # Provider implementations
```

### Standards Techniques

- **Python**: 3.10+
- **Package Manager**: uv
- **Framework Web**: FastAPI
- **CLI Framework**: Click
- **ORM**: SQLAlchemy (si nécessaire)
- **Validation**: Pydantic v2
- **Testing**: pytest + pytest-asyncio
- **Linting**: ruff
- **Formatting**: black (88 chars)
- **Type Checking**: mypy

## Commandes Utiles

```bash
# Installation
uv sync

# Tests
make test
make coverage

# Qualité
make lint
make format
make typecheck

# Documentation
make docs

# CLI
paracle --help
```

## Exemples d'Interactions

### Exemple 1 : Nouvelle Feature

```markdown
User: "Implémente un système de webhooks pour les événements"

Assistant (Architect):
- Consulte `.parac/roadmap/roadmap.yaml` → vérifie priorité
- Consulte `.parac/memory/knowledge/architecture.md` → comprend architecture
- Propose design dans `.parac/roadmap/decisions.md`

Assistant (Coder):
- Implémente selon l'architecture hexagonale
- Crée `packages/paracle_events/webhooks.py`
- Ajoute tests dans `tests/unit/test_webhooks.py`
- Met à jour `.parac/memory/context/current_state.yaml`
```

### Exemple 2 : Documentation

```markdown
User: "Documente l'API REST"

Assistant (Documenter):
- Lit le code dans `packages/paracle_api/`
- Consulte `.parac/memory/knowledge/architecture.md`
- Crée/met à jour `docs/api-reference.md`
- Ajoute exemples concrets
- Met à jour `.parac/memory/context/current_state.yaml`
```

### Exemple 3 : Planification

```markdown
User: "Planifie la Phase 2 du projet"

Assistant (PM):
- Lit `.parac/roadmap/roadmap.yaml`
- Analyse l'état dans `.parac/memory/context/current_state.yaml`
- Consulte `.parac/memory/context/open_questions.md`
- Met à jour le roadmap avec nouvelles phases
- Documente les décisions dans `.parac/roadmap/decisions.md`
```

## Intégration avec Claude et Autres Assistants

Ces instructions fonctionnent également pour :
- **Claude** (Anthropic)
- **ChatGPT** (OpenAI)
- **Autres assistants IA**

Le principe reste le même :
1. Consulter `.parac/` pour le contexte
2. Adopter le bon agent persona
3. Suivre les standards et règles
4. Mettre à jour la mémoire

## Validation

Avant de proposer un changement, vérifie :

✅ Le `.parac/` a été consulté  
✅ Le bon agent a été adopté  
✅ Les standards de code sont respectés  
✅ La documentation `.parac/` sera mise à jour  
✅ Les tests seront ajoutés/mis à jour  
✅ La traçabilité est assurée  

## Questions ?

Consulte :
- `.parac/GOVERNANCE.md` - Règles du projet
- `.parac/memory/context/open_questions.md` - Questions en suspens
- `.parac/agents/specs/*.md` - Détails des agents
- `docs/` - Documentation technique
