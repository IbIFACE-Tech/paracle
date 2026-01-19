# Guide de Gestion des Fix et Versions - Paracle

> **Objectif**: Maintenir un historique clair et structuré de tous les correctifs (fix/bugs) par version de Paracle

---

## 📋 Table des Matières

1. [Workflow de Gestion des Fix](#workflow-de-gestion-des-fix)
2. [Classification des Fix](#classification-des-fix)
3. [Process de Documentation](#process-de-documentation)
4. [Versioning et Releases](#versioning-et-releases)
5. [Outils et Automatisation](#outils-et-automatisation)
6. [Best Practices](#best-practices)

---

## 🔄 Workflow de Gestion des Fix

### 1. Identification du Bug

**Quand un bug est découvert:**

1. **Créer une issue GitHub** (si public) ou **ajouter à `open_questions.md`** (si interne)
   ```bash
   # Créer une issue
   gh issue create --title "Bug: Description courte" \
                   --body "Description détaillée du bug" \
                   --label "bug"
   ```

2. **Documenter dans `.parac/memory/context/open_questions.md`**
   ```markdown
   ## Q-XXX: Bug - Description courte

   **Type**: Bug
   **Severity**: Critical/High/Medium/Low
   **Status**: Open
   **Affected Version**: v1.0.1
   **Discovered**: 2026-01-10

   **Description**:
   Le bug se manifeste quand...

   **Reproduction**:
   1. Étape 1
   2. Étape 2
   3. Résultat attendu vs obtenu

   **Impact**:
   - Bloque l'utilisation de X
   - Affecte les utilisateurs Y

   **Owner**: Agent responsable (TesterAgent, CoderAgent, etc.)
   **Deadline**: Date cible de résolution
   ```

### 2. Priorisation

**Niveaux de priorité:**

| Priority | Severity | SLA        | Exemples                                              |
| -------- | -------- | ---------- | ----------------------------------------------------- |
| **P0**   | Critical | 24h        | CLI ne démarre pas, perte de données, security breach |
| **P1**   | High     | 3 jours    | Fonctionnalité majeure cassée, erreur bloquante       |
| **P2**   | Medium   | 1 semaine  | Bug mineur, workaround possible                       |
| **P3**   | Low      | 2 semaines | Amélioration, polish, edge cases                      |

### 3. Résolution

**Étapes:**

1. **Créer une branche de fix**
   ```bash
   git checkout -b fix/issue-123-docker-import-error
   ```

2. **Implémenter le fix**
   - Suivre les standards de code (`.parac/policies/CODE_STYLE.md`)
   - Ajouter des tests de régression
   - Documenter le changement

3. **Tester**
   ```bash
   # Tests unitaires
   uv run pytest tests/unit/test_sandbox.py -v

   # Tests d'intégration
   uv run pytest tests/integration/ -v

   # Vérifier que le bug est corrigé
   uv run paracle --version  # Exemple
   ```

4. **Logger l'action**
   ```
   # Dans .parac/memory/logs/agent_actions.log
   [2026-01-10 10:30:00] [CoderAgent] [BUGFIX] Fixed docker import error in paracle_sandbox
   ```

5. **Commiter avec convention**
   ```bash
   git commit -m "fix(sandbox): make docker imports optional

   - Made DockerSandbox import optional in __init__.py, manager.py, monitor.py
   - Added clear error message when Docker not installed
   - Fixed type hints compatibility (Optional[Type] instead of Type | None)
   - Closes #123"
   ```

### 4. Documentation du Fix

**Mettre à jour CHANGELOG.md:**

```markdown
## [Unreleased]

### Fixed
- **CRITICAL**: Fixed `ModuleNotFoundError` when running CLI without Docker
  - Made Docker imports optional in paracle_sandbox
  - Added graceful fallback with clear error message
  - Issue #123
```

**Mettre à jour `.parac/roadmap/decisions.md`** (si décision architecturale):

```markdown
### ADR-XXX: Rendre Docker Optionnel dans Sandbox

**Date**: 2026-01-10
**Status**: Accepted
**Context**: CLI crashait si Docker n'était pas installé
**Decision**: Rendre l'import de DockerSandbox optionnel
**Consequences**:
- ✅ CLI fonctionne sans Docker
- ✅ Message d'erreur clair
- ⚠️ Sandbox nécessite installation manuelle
```

### 5. Merge et Release

1. **Créer une Pull Request**
   ```bash
   gh pr create --title "fix(sandbox): make docker imports optional" \
                --body "Fixes #123" \
                --label "bug,fix"
   ```

2. **Review** (par ReviewerAgent ou équipe)

3. **Merge vers develop**
   ```bash
   git checkout develop
   git merge fix/issue-123-docker-import-error
   git push origin develop
   ```

4. **Si fix critique → Patch release**
   ```bash
   # Incrémenter version patch (1.0.1 → 1.0.2)
   # Voir section "Versioning et Releases"
   ```

---

## 🏷️ Classification des Fix

### Types de Fix

1. **CRITICAL** - Bloque l'utilisation du framework
   - CLI ne démarre pas
   - Crash systématique
   - Perte de données
   - Faille de sécurité
   - **→ Patch release immédiate (X.X.Y+1)**

2. **HIGH** - Fonctionnalité majeure cassée
   - Commande importante ne fonctionne pas
   - Erreur bloquante avec workaround difficile
   - **→ Patch release rapide (dans 48h)**

3. **MEDIUM** - Bug mineur avec workaround
   - Comportement incorrect mais contournable
   - Message d'erreur peu clair
   - **→ Inclus dans prochaine release mineure**

4. **LOW** - Amélioration, polish
   - Typo dans la documentation
   - Message d'erreur améliorable
   - Edge case rare
   - **→ Inclus quand prêt**

### Catégories de Fix

| Catégorie   | Préfixe Git        | Exemples                                     |
| ----------- | ------------------ | -------------------------------------------- |
| Bug Code    | `fix(scope):`      | `fix(cli): correct version display`          |
| Bug Config  | `fix(config):`     | `fix(pyproject): add missing dependency`     |
| Bug Docs    | `docs(fix):`       | `docs(readme): correct installation command` |
| Sécurité    | `security(scope):` | `security(api): fix auth vulnerability`      |
| Performance | `perf(scope):`     | `perf(agent): optimize tool loading`         |

---

## 📝 Process de Documentation

### Fichiers à Mettre à Jour

#### 1. **CHANGELOG.md** (OBLIGATOIRE)

**Format:**
```markdown
## [Version] - YYYY-MM-DD

### Fixed
- **[SEVERITY]**: Brève description du fix
  - Détails techniques
  - Fichiers modifiés
  - Issue/PR reference
```

**Exemple:**
```markdown
## [1.0.2] - 2026-01-10

### Fixed
- **CRITICAL**: Fixed CLI crash when Docker not installed
  - Made docker imports optional in paracle_sandbox package
  - Added clear error message: "Install with: pip install docker psutil"
  - Fixed in: packages/paracle_sandbox/{__init__.py,manager.py,monitor.py}
  - Closes #123, PR #124
```

#### 2. **`.parac/memory/logs/agent_actions.log`** (OBLIGATOIRE)

```
[2026-01-10 10:30:00] [CoderAgent] [BUGFIX] Fixed docker import error - Made imports optional in paracle_sandbox
[2026-01-10 10:45:00] [TesterAgent] [TEST] Added regression tests for optional docker imports
[2026-01-10 11:00:00] [ReviewerAgent] [REVIEW] Reviewed PR #124 - docker import fix
```

#### 3. **`.parac/memory/context/open_questions.md`** (si applicable)

Marquer la question comme résolue:
```markdown
## Q-123: Bug - CLI crash sans Docker ✅ RESOLVED

**Status**: Resolved (2026-01-10)
**Resolution**: Made docker imports optional
**PR**: #124
**Version**: v1.0.2
```

#### 4. **`.parac/roadmap/decisions.md`** (si décision architecturale)

Documenter les décisions importantes prises pendant le fix.

#### 5. **GitHub Release Notes** (lors de la release)

```markdown
## Bug Fixes

- **CRITICAL**: Fixed CLI crash when Docker not installed (#123)
  - Made docker imports optional
  - Added graceful error handling
  - Users can now use CLI without Docker installed

## Contributors

Thanks to @username for reporting this issue!
```

---

## 🚀 Versioning et Releases

### Semantic Versioning

**Format**: `MAJOR.MINOR.PATCH`

```
1.0.2
│ │ │
│ │ └─ PATCH: Bug fixes, patches
│ └─── MINOR: New features (backwards compatible)
└───── MAJOR: Breaking changes
```

### Quand Incrémenter

| Type de Change              | Version          | Exemples      |
| --------------------------- | ---------------- | ------------- |
| **Bug fix critique**        | PATCH (X.X.Y+1)  | 1.0.1 → 1.0.2 |
| **Nouvelle fonctionnalité** | MINOR (X.Y+1.0)  | 1.0.2 → 1.1.0 |
| **Breaking change**         | MAJOR (X+1.0.0)  | 1.1.0 → 2.0.0 |
| **Plusieurs bug fixes**     | PATCH            | 1.0.2 → 1.0.3 |
| **Sécurité**                | PATCH (immédiat) | 1.0.2 → 1.0.3 |

### Process de Release avec Fix

#### 1. Préparer la Release

```bash
# 1. Incrémenter la version
# Dans pyproject.toml
version = "1.0.3"

# Dans .parac/memory/context/current_state.yaml
project:
  version: 1.0.3

# Dans packages/paracle_cli/main.py
@click.version_option(version="1.0.3")

# 2. Mettre à jour CHANGELOG.md
## [1.0.3] - 2026-01-XX

### Fixed
- Liste des fix de cette version
```

#### 2. Créer le Tag et la Release

```bash
# 1. Commit des changements de version
git add .
git commit -m "chore(release): bump version to 1.0.3"

# 2. Créer le tag
git tag -a v1.0.3 -m "Release v1.0.3 - Bug Fixes

Bug Fixes:
- Fixed X (#123)
- Fixed Y (#124)
- Security fix for Z (#125)

See CHANGELOG.md for details."

# 3. Push
git push origin develop
git push origin v1.0.3

# 4. Créer GitHub Release
gh release create v1.0.3 \
  --title "v1.0.3 - Bug Fixes" \
  --notes-file release-notes.md \
  dist/*
```

#### 3. Release Notes Template

```markdown
## 🐛 Bug Fixes

### Critical
- **Fixed CLI crash when Docker not installed** (#123)
  - Made docker imports optional
  - Added clear error message

### High Priority
- Fixed IDE setup for VS Code (#125)
  - Added vscode to supported IDEs

### Other Fixes
- Fixed linting errors in sandbox module
- Improved error messages across CLI

## 📚 Documentation
- Updated CHANGELOG.md with all fixes
- Improved troubleshooting guide

## 🙏 Contributors
Thanks to everyone who reported issues!

## 📦 Installation

pip install --upgrade paracle==1.0.3

## 🔗 Full Changelog
https://github.com/IbIFACE-Tech/paracle-lite/compare/v1.0.2...v1.0.3
```

---

## 🛠️ Outils et Automatisation

### 1. CLI Commands pour Fix Management

```bash
# Créer une issue de bug
paracle bug report --title "Description" --severity critical

# Logger un fix
paracle bug fix --issue 123 --description "Made docker optional"

# Mettre à jour CHANGELOG automatiquement
paracle changelog add --type fix --description "Fixed X"

# Préparer une release
paracle release prepare --type patch --changelog
```

### 2. GitHub Actions Workflow

**`.github/workflows/bugfix-release.yml`:**

```yaml
name: Bugfix Release

on:
  push:
    branches:
      - 'fix/**'

jobs:
  test-fix:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run regression tests
        run: |
          uv sync
          uv run pytest tests/ -v --cov

      - name: Verify fix
        run: |
          # Vérifier que le bug est corrigé
          uv run paracle --version
```

### 3. Pre-commit Hook

**`.pre-commit-config.yaml`:**

```yaml
- repo: local
  hooks:
    - id: check-changelog
      name: Check CHANGELOG.md updated
      entry: scripts/check_changelog.py
      language: system
      pass_filenames: false
```

### 4. Script de Vérification

**`scripts/check_changelog.py`:**

```python
#!/usr/bin/env python3
"""Vérifie que CHANGELOG.md est à jour."""
import sys
from pathlib import Path

changelog = Path("CHANGELOG.md").read_text()

if "## [Unreleased]" not in changelog:
    print("❌ CHANGELOG.md manque la section [Unreleased]")
    sys.exit(1)

if "### Fixed\n- Nothing yet" in changelog:
    print("⚠️  Pas de fix documenté dans CHANGELOG.md")
    # Ne pas bloquer, juste avertir

print("✅ CHANGELOG.md OK")
```

---

## ✅ Best Practices

### DO ✅

1. **Documenter IMMÉDIATEMENT**
   - Dès qu'un fix est fait, mettre à jour CHANGELOG.md
   - Logger dans agent_actions.log
   - Fermer l'issue/question

2. **Être DESCRIPTIF**
   - Expliquer le bug ET la solution
   - Lister les fichiers modifiés
   - Mentionner les tests ajoutés

3. **Suivre les CONVENTIONS**
   - Git commits: `fix(scope): description`
   - CHANGELOG: Format Keep a Changelog
   - Versioning: Semantic Versioning

4. **Tester EXHAUSTIVEMENT**
   - Tests unitaires
   - Tests de régression
   - Tests d'intégration
   - Vérifier que le bug ne revient pas

5. **Communiquer CLAIREMENT**
   - Release notes lisibles
   - Documentation à jour
   - Migration guide si nécessaire

### DON'T ❌

1. **Ne PAS skipper CHANGELOG.md**
   - Toujours documenter les fix
   - Même les petits fix

2. **Ne PAS oublier les TESTS**
   - Chaque fix doit avoir un test de régression
   - Sinon le bug reviendra

3. **Ne PAS mélanger fix et features**
   - Un fix = un commit/PR
   - Pas de "pendant que j'y suis..."

4. **Ne PAS garder les fix dans develop**
   - Fix critique → release patch immédiate
   - Pas attendre la prochaine minor

5. **Ne PAS ignorer la SÉCURITÉ**
   - Security fix = priorité P0
   - Release patch immédiate
   - Communication publique si nécessaire

---

## 📊 Métriques à Suivre

### KPIs de Gestion des Fix

1. **Time to Fix (TTF)**
   - P0: < 24h
   - P1: < 3 jours
   - P2: < 1 semaine
   - P3: < 2 semaines

2. **Fix Rate**
   - Nombre de fix par version
   - Taux de régression (fix qui cassent)

3. **Bug Backlog**
   - Nombre de bugs ouverts
   - Âge moyen des bugs ouverts

4. **Coverage des Tests**
   - % de fix avec tests de régression
   - Target: 100%

### Dashboard dans .parac/

**`.parac/memory/metrics/fix_metrics.yaml`:**

```yaml
# Généré automatiquement
fix_metrics:
  period: "2026-01"
  total_fixes: 5
  by_severity:
    critical: 1
    high: 2
    medium: 1
    low: 1
  average_ttf:
    critical: "18h"
    high: "2.5d"
    medium: "5d"
  regression_rate: "0%"
  test_coverage: "100%"
```

---

## 🎯 Checklist Complète de Fix

**Avant de merger un fix:**

- [ ] Bug reproductible et documenté dans open_questions.md
- [ ] Fix implémenté avec tests de régression
- [ ] CHANGELOG.md mis à jour
- [ ] agent_actions.log mis à jour
- [ ] Version incrémentée (si release patch)
- [ ] Tests passent (unit + integration)
- [ ] Code review effectué
- [ ] Documentation mise à jour (si applicable)
- [ ] Issue/Question fermée et cross-référencée
- [ ] Migration guide écrit (si breaking)
- [ ] Release notes préparées (si release)

---

## 📖 Références

- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)

---

**Dernière mise à jour**: 2026-01-10
**Version du guide**: 1.0
**Maintenu par**: ReleaseManager Agent
