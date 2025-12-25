# 🔄 Guide de Synchronisation PARACLE

Guide pratique pour maintenir les agents et le manifeste synchronisés.

## 🚀 Installation (Une fois)

### Windows
```powershell
.\.parac\hooks\install-hooks.ps1
```

### Unix/Linux/Mac
```bash
bash .parac/hooks/install-hooks.sh
```

✅ **C'est fait !** Le système se synchronise maintenant automatiquement.

---

## 📝 Workflows Quotidiens

### Workflow Standard (Recommandé)

```bash
# 1. Modifier un agent
vim .parac/agents/specs/coder.md

# 2. Commiter normalement
git add .parac/agents/specs/coder.md
git commit -m "Enhanced coder agent capabilities"

# → Le manifeste est automatiquement mis à jour et inclus dans le commit ✅
```

**Avantages** :
- ✅ Zéro effort manuel
- ✅ Toujours synchronisé
- ✅ Historique git cohérent

### Workflow Développement Actif

```bash
# Terminal 1: Lancer le watcher
python .parac/hooks/sync-watch.py

# Terminal 2: Éditer librement
code .parac/agents/specs/

# → Le manifeste se régénère à chaque sauvegarde ✅
```

**Avantages** :
- ✅ Feedback immédiat
- ✅ Voir les changements en direct
- ✅ Pas besoin de commit pour tester

### Workflow Manuel (Contrôle total)

```bash
# Modifier plusieurs agents
vim .parac/agents/specs/pm.md
vim .parac/agents/specs/architect.md
vim .parac/agents/specs/tester.md

# Régénérer une seule fois
paracle parac sync --manifest

# Vérifier
paracle agents list
git diff .parac/manifest.yaml
```

**Avantages** :
- ✅ Contrôle total
- ✅ Batch updates
- ✅ Validation avant commit

---

## 🔍 Vérification de Synchronisation

### Vérifier l'état actuel

```bash
# Lister tous les agents découverts
paracle agents list

# Comparer avec le manifeste
cat .parac/manifest.yaml | grep "agent_count:"

# Voir la date de dernière génération
grep generated_at .parac/manifest.yaml
```

### Vérifier si un agent est à jour

```bash
# Voir les métadonnées de l'agent
paracle agents get coder

# Comparer avec le fichier source
cat .parac/agents/specs/coder.md | head -20
```

### Vérifier le statut git

```bash
# Si le manifeste est modifié mais pas staged
git status .parac/manifest.yaml

# Si des agents sont modifiés
git diff .parac/agents/specs/
```

---

## 📦 Scénarios Courants

### ➕ Créer un Nouvel Agent

```bash
# 1. Créer le fichier
cat > .parac/agents/specs/deployer.md << 'EOF'
# Deployer Agent

## Role
Handles deployment and release management.

## Responsibilities
- Deploy to environments
- Manage releases
- Monitor deployments
EOF

# 2. Régénération (automatique si hooks installés)
paracle parac sync --manifest

# 3. Vérifier
paracle agents list | grep deployer
```

### ✏️ Modifier un Agent Existant

```bash
# 1. Éditer
code .parac/agents/specs/coder.md
# Ajouter nouvelles capacités, standards, etc.

# 2. Si hooks installés: juste commiter
git commit -am "Updated coder agent with new standards"

# Sinon: régénérer manuellement
paracle parac sync --manifest
```

### ❌ Supprimer un Agent

```bash
# 1. Supprimer le fichier
git rm .parac/agents/specs/old-agent.md

# 2. Régénérer
paracle parac sync --manifest

# 3. Vérifier qu'il n'apparaît plus
paracle agents list
```

### 🔄 Fusionner des Modifications d'Agent

```bash
# Après un git pull avec conflits sur un agent
git status

# 1. Résoudre les conflits
vim .parac/agents/specs/coder.md
git add .parac/agents/specs/coder.md

# 2. Régénérer le manifeste
paracle parac sync --manifest

# 3. Compléter la fusion
git commit
```

---

## 🔧 Commandes Utiles

### Voir tous les agents

```bash
# Format table
paracle agents list

# Format JSON (pour scripting)
paracle agents list --format=json

# Format YAML
paracle agents list --format=yaml
```

### Obtenir un agent spécifique

```bash
# Métadonnées
paracle agents get pm

# Spec complète
paracle agents get pm --spec

# JSON pour parsing
paracle agents get pm --format=json
```

### Exporter pour intégration

