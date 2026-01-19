# Guide Complet d'Utilisation du `.parac/`

## Vision Globale

Le répertoire `.parac/` est le **système nerveux central** de votre projet Paracle. Il contient toute la gouvernance, la mémoire, les agents, et la configuration nécessaires pour un développement structuré et traçable.

```
┌─────────────────────────────────────────────────────────────┐
│                  VOTRE PROJET                               │
│               (Code source, tests, docs)                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ gouverné par
                   ↓
┌─────────────────────────────────────────────────────────────┐
│                    .parac/                                  │
│          SOURCE UNIQUE DE VÉRITÉ                            │
│                                                             │
│  📋 Gouvernance    🧠 Mémoire      👥 Agents               │
│  🗺️  Roadmap       🔧 Outils       🔄 Workflows            │
└─────────────────────────────────────────────────────────────┘
```

---

## Structure Complète

```
.parac/
├── manifest.yaml              # Métadonnées du workspace
├── project.yaml               # Configuration du projet
├── GOVERNANCE.md              # Règles de gouvernance
├── STRUCTURE.md               # Documentation de la structure
├── MAINTENANCE.md             # Guide de maintenance
├── changelog.md               # Changelog du workspace
│
├── agents/                    # Configuration des agents IA
│   ├── manifest.yaml          # Liste et config des agents
│   ├── SKILL_ASSIGNMENTS.md   # Skills par agent
│   ├── specs/                 # Spécifications détaillées
│   │   ├── architect.md
│   │   ├── coder.md
│   │   ├── documenter.md
│   │   ├── pm.md
│   │   ├── reviewer.md
│   │   └── tester.md
│   └── skills/                # Bibliothèque de skills
│       ├── api-development/
│       ├── testing-qa/
│       └── ...
│
├── memory/                    # Mémoire du projet
│   ├── index.yaml             # Index de la mémoire
│   ├── context/               # Contexte actuel
│   │   ├── current_state.yaml # État du projet
│   │   └── open_questions.md  # Questions en suspens
│   ├── knowledge/             # Connaissances accumulées
│   │   ├── architecture.md
│   │   ├── glossary.md
│   │   └── decisions/
│   ├── logs/                  # Logs des actions
│   │   ├── agent_actions.log  # Actions des agents
│   │   ├── decisions.log      # Décisions importantes
│   │   └── sessions/          # Par session
│   └── summaries/             # Résumés périodiques
│
├── roadmap/                   # Planification
│   ├── roadmap.yaml           # Phases et milestones
│   └── decisions.md           # ADR (Architecture Decision Records)
│
├── workflows/                 # Workflows automatisés
│   ├── manifest.yaml          # Liste des workflows
│   └── definitions/           # Définitions YAML
│
├── tools/                     # Outils personnalisés
│   └── manifest.yaml          # Configuration des outils
│
├── adapters/                  # Adaptateurs externes
│   └── manifest.yaml          # Configuration des adapters
│
├── policies/                  # Politiques du projet
│   ├── CODE_STYLE.md
│   ├── TESTING.md
│   └── SECURITY.md
│
└── integrations/              # Intégrations externes
    ├── README.md
    └── ide/                   # Instructions IDE
        ├── _manifest.yaml
        ├── .cursorrules       # Cursor
        ├── .clinerules        # Cline
        ├── .windsurfrules     # Windsurf
        ├── CLAUDE.md          # Claude Code
        └── copilot-instructions.md  # GitHub Copilot
```

---

## 🎯 Principe Fondamental

> **`.parac/` est la source unique et immuable de vérité.**

