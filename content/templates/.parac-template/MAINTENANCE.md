# .parac Maintenance Guide

## Vue d'ensemble

Le système de maintenance automatique du `.parac/` garde le workspace synchronisé avec les changements du projet.

## 🔄 Système de Maintenance Automatique

### Composants

| Composant         | Fichier                                | Usage                        |
| ----------------- | -------------------------------------- | ---------------------------- |
| **Script Python** | `.parac/tools/auto-maintain.py`        | Détection et synchronisation |
| **Git Hook**      | `.parac/tools/hooks/pre-commit`        | Exécution avant commit       |
| **GitHub Action** | `.github/workflows/maintain-parac.yml` | CI/CD automatique            |

### Installation Rapide

```bash
# 1. Installer le pre-commit hook
cp .parac/tools/hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# 2. Tester le script
python .parac/tools/auto-maintain.py --dry-run --verbose

# 3. Le hook s'exécutera automatiquement à chaque commit
```

## 📋 Fichiers Maintenus Automatiquement

### 1. current_state.yaml
- **Emplacement**: `.parac/memory/context/current_state.yaml`
- **Mis à jour**: Date snapshot, changements récents, métadonnées
- **Trigger**: Tout changement git détecté

### 2. changelog.md
- **Emplacement**: `.parac/changelog.md`
- **Mis à jour**: Nouvelles entrées datées des changements
- **Trigger**: Changements dans packages/, templates/, docs/, examples/

### 3. roadmap.yaml
- **Emplacement**: `.parac/roadmap/roadmap.yaml`
- **Mis à jour**: Timestamp last_update, recent_achievements
- **Trigger**: Nouvelles fonctionnalités complétées

## 🎯 Cas d'Usage

### Développement Quotidien

```bash
# Workflow normal
git add packages/paracle_core/feature.py
git commit -m "feat: nouvelle fonctionnalité"
# 🔄 Le hook exécute auto-maintain.py
# ✅ .parac/ est mis à jour et inclus dans le commit
```

### Synchronisation Manuelle

```bash
# Vérifier ce qui serait modifié
python .parac/tools/auto-maintain.py --dry-run

# Appliquer les modifications
python .parac/tools/auto-maintain.py

# Réviser
git diff .parac/
```

### CI/CD

Sur push vers GitHub:
1. GitHub Action s'exécute automatiquement
2. Détecte les désynchronisations
3. Crée un commit auto avec les mises à jour
4. Commente les PRs si action manuelle requise

## 🔧 Configuration

### Options du Script

```bash
# Exécution normale
python .parac/tools/auto-maintain.py

# Simulation (pas de modification)
python .parac/tools/auto-maintain.py --dry-run

# Sortie détaillée
python .parac/tools/auto-maintain.py --verbose

# Combiner les options
python .parac/tools/auto-maintain.py --dry-run --verbose
```

### Personnalisation

Éditer `.parac/tools/auto-maintain.py` pour ajouter:

```python
# Détection personnalisée
def detect_custom_area(self, changes: Dict[str, Set[str]]) -> None:
    if changes.get("my_custom_folder"):
        # Logique personnalisée
        self.log("Custom area changed", "change")
```

## 🛠️ Intégration IDE

### VS Code Task

Ajouter à `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Maintain .parac",
      "type": "shell",
      "command": "python",
      "args": [".parac/tools/auto-maintain.py", "--verbose"],
      "group": "none",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    }
  ]
}
```

Exécuter: `Ctrl+Shift+P` → "Tasks: Run Task" → "Maintain .parac"

### Makefile

Ajouter au `Makefile`:

```makefile
.PHONY: maintain-parac
maintain-parac:
	@echo "🔄 Maintaining .parac workspace..."
	@python .parac/tools/auto-maintain.py --verbose
```

Usage: `make maintain-parac`

## 🚨 Dépannage

### Le hook ne s'exécute pas

```bash
# Vérifier les permissions
ls -la .git/hooks/pre-commit

# Rendre exécutable
chmod +x .git/hooks/pre-commit

# Tester manuellement
.git/hooks/pre-commit
```

### Erreur Python/YAML

```bash
# Installer les dépendances
pip install pyyaml

# Vérifier la version Python
python --version  # Doit être 3.10+
```

### Changements non détectés

```bash
# Vérifier le statut git
git status

# Voir les fichiers suivis
git ls-files

# Vérifier les fichiers ignorés
git check-ignore -v file.txt
```

### Conflit de commits automatiques

Si GitHub Action crée un commit pendant que vous travaillez:

```bash
# Récupérer les changements distants
git pull --rebase

# Résoudre les conflits si nécessaire
git status
```

## 📚 Bonnes Pratiques

### ✅ À Faire

- **Installer le hook** dès le clone du repo
- **Tester avec --dry-run** avant première utilisation
- **Réviser les diffs** avant de push
- **Lire les logs** en mode verbose si problème

### ❌ À Éviter

- **Éditer manuellement** les sections auto-générées
- **Skip le hook** sauf exception justifiée
- **Ignorer les warnings** de la CI
- **Désactiver** le système sans raison

### 🎯 Exceptions

Quand skipper le hook:

```bash
# Fix typo rapide dans le README
git commit --no-verify -m "docs: fix typo"

# Commit de merge
git merge --no-verify feature-branch
```

Quand skipper la CI:

```bash
# Changement cosmétique
git commit -m "style: fix formatting [skip ci]"
```

## 🔍 Détails Techniques

### Détection des Changements

Le script analyse:
- **Fichiers staged**: `git diff --cached --name-only`
- **Fichiers unstaged**: `git diff --name-only`
- **Fichiers untracked**: `git ls-files --others --exclude-standard`

### Catégorisation

```python
{
    "templates": set(),    # templates/**
    "packages": set(),     # packages/**
    "docs": set(),         # docs/**
    "examples": set(),     # examples/**
    "tests": set(),        # tests/**
    "roadmap": set(),      # .roadmap/**
    "all": set()           # Tous les changements
}
```

### Mise à Jour Conditionnelle

Le système met à jour uniquement si:
- ✓ Changements détectés dans zones surveillées
- ✓ Pas d'entrée changelog pour aujourd'hui
- ✓ current_state.yaml n'est pas déjà à jour

## 📊 Métriques de Maintenance

Le système peut tracker:
- Nombre de mises à jour automatiques
- Fréquence des synchronisations manuelles
- Temps moyen d'exécution
- Zones les plus modifiées

## 🚀 Améliorations Futures

- [ ] Support des hooks post-commit
- [ ] Notifications Slack/Discord
- [ ] Dashboard de métriques
- [ ] AI-powered changelog generation
- [ ] Détection automatique de breaking changes

## 📖 Voir Aussi

- [Structure .parac](.parac/STRUCTURE.md)
- [Roadmap](.parac/roadmap/roadmap.yaml)
- [Current State](.parac/memory/context/current_state.yaml)
- [Changelog](.parac/changelog.md)
- [Tools Registry](.parac/tools/registry.yaml)
