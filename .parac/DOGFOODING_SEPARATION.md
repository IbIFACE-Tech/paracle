# Dogfooding: Séparation des Responsabilités

> **Contexte**: Paracle utilise Paracle pour concevoir Paracle (dogfooding)

## 🎯 Principe Fondamental

Ce projet a **3 couches distinctes** qui ne doivent JAMAIS être mélangées :

```
┌─────────────────────────────────────────────────────────────┐
│ COUCHE 1: PRODUIT (packages/)                               │
│ Le framework Paracle que nous développons                   │
│ ➜ Publié sur PyPI                                          │
│ ➜ Utilisé par nos clients                                  │
└─────────────────────────────────────────────────────────────┘
                          ↓ utilise
┌─────────────────────────────────────────────────────────────┐
│ COUCHE 2: UTILISATEUR (.parac/)                             │
│ Notre utilisation de Paracle pour gérer notre projet        │
│ ➜ Dogfooding: nous sommes notre propre client             │
│ ➜ Exemple de ce qu'un utilisateur aurait                  │
└─────────────────────────────────────────────────────────────┘
                          ↕ distinct de
┌─────────────────────────────────────────────────────────────┐
│ COUCHE 3: DÉVELOPPEMENT (scripts/)                          │
│ Outils pour développer le framework Paracle                 │
│ ➜ PAS pour les utilisateurs de Paracle                    │
│ ➜ Outils de build/release/test du framework               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Cartographie des Responsabilités

### **COUCHE 1: `packages/` - Le PRODUIT**

**Rôle**: Code source du framework Paracle

**Contenu**:
- `packages/paracle_core/` - Core utilities
- `packages/paracle_api/` - REST API
- `packages/paracle_cli/` - CLI commands
- `packages/paracle_agents/` - Agent system
- etc.

**Publié**: Oui, sur PyPI via `uv publish`

**Utilisé par**:
- ✅ Nos clients (utilisateurs externes)
- ✅ Nous-mêmes via `.parac/` (dogfooding)

**Exemples**:
- `packages/paracle_cli/main.py` - CLI entrypoint
- `packages/paracle_core/governance.py` - Governance logic

---

### **COUCHE 2: `.parac/` - L'UTILISATEUR (Dogfooding)**

**Rôle**: Notre utilisation de Paracle pour gérer le développement de Paracle

**Contenu**:
- `.parac/agents/` - Nos agents (CoderAgent, TesterAgent, etc.)
- `.parac/memory/` - État du projet, logs, knowledge
- `.parac/roadmap/` - Notre roadmap, phases, décisions
- `.parac/policies/` - Nos politiques (code style, testing, security)
- `.parac/tools/hooks/` - **Outils de gouvernance** (maintenir `.parac/`)

**Publié**: Non, c'est notre workspace privé

**Utilisé par**:
- ✅ Nous (équipe Paracle)
- ✅ Agents IA (Claude, Copilot) pour comprendre le projet

**Exemples**:
- `.parac/agents/specs/coder.md` - Notre agent CoderAgent
- `.parac/memory/context/current_state.yaml` - État du projet Paracle
- `.parac/tools/hooks/agent-logger.py` - Logger les actions agents
- `.parac/roadmap/roadmap.yaml` - Roadmap de Paracle

**Important**: C'est ce qu'un **client de Paracle** aurait dans son propre projet !

---

### **COUCHE 3: `scripts/` - Le DÉVELOPPEMENT**

**Rôle**: Outils pour développer et maintenir le framework Paracle

**Contenu**:
- `scripts/bump_version.py` - Incrémenter version du framework
- `scripts/generate_changelog.py` - Générer CHANGELOG.md
- `scripts/git_commit_automation.py` - Automatisation git
- `scripts/fix_security_tests.py` - Fix tests du framework
- `scripts/baseline_profiling.py` - Profiling performance

**Publié**: Non, outils internes

**Utilisé par**:
- ✅ Développeurs du framework Paracle
- ❌ PAS par les utilisateurs de Paracle

**Exemples**:
- `scripts/bump_version.py` - Bump version dans `pyproject.toml`
- `scripts/generate_changelog.py` - Génère CHANGELOG.md du framework

**Important**: Ces scripts ne seraient **PAS** dans le `.parac/` d'un client !

---

## 🚫 Anti-Patterns à Éviter

### ❌ **Mélanger `.parac/` et `scripts/`**

**WRONG**:
```
scripts/
  log-action.py          # ❌ Outil de gouvernance dans scripts/
  agent-logger-wrapper.ps1  # ❌ Devrait être dans .parac/tools/hooks/
```

**RIGHT**:
```
.parac/tools/hooks/
  agent-logger.py        # ✅ Outil de gouvernance
  log-fix.ps1            # ✅ Helper pour logging
```

### ❌ **Mettre des outils de dev dans `.parac/`**

**WRONG**:
```
.parac/tools/
  bump_version.py        # ❌ Outil de développement du framework
  publish_to_pypi.py     # ❌ Release du framework
```

**RIGHT**:
```
scripts/
  bump_version.py        # ✅ Outil de développement
  publish_to_pypi.py     # ✅ Release du framework