Tout assistant IA (peu importe l'IDE) DOIT:

1. **CONSULTER** `.parac/` avant toute action
2. **SUIVRE** les règles de gouvernance
3. **LOGGER** toutes les actions importantes
4. **METTRE À JOUR** la mémoire après chaque changement

---

## 🚀 Workflow Standard pour TOUT Assistant IA

### 1. Initialisation (Première Utilisation)

```bash
# L'assistant lit ces fichiers EN PREMIER:
1. .parac/GOVERNANCE.md           # Règles du projet
2. .parac/manifest.yaml           # Configuration workspace
3. .parac/agents/manifest.yaml    # Agents disponibles
4. .parac/memory/context/current_state.yaml  # État actuel
5. .parac/roadmap/roadmap.yaml    # Phase et priorités
```

**Pourquoi?** Ces 5 fichiers donnent le contexte complet du projet.

### 2. Avant Toute Tâche

```bash
# Checklist mentale de l'assistant:
□ Quel est l'état actuel? → .parac/memory/context/current_state.yaml
□ Quelle phase sommes-nous? → .parac/roadmap/roadmap.yaml
□ Y a-t-il des questions ouvertes? → .parac/memory/context/open_questions.md
□ Quel agent adopter? → .parac/agents/specs/{agent}.md
□ Quelles sont les règles? → .parac/GOVERNANCE.md
```

### 3. Pendant l'Exécution

```bash
# Actions à prendre:
1. Adopter le bon agent persona
2. Suivre les standards du projet
3. Documenter les décisions importantes
4. Logger les actions dans .parac/memory/logs/
```

### 4. Après Chaque Action Significative

```bash
# Mettre à jour la mémoire:
1. Logger dans .parac/memory/logs/agent_actions.log
2. Si décision importante → .parac/roadmap/decisions.md
3. Si changement d'état → .parac/memory/context/current_state.yaml
4. Si nouvelle connaissance → .parac/memory/knowledge/
5. Si question → .parac/memory/context/open_questions.md
```

---

## 📖 Guide par Rôle d'Assistant

### Pour les Assistants de Code (Copilot, Cursor, Cline, etc.)

**Objectif**: Écrire du code de qualité qui suit les standards du projet.

#### Workflow:
1. **Lire**: `.parac/agents/specs/coder.md` pour adopter le persona
2. **Consulter**: `.parac/policies/CODE_STYLE.md` pour les standards
3. **Vérifier**: `.parac/memory/context/current_state.yaml` pour l'état
4. **Implémenter**: Feature selon les règles
5. **Logger**: Action dans `.parac/memory/logs/agent_actions.log`

#### Exemple de Log:
```
[2026-01-04 14:30:00] [CoderAgent] [IMPLEMENTATION] Implemented CLI workflow commands with API-first architecture
```

### Pour les Assistants de Chat (Claude, ChatGPT, etc.)

**Objectif**: Planifier, conseiller, et coordonner.

#### Workflow:
1. **Lire**: `.parac/GOVERNANCE.md` pour comprendre les règles
2. **Analyser**: `.parac/roadmap/roadmap.yaml` pour les priorités
3. **Consulter**: `.parac/memory/context/open_questions.md`
4. **Proposer**: Solutions alignées avec la gouvernance
5. **Documenter**: Décisions dans `.parac/roadmap/decisions.md`

### Pour les Assistants de Revue (Review Agents)

**Objectif**: Assurer la qualité et la conformité.

#### Workflow:
1. **Lire**: `.parac/agents/specs/reviewer.md` pour les critères
2. **Vérifier**: Conformité avec `.parac/policies/`
3. **Tester**: Selon `.parac/policies/TESTING.md`
4. **Logger**: Résultats dans `.parac/memory/logs/agent_actions.log`

---

## 🔥 Instructions IDE-Agnostiques

### Configuration Universelle

Ces instructions fonctionnent avec **n'importe quel IDE** ou assistant IA:

```markdown
# Instructions Universelles Paracle

## Étape 1: Localiser le .parac/
Cherche le répertoire `.parac/` à la racine du projet.

## Étape 2: Lire la Configuration
Lis ces fichiers dans l'ordre:
1. .parac/GOVERNANCE.md
2. .parac/manifest.yaml
3. .parac/agents/manifest.yaml
4. .parac/memory/context/current_state.yaml
5. .parac/roadmap/roadmap.yaml

## Étape 3: Adopter le Bon Agent
Consulte .parac/agents/specs/ pour trouver l'agent approprié:
- Nouvelle feature → coder
- Architecture → architect
- Documentation → documenter
- Planification → pm
- Code review → reviewer
- Tests → tester

## Étape 4: Suivre les Règles
Applique les standards de:
- .parac/policies/CODE_STYLE.md
- .parac/policies/TESTING.md
- .parac/policies/SECURITY.md

## Étape 5: Logger Toutes les Actions
Après chaque action significative:
[TIMESTAMP] [AGENT] [ACTION] Description
```

---

## 🎨 Personnalisation par IDE

### Cursor (.cursorrules)

```plaintext
# Fichier: .cursorrules

# Paracle Workspace Configuration
> Consulte TOUJOURS .parac/ avant d'agir

## Fichiers Clés
- .parac/GOVERNANCE.md
- .parac/agents/manifest.yaml
- .parac/memory/context/current_state.yaml

## Workflow
1. Lire l'état actuel
2. Adopter le bon agent
3. Implémenter selon les standards
4. Logger l'action

## Logging
Format: [TIMESTAMP] [AGENT] [ACTION] Description
Destination: .parac/memory/logs/agent_actions.log
```

### Claude Code (CLAUDE.md)

```markdown
# Fichier: .claude/CLAUDE.md

# Instructions Paracle

## Principe
.parac/ = Source unique de vérité

## Contexte Requis
Lis ces fichiers EN PREMIER:
1. .parac/GOVERNANCE.md
2. .parac/manifest.yaml
3. .parac/agents/manifest.yaml
4. .parac/memory/context/current_state.yaml
5. .parac/roadmap/roadmap.yaml

## Agents Disponibles
- architect: Design système
- coder: Implémentation
- reviewer: Code review
- tester: Tests
- pm: Planification
- documenter: Documentation

## Actions Requises
Après chaque tâche importante:
1. Log → .parac/memory/logs/agent_actions.log
2. Décision → .parac/roadmap/decisions.md
3. État → .parac/memory/context/current_state.yaml
```

### GitHub Copilot (copilot-instructions.md)

```markdown
# Fichier: .github/copilot-instructions.md

# Paracle Project Instructions

## Configuration
Ce projet utilise le framework Paracle avec `.parac/` governance.

## Avant Chaque Suggestion
1. Vérifie .parac/memory/context/current_state.yaml
2. Consulte .parac/policies/CODE_STYLE.md
3. Adopte le persona de .parac/agents/specs/coder.md

## Standards
- Python 3.10+ avec type hints
- Pydantic v2 pour les modèles
- Google-style docstrings
- Black formatter (88 chars)
- Architecture hexagonale

## Après Chaque Commit
Suggère un log pour .parac/memory/logs/agent_actions.log
```

### Cline (.clinerules)

```plaintext
# Fichier: .clinerules

# Paracle Workspace Rules

Source de Vérité: .parac/

Lecture Obligatoire:
- .parac/GOVERNANCE.md
- .parac/agents/manifest.yaml
- .parac/memory/context/current_state.yaml

Workflow Standard:
1. Consulter .parac/ pour contexte
2. Adopter agent approprié
3. Suivre standards projet
4. Logger actions importantes

Format Log:
[TIMESTAMP] [AGENT] [ACTION] Description
```

### Windsurf (.windsurfrules)

```plaintext
# Fichier: .windsurfrules

# Paracle Governance

## Principe
.parac/ = Unique source de vérité

## Initialisation
Lire:
1. .parac/GOVERNANCE.md
2. .parac/manifest.yaml
3. .parac/memory/context/current_state.yaml
4. .parac/roadmap/roadmap.yaml

## Agents
Consulter .parac/agents/specs/ pour le bon persona

## Logging
Destination: .parac/memory/logs/agent_actions.log
Format: [TIMESTAMP] [AGENT] [ACTION] Description
```

---

## 🔧 Commandes CLI Paracle

### Initialisation

```bash
# Créer un workspace .parac/
paracle init

# Configurer les agents
paracle agents create my-agent

# Générer les instructions IDE
paracle ide init
paracle ide sync --copy
```

### Consultation

```bash
# Voir l'état du projet
paracle status

# Voir le roadmap
paracle roadmap show

# Lister les agents
paracle agents list

# Voir les logs
paracle logs show
```

### Synchronisation

```bash
# Synchroniser l'état
paracle sync

# Valider la cohérence
paracle validate

# Créer un checkpoint
paracle session checkpoint
```

### Gestion de la Mémoire

```bash
# Voir la mémoire actuelle
cat .parac/memory/context/current_state.yaml

# Ajouter une décision
echo "## ADR-123: Use API-first" >> .parac/roadmap/decisions.md

# Logger une action
echo "[$(date)] [CoderAgent] [IMPLEMENTATION] Feature X" >> .parac/memory/logs/agent_actions.log
```

---

## 📊 Métriques de Qualité

### Pour Mesurer l'Utilisation Efficace du .parac/

#### ✅ Bon Signe
- `.parac/memory/logs/agent_actions.log` mis à jour régulièrement
- `.parac/memory/context/current_state.yaml` reflète l'état réel
- `.parac/roadmap/decisions.md` contient les décisions importantes
- Toutes les actions importantes sont loggées
- La mémoire est cohérente avec le code

#### ⚠️ Mauvais Signe
- Logs vides ou obsolètes
- État du projet incohérent
- Décisions non documentées
- Mémoire non synchronisée
- Assistants IA qui n'utilisent pas .parac/

---

## 🎓 Exemples Concrets

### Exemple 1: Nouvelle Feature

```bash
# Assistant IA reçoit: "Ajoute une API REST pour les workflows"

# Étape 1: Consulter le contexte
$ cat .parac/memory/context/current_state.yaml
# → Phase 4 en cours, 60% complet

# Étape 2: Vérifier le roadmap
$ cat .parac/roadmap/roadmap.yaml
# → Priority 1: CLI commands (en cours)

# Étape 3: Adopter le bon agent
$ cat .parac/agents/specs/coder.md
# → Persona Coder Agent

# Étape 4: Implémenter selon standards
$ cat .parac/policies/CODE_STYLE.md
# → Python 3.10+, Pydantic v2, Architecture hexagonale

# Étape 5: Logger l'action
$ echo "[2026-01-04 15:00:00] [CoderAgent] [IMPLEMENTATION] Added REST API endpoints for workflow execution" >> .parac/memory/logs/agent_actions.log

# Étape 6: Mettre à jour l'état
$ # Modifier .parac/memory/context/current_state.yaml
```

### Exemple 2: Décision Architecture

```bash
# Assistant IA reçoit: "Comment gérer les erreurs de workflow?"

# Étape 1: Consulter l'architect
$ cat .parac/agents/specs/architect.md

# Étape 2: Vérifier les décisions existantes
$ cat .parac/roadmap/decisions.md

# Étape 3: Analyser l'architecture actuelle
$ cat .parac/memory/knowledge/architecture.md

# Étape 4: Proposer une décision
# → Documenter dans .parac/roadmap/decisions.md

# Étape 5: Logger la décision
$ echo "[2026-01-04 15:10:00] [ArchitectAgent] [DECISION] Use exception hierarchy for workflow errors" >> .parac/memory/logs/decisions.log
```

### Exemple 3: Code Review

```bash
# Assistant IA reçoit: "Review ce pull request"

# Étape 1: Adopter Reviewer persona
$ cat .parac/agents/specs/reviewer.md

# Étape 2: Vérifier les standards
$ cat .parac/policies/CODE_STYLE.md
$ cat .parac/policies/TESTING.md

# Étape 3: Analyser le code
# → Comparer avec les standards

# Étape 4: Logger la review
$ echo "[2026-01-04 15:20:00] [ReviewerAgent] [REVIEW] PR #42 approved with minor comments" >> .parac/memory/logs/agent_actions.log
```

---

## 🌟 Best Practices

### 1. Traçabilité Totale
**Tout doit être loggé dans .parac/**
- Actions d'agents
- Décisions importantes
- Changements d'état
- Questions ouvertes

### 2. Incrémentalité
**Petits changements validables**
- Commit fréquents
- Tests à chaque changement
- Mise à jour .parac/ synchrone

### 3. Cohérence
**Le .parac/ doit toujours refléter la réalité**
- État = état réel du projet
- Roadmap = plan réel
- Logs = actions réelles

### 4. Communication
**Le .parac/ est le canal de communication entre assistants**
- Pas de mémoire privée
- Tout dans .parac/
- Lecture obligatoire avant action

---

## 🔄 Migration Entre IDEs

### Si vous changez d'IDE

```bash
# 1. Régénérer les instructions pour le nouvel IDE
paracle ide sync --copy

# 2. Copier les fichiers générés
# → Les fichiers dans .parac/integrations/ide/ sont prêts

# 3. Tester que l'assistant lit .parac/
# → Demander à l'assistant de lire .parac/GOVERNANCE.md

# 4. Vérifier le logging
# → Vérifier que .parac/memory/logs/ est mis à jour
```

**Important**: Le contenu du `.parac/` est **IDE-agnostique**. Seuls les fichiers dans `.parac/integrations/ide/` changent de format.

---

## 📚 Documentation Additionnelle

### Fichiers Clés à Lire

1. **`.parac/GOVERNANCE.md`** - Règles du projet
2. **`.parac/STRUCTURE.md`** - Structure détaillée
3. **`.parac/MAINTENANCE.md`** - Guide de maintenance
4. **`.parac/agents/SKILL_ASSIGNMENTS.md`** - Skills par agent
5. **`.parac/roadmap/roadmap.yaml`** - Planification

### Resources Externes

- [Architecture Overview](../../docs/architecture.md)
- [API-First CLI](../../docs/api-first-cli.md)
- [Workflow Management](../../docs/workflow-management.md)
- [Getting Started](../../docs/getting-started.md)

---

## ✨ Résumé: Maximiser l'Utilisation du .parac/

### Pour les Utilisateurs

1. **Initialisez**: `paracle init`
2. **Configurez**: Agents, workflows, outils
3. **Synchronisez**: `paracle sync` régulièrement
4. **Validez**: `paracle validate` avant commits

### Pour les Assistants IA (TOUS)

1. **LIRE**: `.parac/` avant toute action
2. **ADOPTER**: Le bon agent persona
3. **SUIVRE**: Les standards du projet
4. **LOGGER**: Toutes les actions importantes
5. **METTRE À JOUR**: La mémoire après chaque changement

### Le Mantra

> **"Consulte .parac/, suis .parac/, logue dans .parac/"**

---

**Le `.parac/` n'est pas juste un dossier de config.**
**C'est le cerveau de votre projet.**
**Utilisez-le pleinement. 🧠✨**
