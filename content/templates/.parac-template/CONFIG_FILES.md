# Fichiers de Configuration du .parac/

## Vue d'Ensemble

Le `.parac/` utilise **deux fichiers de configuration distincts** avec des responsabilités différentes:

```
.parac/
├── project.yaml          # Configuration PROJET (manuel)
└── manifest.yaml         # État WORKSPACE (auto-généré)
```

---

## 📋 project.yaml - Configuration Projet

**Type**: Fichier **édité manuellement** par l'utilisateur
**Rôle**: Configuration business/organisationnelle du projet
**Quand le modifier**: Setup initial, changements de team, nouvelles configs

### Contenu

```yaml
name: paracle
version: 0.0.1
description: Framework multi-agent...

# IDENTITY - Qui possède ce projet?
identity:
  organization: IbIFACE-Tech
  repository: paracle
  license: Apache-2.0
  homepage: https://github.com/...

# TEAM - Qui maintient?
team:
  maintainers:
    - role: lead
      contact: team@ibiface-tech.com

# DEFAULTS - Configurations par défaut
defaults:
  python_version: "3.10"
  agent_framework: internal
  model_provider: openai
  default_model: gpt-4
  orchestrator: internal

# METADATA - Info projet
metadata:
  created_at: "2025-12-24"
  phase: "Phase 4"
  status: active
  tags:
    - multi-agent
    - ai-framework

# LOGGING - Configuration logs
logging:
  level: INFO
  format: json
  rotation: daily
```

### Responsabilités

- ✅ Identité organisationnelle (org, repo, license)
- ✅ Équipe et maintainers
- ✅ Configurations par défaut (Python version, providers)
- ✅ Phase et status du projet
- ✅ Logging configuration
- ✅ Tags et catégorisation

### Quand Modifier

```bash
# Nouveau maintainer
team:
  maintainers:
    - role: lead
      contact: lead@example.com
    - role: contributor
      contact: dev@example.com

# Changement de provider par défaut
defaults:
  model_provider: anthropic
  default_model: claude-3-sonnet

# Nouvelle phase
metadata:
  phase: "Phase 5"
  status: in_progress
```

---

## 🔄 manifest.yaml - État Workspace

**Type**: Fichier **auto-généré** par les commandes Paracle
**Rôle**: État technique du workspace et des agents configurés
**Quand il change**: `paracle agents create`, `paracle sync`, `paracle validate`

### Contenu

```yaml
schema_version: '1.0'
generated_at: '2026-01-04T15:30:00.123456'  # ← Timestamp auto

workspace:
  name: paracle                        # ← Repris de project.yaml
  version: 0.0.1
  parac_version: 0.0.1
  root: /path/to/.parac

# AGENTS - Liste des agents configurés
agents:
  - id: architect
    name: System Architect Agent
    role: System architecture design...
    spec_file: agents/specs/architect.md
    capabilities:
      - architecture design
      - technical decisions

  - id: coder
    name: Coder Agent
    role: Implementation of features...
    spec_file: agents/specs/coder.md
    capabilities:
      - code implementation
      - code quality

# METADATA - État du workspace
metadata:
  agent_count: 6
  specs_directory: agents/specs/
  last_sync: '2026-01-04T15:30:00'
```

### Responsabilités

- ✅ Liste des agents configurés (id, role, capabilities)
- ✅ Chemins vers les specs d'agents
- ✅ Métadonnées de génération (timestamp)
- ✅ État technique du workspace
- ✅ Version du schéma manifest

### Quand Il Change

```bash
# Création d'un agent
$ paracle agents create my-agent
# → manifest.yaml mis à jour automatiquement

# Synchronisation
$ paracle sync
# → generated_at mis à jour
# → Liste des agents re-scannée

# Validation
$ paracle validate
# → Vérifie cohérence avec les specs
```

---

## 🔍 Comparaison Côte à Côte

| Aspect            | project.yaml             | manifest.yaml            |
| ----------------- | ------------------------ | ------------------------ |
| **Édition**       | ✍️ Manuel                 | 🤖 Auto-généré            |
| **Rôle**          | Config projet/business   | État technique workspace |
| **Quand changer** | Setup, team, configs     | Commandes paracle        |
| **Contient**      | Identity, team, defaults | Agents, specs, état      |
| **Version**       | Gérée manuellement       | Timestamp auto           |
| **Commit Git**    | ✅ Oui, toujours          | ✅ Oui, track changes     |
| **Modifiable**    | ✅ Oui, encouragé         | ⚠️ Non, regenerate        |

