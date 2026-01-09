# Paracle Governance Hooks

Ce répertoire contient les scripts de mise à jour automatique de `.parac/`.

## 🔄 Synchronisation des Agents

### Scripts de Synchronisation

#### `install-hooks.ps1` / `install-hooks.sh`
Installe les git hooks pour auto-régénérer le manifeste des agents.

**Installation (Windows)** :
```powershell
.\.parac\tools\hooks\install-hooks.ps1
```

**Installation (Unix/Linux/Mac)** :
```bash
bash .parac/tools/hooks/install-hooks.sh
```

**Effet** : Régénère automatiquement `.parac/manifest.yaml` lors du commit si des agents sont modifiés.

#### `sync-watch.py`
Surveille `.parac/agents/specs/` et régénère le manifeste en temps réel.

**Usage** :
```bash
# Mode watchdog (temps réel, recommandé)
pip install watchdog
python .parac/tools/hooks/sync-watch.py

# Mode polling (sans dépendances)
python .parac/tools/hooks/sync-watch.py --interval=2
```

### Workflows de Synchronisation

#### Workflow 1 : Git Hooks (Recommandé)
```bash
# 1. Installer les hooks une fois
.\.parac\tools\hooks\install-hooks.ps1

# 2. Modifier un agent
vim .parac/agents/specs/coder.md

# 3. Commiter
git commit -am "Updated coder agent"
# → Le manifeste est automatiquement régénéré et inclus
```

#### Workflow 2 : Watch Mode (Développement)
```bash
# Terminal 1: Lancer le watcher
python .parac/tools/hooks/sync-watch.py

# Terminal 2: Modifier les agents
vim .parac/agents/specs/architect.md
# → Régénération automatique à chaque sauvegarde
```

#### Workflow 3 : Manuel
```bash
# Modifier un agent
vim .parac/agents/specs/tester.md

# Régénérer manuellement
paracle sync --manifest

# Vérifier
paracle agents get tester
```

## 📝 Logging des Actions

### agent-logger.py
Logger pour tracer les actions des agents dans `.parac/memory/logs/`.

```bash
# Logger une action
python .parac/tools/hooks/agent-logger.py CoderAgent IMPLEMENTATION "Added webhook system"

# Logger une décision
python .parac/tools/hooks/agent-logger.py ArchitectAgent DECISION "Use event sourcing" \
  --decision \
  --rationale "Better auditability" \
  --impact "Medium impact on persistence"
```

Utilisation depuis Python:

```python
from parac.tools.hooks.agent_logger import AgentLogger

logger = AgentLogger()
logger.log_action("CoderAgent", "IMPLEMENTATION", "Added new feature")
logger.log_decision(
    "ArchitectAgent",
    "Use hexagonal architecture",
    "Better separation of concerns",
    "High impact - restructure packages"
)
```

### pre-session.py
Vérifie l'état de `.parac/` avant une session de travail.

```bash
python .parac/tools/hooks/pre-session.py
```

### post-session.py
Met à jour `.parac/` après une session de travail.

```bash
python .parac/tools/hooks/post-session.py --summary "Description des changements"
```

### validate.py
Valide la cohérence et la syntaxe de tous les fichiers `.parac/`.

```bash
python .parac/tools/hooks/validate.py
```

### sync-state.py
Synchronise `current_state.yaml` avec l'état réel du projet (git, tests, etc.).

```bash
python .parac/tools/hooks/sync-state.py
```

## Intégration Git

### Pre-commit Hook

Ajouter dans `.git/hooks/pre-commit`:

```bash
#!/bin/bash
python .parac/tools/hooks/validate.py
if [ $? -ne 0 ]; then
    echo "❌ .parac validation failed"
    exit 1
fi
```

### Post-merge Hook

Ajouter dans `.git/hooks/post-merge`:

```bash
#!/bin/bash
python .parac/tools/hooks/sync-state.py
```

## Intégration Makefile

```makefile
# Validation .parac
parac-check:
	python .parac/tools/hooks/validate.py

parac-sync:
	python .parac/tools/hooks/sync-state.py

parac-status:
	python .parac/tools/hooks/status.py
```

## Intégration Claude Code

Les hooks peuvent être déclenchés via Claude Code hooks dans `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": {
      "*": "python .parac/tools/hooks/pre-session.py --check"
    }
  }
}
```