```

### ❌ **Code framework dans `.parac/`**

**WRONG**:
```
.parac/
  src/                   # ❌ Code source dans .parac/
  lib/                   # ❌ Librairies dans .parac/
```

**RIGHT**:
```
packages/
  paracle_core/          # ✅ Code source du framework
  paracle_api/           # ✅ Librairies du framework
```

---

## ✅ Règles de Décision

### Où placer un nouveau fichier ?

**Question 1**: Est-ce du code qui sera **publié sur PyPI** ?
- ✅ OUI → `packages/paracle_*/`

**Question 2**: Est-ce un outil de **gouvernance** pour maintenir `.parac/` ?
- ✅ OUI → `.parac/tools/hooks/`

**Question 3**: Est-ce un outil pour **développer le framework** ?
- ✅ OUI → `scripts/`

**Question 4**: Est-ce de la **configuration/mémoire** de notre projet ?
- ✅ OUI → `.parac/memory/`, `.parac/roadmap/`, etc.

---

## 📋 Exemples Concrets

### **Exemple 1: Logger une action d'agent**

**But**: Tracer les actions dans `.parac/memory/logs/agent_actions.log`

**Emplacement**: `.parac/tools/hooks/agent-logger.py` ✅

**Raison**:
- C'est de la **gouvernance** (maintient `.parac/`)
- Un **utilisateur** de Paracle aurait ce script
- C'est du **dogfooding**

**Usage**:
```bash
python .parac/tools/hooks/agent-logger.py CoderAgent BUGFIX "Fixed X"
```

### **Exemple 2: Bump version du framework**

**But**: Incrémenter version dans `pyproject.toml`

**Emplacement**: `scripts/bump_version.py` ✅

**Raison**:
- C'est du **développement** du framework
- Un **utilisateur** de Paracle n'en a PAS besoin
- Modifie le **produit** (packages/)

**Usage**:
```bash
python scripts/bump_version.py --patch
```

### **Exemple 3: Commit automatisé par ReleaseManager**

**But**: Automatiser les commits git pour releases

**Emplacement**: `scripts/git_commit_automation.py` ✅

**Raison**:
- C'est du **développement** (workflow release du framework)
- Pas dans `.parac/` car spécifique au framework Paracle
- Un utilisateur utiliserait `paracle` CLI, pas ces scripts

**Usage**:
```bash
python scripts/releasemanager_commit.py --message "Release v1.0.3"
```

### **Exemple 4: Synchroniser manifest.yaml**

**But**: Régénérer `.parac/agents/manifest.yaml` quand specs modifiés

**Emplacement**: `.parac/tools/hooks/sync-watch.py` ✅

**Raison**:
- C'est de la **gouvernance** (maintient `.parac/`)
- Un **utilisateur** de Paracle aurait ce script
- Surveille `.parac/agents/specs/`

**Usage**:
```bash
python .parac/tools/hooks/sync-watch.py
```

---

## 🔍 Test de Cohérence

Pour vérifier si un fichier est au bon endroit, demandez-vous :

### "Un client utilisant Paracle aurait-il ce fichier ?"

- ✅ **OUI** → Doit être dans `.parac/` (dogfooding)
- ❌ **NON** → Doit être dans `scripts/` (développement) ou `packages/` (produit)

### Exemples:

| Fichier                 | Client l'aurait ?     | Emplacement correct      |
| ----------------------- | --------------------- | ------------------------ |
| `agent-logger.py`       | ✅ Oui (gouvernance)   | `.parac/tools/hooks/`    |
| `bump_version.py`       | ❌ Non (dev framework) | `scripts/`               |
| `governance.py`         | ✅ Oui (via PyPI)      | `packages/paracle_core/` |
| `generate_changelog.py` | ❌ Non (dev framework) | `scripts/`               |
| `current_state.yaml`    | ✅ Oui (son projet)    | `.parac/memory/context/` |

---

## 📚 Documentation Complémentaire

- **[GOVERNANCE.md](GOVERNANCE.md)** - Règles de gouvernance du `.parac/`
- **[STRUCTURE.md](STRUCTURE.md)** - Structure complète du `.parac/`
- **[content/docs/architecture.md](../content/docs/architecture.md)** - Architecture du framework
- **[scripts/README.md](../scripts/README.md)** - Documentation des scripts de dev

---

## 🎯 Résumé - Règle d'Or

```
┌─────────────────────────────────────────────────────────────┐
│                    RÈGLE D'OR                               │
│                                                             │
│  .parac/      = Ce qu'un CLIENT de Paracle aurait         │
│  scripts/     = Ce que NOUS (devs) utilisons               │
│  packages/    = Ce que nous PUBLIONS sur PyPI              │
│                                                             │
│  Ne JAMAIS mélanger ces 3 couches !                        │
└─────────────────────────────────────────────────────────────┘
```

**Quand vous hésitez**: Posez-vous la question "Un client l'aurait ?"
- OUI → `.parac/`
- NON → `scripts/` ou `packages/`

---

**Version**: 1.0
**Date**: 2026-01-10
**Auteur**: Équipe Paracle
**Status**: Active
