# 🚀 Quick Reference - Synchronisation PARACLE

Aide-mémoire rapide pour la synchronisation des agents.

## Installation (Une fois)

```bash
# Windows
.\.parac\hooks\install-hooks.ps1

# Linux/Mac
bash .parac/hooks/install-hooks.sh
```

## Commandes Principales

```bash
# Lister les agents
paracle agents list

# Voir un agent
paracle agents get <id>

# Spec complète
paracle agents get <id> --spec

# Régénérer manifeste
paracle parac sync --manifest

# Export JSON
paracle agents export
```

## Workflows

### Standard (avec git hooks)
```bash
vim .parac/agents/specs/coder.md
git commit -am "Update"  # Auto-sync ✅
```

### Développement
```bash
# Terminal 1
python .parac/hooks/sync-watch.py

# Terminal 2
code .parac/agents/specs/
```

### Manuel
```bash
vim .parac/agents/specs/*.md
paracle parac sync --manifest
```

## Dépannage

```bash
# Forcer régénération
paracle parac sync --manifest --no-git --no-metrics

# Réinstaller hooks
.\.parac\hooks\install-hooks.ps1

# Vérifier date manifeste
grep generated_at .parac/manifest.yaml
```

## Fichiers Clés

- `.parac/agents/specs/*.md` - Source de vérité (agents)
- `.parac/manifest.yaml` - Auto-généré (ne pas éditer)
- `.git/hooks/pre-commit*` - Hooks d'auto-sync
- `.parac/hooks/sync-watch.py` - Watcher temps réel

## Plus d'Infos

- Guide complet : `docs/synchronization-guide.md`
- Documentation : `docs/agent-discovery.md`
- Hooks README : `.parac/hooks/README.md`