```bash
# Export JSON
paracle agents export > agents.json

# Export YAML
paracle agents export --format=yaml -o agents.yaml

# Pipe vers autre outil
paracle agents list --format=json | jq '.[] | .name'
```

### Forcer la régénération

```bash
# Régénération complète
paracle parac sync --manifest

# Seulement manifeste (pas git/metrics)
paracle parac sync --manifest --no-git --no-metrics
```

---

## 🐛 Dépannage

### Le manifeste n'est pas à jour

**Symptôme** : Le manifeste ne reflète pas les dernières modifications

**Solution** :
```bash
# Forcer la régénération
paracle parac sync --manifest --no-git --no-metrics

# Vérifier la date
grep generated_at .parac/manifest.yaml
```

### Les hooks git ne fonctionnent pas

**Symptôme** : Le manifeste n'est pas régénéré lors du commit

**Vérifications** :
```bash
# 1. Vérifier que le hook existe
ls .git/hooks/pre-commit*

# 2. Vérifier qu'il est exécutable
cat .git/hooks/pre-commit

# 3. Réinstaller
.\.parac\hooks\install-hooks.ps1
```

**Windows spécifique** :
```powershell
# Vérifier PowerShell
where.exe pwsh

# Si pas trouvé, installer PowerShell 7+
winget install Microsoft.PowerShell
```

### Le watcher ne détecte pas les changements

**Solution 1** : Installer watchdog
```bash
pip install watchdog
python .parac/hooks/sync-watch.py
```

**Solution 2** : Mode polling
```bash
python .parac/hooks/sync-watch.py --interval=1
```

### Conflit git sur manifest.yaml

**Symptôme** : Conflits lors d'un merge sur `manifest.yaml`

**Solution** :
```bash
# Toujours prendre leur version, puis régénérer
git checkout --theirs .parac/manifest.yaml
paracle parac sync --manifest
git add .parac/manifest.yaml
```

**Astuce** : Configurer git pour auto-résoudre :
```bash
# Dans .gitattributes
.parac/manifest.yaml merge=ours
```

---

## 🎯 Meilleures Pratiques

### ✅ À Faire

- ✅ Installer les git hooks dès le début
- ✅ Régénérer le manifeste après chaque modification d'agent
- ✅ Commiter le manifeste avec les modifications d'agents
- ✅ Utiliser `sync-watch.py` pendant développement actif
- ✅ Vérifier `paracle agents list` après modifications

### ❌ À Éviter

- ❌ Modifier manuellement `manifest.yaml`
- ❌ Commiter agents sans régénérer le manifeste
- ❌ Ignorer les warnings du watcher
- ❌ Supprimer `.parac/manifest.yaml` sans le régénérer

---

## 🚀 Automatisation Avancée

### CI/CD (GitHub Actions)

```yaml
# .github/workflows/sync-agents.yml
name: Sync Agent Manifest

on:
  push:
    paths:
      - '.parac/agents/specs/*.md'

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4

      - name: Install Paracle
        run: |
          pip install uv
          uv sync

      - name: Regenerate Manifest
        run: uv run paracle parac sync --manifest

      - name: Commit if changed
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "actions@github.com"
          git add .parac/manifest.yaml
          git diff --quiet && git diff --staged --quiet || \
            git commit -m "chore: regenerate agent manifest [skip ci]"
          git push
```

### Pre-commit Framework

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: paracle-sync
        name: Sync PARACLE Manifest
        entry: paracle parac sync --manifest --no-git --no-metrics
        language: system
        files: ^\.parac/agents/specs/.*\.md$
```

### VS Code Task

```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "PARACLE: Sync Manifest",
      "type": "shell",
      "command": "paracle parac sync --manifest",
      "problemMatcher": [],
      "group": {
        "kind": "build",
        "isDefault": false
      }
    },
    {
      "label": "PARACLE: Watch Agents",
      "type": "shell",
      "command": "python .parac/hooks/sync-watch.py",
      "isBackground": true,
      "problemMatcher": []
    }
  ]
}
```

---

## 📚 Ressources

- [Agent Discovery System Documentation](../docs/agent-discovery.md)
- [ADR-008: Agent Discovery System](../.parac/roadmap/decisions.md#adr-008)
- [Hooks README](../.parac/hooks/README.md)
- [Agent Specifications](../.parac/agents/specs/)

---

**💡 Astuce** : Après installation des hooks, vous n'avez plus à vous préoccuper de la synchronisation - elle se fait automatiquement ! 🎉
