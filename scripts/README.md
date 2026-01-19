# Paracle Development Scripts

> **⚠️ IMPORTANT - Dogfooding Séparation**
> Ce répertoire contient les outils de **DÉVELOPPEMENT** du framework Paracle.
> Pour les outils de **GOUVERNANCE** (maintenir `.parac/`), voir `.parac/tools/hooks/`.
> Voir [.parac/DOGFOODING_SEPARATION.md](../.parac/DOGFOODING_SEPARATION.md) pour la distinction complète.

---

## 🎯 Purpose

Ces scripts sont utilisés par les **développeurs du framework Paracle** pour :
- Gérer les versions et releases
- Automatiser les commits git
- Générer les changelogs
- Corriger des problèmes de build/tests
- Profiler les performances

**Ces scripts ne sont PAS pour les utilisateurs de Paracle !**

---

## 📋 Scripts Disponibles

### **Version Management**

#### `bump_version.py`
Incrémente la version du framework dans `pyproject.toml` et autres fichiers.

```bash
python scripts/bump_version.py --patch   # 1.0.2 → 1.0.3
python scripts/bump_version.py --minor   # 1.0.3 → 1.1.0
python scripts/bump_version.py --major   # 1.1.0 → 2.0.0
```

#### `bump-version.ps1` / `bump-version.sh`
Wrappers shell pour bump_version.py.

```powershell
# PowerShell
.\scripts\bump-version.ps1 -Type patch

# Bash
bash scripts/bump-version.sh patch
```

---

### **Changelog Management**

#### `generate_changelog.py`
Génère ou met à jour CHANGELOG.md depuis les commits git.

```bash
python scripts/generate_changelog.py --from v1.0.0 --to HEAD
```

---

### **Git Automation**

#### `git_commit_automation.py`
Automatisation des commits git avec conventions.

```bash
python scripts/git_commit_automation.py \
  --type fix \
  --scope sandbox \
  --message "Made docker imports optional"
```

#### `releasemanager_commit.py`
Commits automatisés par l'agent ReleaseManager.

```bash
python scripts/releasemanager_commit.py \
  --message "Release v1.0.3" \
  --tag v1.0.3
```

---

### **Security**

#### `run-owasp-scan.ps1` / `run-owasp-scan.sh`
Lance un scan de sécurité OWASP sur le framework.

```powershell
# PowerShell
.\scripts\run-owasp-scan.ps1

# Bash
bash scripts/run-owasp-scan.sh
```

---

### **Testing & Fixing**

#### `fix_security_tests.py`
Corrige les tests de sécurité du framework.

```bash
python scripts/fix_security_tests.py
```

#### `fix_tool_init.py`
Corrige les imports dans `paracle_tools/__init__.py`.

```bash
python scripts/fix_tool_init.py
```

---

### **Profiling**

#### `baseline_profiling.py`
Profiling de performance pour établir des baselines.

```bash
python scripts/baseline_profiling.py --component agent --output baselines/
```

---

### **Utilities**

#### `create_icon.py`
Génère l'icône du projet.

```bash
python scripts/create_icon.py --size 256 --output assets/icon.png
```

#### `log-action.py` / `log-action.ps1` / `log-action.sh`
**⚠️ DEPRECATED** - Utilisez `.parac/tools/hooks/agent-logger.py` à la place.

Ces scripts sont des wrappers qui appellent l'outil de gouvernance.

```powershell
# Utiliser directement l'outil de gouvernance
python .parac/tools/hooks/agent-logger.py CoderAgent BUGFIX "Description"
```

---

## 🚫 Ce qui N'appartient PAS Ici

### ❌ Outils de Gouvernance
Ces outils doivent être dans `.parac/tools/hooks/` :
- `agent-logger.py` - Logger les actions agents
- `sync-watch.py` - Synchroniser manifest.yaml
- `validate-structure.py` - Valider la structure .parac/

### ❌ Code Source du Framework
Le code source appartient à `packages/` :
- Logique métier → `packages/paracle_core/`
- API REST → `packages/paracle_api/`
- CLI → `packages/paracle_cli/`

### ❌ Configuration Projet
La configuration du projet appartient à `.parac/` :
- État du projet → `.parac/memory/context/current_state.yaml`
- Roadmap → `.parac/roadmap/roadmap.yaml`
- Agents → `.parac/agents/specs/`

---

## 📊 Règle de Décision

**"Un client utilisant Paracle aurait-il ce script ?"**

- ❌ **NON** → Le script reste ici dans `scripts/` ✅
- ✅ **OUI** → Le script va dans `.parac/tools/hooks/` ⚠️

---

## 🔗 Voir Aussi

- **[.parac/DOGFOODING_SEPARATION.md](../.parac/DOGFOODING_SEPARATION.md)** - Séparation complète des responsabilités
- **[.parac/tools/hooks/README.md](../.parac/tools/hooks/README.md)** - Outils de gouvernance
- **[.parac/GOVERNANCE.md](../.parac/GOVERNANCE.md)** - Règles de gouvernance
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Guide de contribution

---

**Note**: Ces scripts sont des **outils internes** pour développer le framework Paracle. Ils ne sont pas publiés sur PyPI et ne font pas partie du produit final.
