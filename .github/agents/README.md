# Agents PARACLE pour Assistants IA

Ce dossier contient les configurations pour intégrer le système d'agents PARACLE avec GitHub Copilot, Claude, ChatGPT et autres assistants IA.

## Vue d'ensemble

Le framework PARACLE utilise un système d'agents définis dans `.parac/agents/specs/` qui peuvent être adoptés comme **personas** par les assistants IA.

### Dogfooding : Nous utilisons PARACLE pour développer PARACLE

> **Important** : Ce projet a une relation méta particulière.

```
┌─────────────────────────────────────────────────────────────┐
│                    PARACLE FRAMEWORK                        │
│                      packages/                              │
│                                                             │
│   Le PRODUIT que nous développons                          │
│   - Code source du framework                                │
│   - Génère les .parac/ pour les utilisateurs              │
└─────────────────────────────────────────────────────────────┘
                          ↓ génère/utilise
┌─────────────────────────────────────────────────────────────┐
│                   .parac/ WORKSPACE                         │
│                  (Côté utilisateur)                         │
│                                                             │
│   Ici : Notre propre utilisation du framework              │
│   - Gouvernance de notre développement                     │
│   - Source de vérité pour gérer CE projet                 │
└─────────────────────────────────────────────────────────────┘
```

**Distinction clé** :

- **`packages/`** = Le framework PARACLE (le produit que nous construisons)
- **`.parac/`** = Notre workspace utilisateur (comment nous gérons ce projet avec notre propre framework)

C'est du **dogfooding** - nous sommes notre premier utilisateur.

## Fichiers Principaux

### Instructions

- **`copilot-instructions.md`** : Instructions complètes pour GitHub Copilot et autres assistants
- **`COPILOT_INSTRUCTIONS`** : Version courte pour VS Code Copilot
- **`instructions/agents.md`** : Instructions globales pour tous les agents
- **`instructions/parac-agents-mapping.md`** : Mapping entre agents PARAC et assistants IA

### Configuration

- **`copilot-config.json`** : Configuration JSON pour VS Code Copilot

### Agents GitHub

- **`agents/framework-architect.md`** : Agent spécialisé en architecture de frameworks
- **`agents/documentation-writer.md`** : Agent spécialisé en documentation technique

## Agents PARAC Disponibles

Les agents suivants sont définis dans `.parac/agents/specs/` :

| Agent          | Rôle             | Quand l'utiliser                  |
| -------------- | ---------------- | --------------------------------- |
| **PM**         | Project Manager  | Planification, roadmap, tracking  |
| **Architect**  | System Architect | Décisions architecturales, design |
| **Coder**      | Developer        | Implémentation, code quality      |
| **Tester**     | QA Engineer      | Tests, validation, QA             |
| **Reviewer**   | Code Reviewer    | Revue de code, standards          |
| **Documenter** | Tech Writer      | Documentation technique           |

## Comment ça Fonctionne

### 1. Détection Automatique

Les assistants IA détectent automatiquement quel agent adopter en fonction de la requête de l'utilisateur :

```
User: "Implémente une nouvelle feature pour les workflows"
→ Assistant adopte le persona "Coder"

User: "Planifie la Phase 2 du projet"
→ Assistant adopte le persona "PM"

User: "Documente l'API REST"
→ Assistant adopte le persona "Documenter"
```

### 2. Consultation du Contexte

Avant toute action, l'assistant consulte `.parac/` pour :

- Comprendre l'état actuel du projet
- Lire les décisions architecturales antérieures
- Connaître les priorités de la roadmap
- Accéder aux connaissances accumulées

### 3. Application des Standards

Chaque agent a ses propres standards et responsabilités définis dans `.parac/agents/specs/{agent}.md`. L'assistant applique ces standards lors de l'exécution de la tâche.

### 4. Mise à Jour de la Mémoire

Après toute action importante, l'assistant met à jour `.parac/` pour maintenir la traçabilité :

- `.parac/memory/context/current_state.yaml` - État actuel
- `.parac/roadmap/decisions.md` - Décisions architecturales
- `.parac/memory/knowledge/` - Nouvelles connaissances

## Workflow Standard

