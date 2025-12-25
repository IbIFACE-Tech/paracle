# Paracle Governance Hooks

Ce répertoire contient les scripts de mise à jour automatique de `.parac/`.

## Hooks Disponibles

### pre-session.py
Vérifie l'état de `.parac/` avant une session de travail.

```bash
python .parac/hooks/pre-session.py
```

### post-session.py
Met à jour `.parac/` après une session de travail.

```bash
python .parac/hooks/post-session.py --summary "Description des changements"
```

### validate.py
Valide la cohérence et la syntaxe de tous les fichiers `.parac/`.

```bash
python .parac/hooks/validate.py
```

### sync-state.py
Synchronise `current_state.yaml` avec l'état réel du projet (git, tests, etc.).

```bash
python .parac/hooks/sync-state.py
```

## Intégration Git

### Pre-commit Hook

Ajouter dans `.git/hooks/pre-commit`:

```bash
#!/bin/bash
python .parac/hooks/validate.py
if [ $? -ne 0 ]; then
    echo "❌ .parac validation failed"
    exit 1
fi
```

### Post-merge Hook

Ajouter dans `.git/hooks/post-merge`:

```bash
#!/bin/bash
python .parac/hooks/sync-state.py
```

## Intégration Makefile

```makefile
# Validation .parac
parac-check:
	python .parac/hooks/validate.py

parac-sync:
	python .parac/hooks/sync-state.py

parac-status:
	python .parac/hooks/status.py
```

## Intégration Claude Code

Les hooks peuvent être déclenchés via Claude Code hooks dans `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": {
      "*": "python .parac/hooks/pre-session.py --check"
    }
  }
}
```