---

## 🎯 Qui Lit Quoi?

### Les Assistants IA

**Priorité de lecture:**
```
1. project.yaml       → Comprendre le projet (identity, phase, defaults)
2. manifest.yaml      → Connaître les agents disponibles
3. agents/specs/      → Détails des agents à adopter
```

### Les Commandes CLI

```bash
# paracle status
→ Lit: project.yaml (phase, status)
→ Lit: manifest.yaml (agents count)

# paracle agents list
→ Lit: manifest.yaml (liste des agents)

# paracle sync
→ Lit: project.yaml (config)
→ Met à jour: manifest.yaml (agents, timestamp)
```

---

## 📝 Recommandations

### Pour les Utilisateurs

1. **Modifier project.yaml** pour:
   - Changer identity/team
   - Ajuster defaults
   - Mettre à jour phase/status
   - Configurer logging

2. **NE PAS modifier manifest.yaml** directement:
   - Laissez les commandes le gérer
   - Utilisez `paracle agents create/update`
   - Utilisez `paracle sync` pour régénérer

3. **Commit les deux fichiers**:
   ```bash
   git add .parac/project.yaml
   git add .parac/manifest.yaml
   git commit -m "Update project config and agent manifest"
   ```

### Pour les Commandes Paracle

```python
# Lire project config
def load_project_config():
    return yaml.safe_load(open('.parac/project.yaml'))

# Lire workspace state
def load_workspace_manifest():
    return yaml.safe_load(open('.parac/manifest.yaml'))

# Mettre à jour manifest (auto)
def update_manifest():
    manifest = scan_agents()
    manifest['generated_at'] = datetime.now().isoformat()
    save_yaml('.parac/manifest.yaml', manifest)
```

---

## 🔄 Workflow Typique

### Setup Initial

```bash
# 1. Créer project.yaml (manuel)
$ vim .parac/project.yaml
# → Identity, team, defaults

# 2. Initialiser workspace
$ paracle init
# → Génère manifest.yaml automatiquement

# 3. Créer agents
$ paracle agents create architect
$ paracle agents create coder
# → manifest.yaml mis à jour avec liste agents
```

### Développement

```bash
# Changer phase du projet
$ vim .parac/project.yaml
metadata:
  phase: "Phase 5"

# Synchroniser
$ paracle sync
# → manifest.yaml regenerated_at updated

# Ajouter un agent
$ paracle agents create analyst
# → manifest.yaml mis à jour (agent_count: 7)
```

### Migration/Changement

```bash
# Changer provider par défaut
$ vim .parac/project.yaml
defaults:
  model_provider: anthropic

# Valider cohérence
$ paracle validate
# → Vérifie project.yaml + manifest.yaml
```

---

## ⚡ Résolution de Conflits

### manifest.yaml Obsolète

```bash
# Régénérer depuis les specs actuelles
$ paracle sync --force

# Ou validation
$ paracle validate --fix
```

### project.yaml et manifest.yaml Incohérents

```yaml
# project.yaml
name: paracle
version: 0.0.1

# manifest.yaml (généré)
workspace:
  name: paracle-old  # ← Incohérent!
  version: 0.0.1
```

**Solution:**
```bash
$ paracle sync
# → manifest.yaml mis à jour avec name de project.yaml
```

---

## 🎓 Règles d'Or

1. **project.yaml = Source de vérité manuelle**
   - Tu le modifies directement
   - Il définit l'identité du projet

2. **manifest.yaml = État dérivé automatique**
   - Généré par les commandes
   - Ne le modifie jamais manuellement

3. **En cas de doute:**
   ```bash
   paracle sync  # Re-génère manifest.yaml
   paracle validate  # Vérifie cohérence
   ```

4. **Assistants IA: Lire les deux**
   ```
   project.yaml → Contexte business/org
   manifest.yaml → Agents disponibles
   ```

---

## 📚 Voir Aussi

- **[STRUCTURE.md](../STRUCTURE.md)** - Structure complète du .parac/
- **[USING_PARAC.md](../USING_PARAC.md)** - Guide d'utilisation
- **[UNIVERSAL_AI_INSTRUCTIONS.md](../UNIVERSAL_AI_INSTRUCTIONS.md)** - Instructions IA

---

**En résumé:**
- **project.yaml** = Configuration projet (manuel, identity, team, defaults)
- **manifest.yaml** = État workspace (auto, agents, specs, timestamp)

**Règle simple:** Modifie project.yaml, laisse manifest.yaml aux commandes! ✨