```
┌─────────────────┐
│  User Request   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Detect Agent    │  ← Identifier le bon agent selon la tâche
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Read .parac/    │  ← Consulter le contexte projet
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Adopt Persona   │  ← Adopter responsabilités et standards
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Execute Task    │  ← Exécuter la tâche
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update .parac/  │  ← Mettre à jour la mémoire
└─────────────────┘
```

## Configuration pour GitHub Copilot

### VS Code

1. Les instructions sont automatiquement chargées depuis `.github/copilot-instructions.md`
2. La configuration JSON est dans `.github/copilot-config.json`

### GitHub CLI

```bash
# Copilot utilisera automatiquement .github/copilot-instructions.md
gh copilot suggest "implémente une nouvelle feature"
```

## Configuration pour Claude

### Claude Desktop

Ajouter dans `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) ou `%APPDATA%\Claude\claude_desktop_config.json` (Windows) :

```json
{
  "projects": {
    "paracle": {
      "context_files": [
        ".github/copilot-instructions.md",
        ".parac/memory/context/current_state.yaml",
        ".parac/roadmap/roadmap.yaml"
      ]
    }
  }
}
```

### Claude API

Les instructions de `.github/copilot-instructions.md` peuvent être incluses dans le contexte système.

## Configuration pour ChatGPT

### ChatGPT Web

1. Créer un GPT custom avec les instructions de `.github/copilot-instructions.md`
2. Uploader les fichiers `.parac/agents/specs/*.md` comme knowledge base

### ChatGPT API

Inclure le contenu de `.github/copilot-instructions.md` dans le system prompt.

## Exemples d'Utilisation

### Exemple 1 : Nouvelle Feature

```markdown
User: "Ajoute un système de webhooks pour les événements"

Assistant (Architect + Coder):

1. Lit .parac/roadmap/roadmap.yaml → vérifie priorité
2. Consulte .parac/memory/knowledge/architecture.md
3. Propose design dans .parac/roadmap/decisions.md
4. Implémente selon architecture hexagonale
5. Ajoute tests
6. Met à jour .parac/memory/context/current_state.yaml
```

### Exemple 2 : Planification

```markdown
User: "Planifie la Phase 2 du projet"

Assistant (PM):

1. Lit .parac/roadmap/roadmap.yaml
2. Analyse .parac/memory/context/current_state.yaml
3. Consulte .parac/memory/context/open_questions.md
4. Met à jour roadmap avec nouvelles phases
5. Documente dans .parac/roadmap/decisions.md
```

### Exemple 3 : Documentation

```markdown
User: "Documente l'API REST"

Assistant (Documenter):

1. Lit le code dans packages/paracle_api/
2. Consulte .parac/memory/knowledge/architecture.md
3. Crée/met à jour docs/api-reference.md
4. Ajoute exemples concrets
5. Met à jour .parac/memory/context/current_state.yaml
```

## Communication Inter-Agents

Quand plusieurs agents doivent collaborer, utiliser le format de message standard :

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

## Validation

Avant de proposer un changement, vérifier :

- ✅ `.parac/` a été consulté pour le contexte
- ✅ Le bon agent a été adopté
- ✅ Les standards de code sont respectés
- ✅ La documentation `.parac/` sera mise à jour
- ✅ Les tests seront ajoutés/mis à jour
- ✅ La traçabilité est assurée

## Support Multi-Assistant

Ce système fonctionne avec :

- ✅ **GitHub Copilot** (VS Code, CLI, GitHub.com)
- ✅ **Claude** (Desktop, API, Web)
- ✅ **ChatGPT** (Web, API, GPT custom)
- ✅ **Autres** (Gemini, Perplexity, etc.)

Le principe reste le même : consulter `.parac/`, adopter un agent, suivre les standards, mettre à jour la mémoire.

## Liens Utiles

- [GOVERNANCE.md](../.parac/GOVERNANCE.md) - Règles de gouvernance
- [Agent Specs](../.parac/agents/specs/) - Spécifications des agents
- [Roadmap](../.parac/roadmap/roadmap.yaml) - Roadmap du projet
- [Current State](../.parac/memory/context/current_state.yaml) - État actuel
