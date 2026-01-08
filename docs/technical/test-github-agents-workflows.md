# Test Complet: GitHub Agents + Workflows Paracle + MCP

Ce guide montre comment tester l'intégration complète des agents GitHub avec les workflows Paracle via MCP.

## 🎯 Objectif

Tester l'exécution réelle d'un workflow Paracle en utilisant :
1. Agents GitHub définis dans `.github/agents/`
2. Workflows définis dans `.parac/workflows/definitions/`
3. Outils MCP pour l'orchestration

## 📋 Prérequis

```bash
# 1. Installer les dépendances
uv sync

# 2. Vérifier que les composants existent
ls .github/agents/           # Agents GitHub
ls .parac/workflows/definitions/  # Workflows
ls packages/paracle_mcp/     # Serveur MCP
```

## 🧪 Tests Disponibles

### Test 1: Simulation d'Intégration

```bash
# Test sans exécution réelle (simulation)
uv run python test_github_agents_workflow.py
```

**Ce test vérifie :**
- ✅ Chargement des agents GitHub
- ✅ Parsing des workflows YAML
- ✅ Création d'AgentSpec Paracle
- ✅ Simulation des étapes du workflow
- ✅ Discovery des outils MCP
- ✅ Registre des adaptateurs

### Test 2: Outils MCP

```bash
# Test des outils MCP (sans exécution de workflow)
uv run python test_mcp_tools.py
```

**Ce test vérifie :**
- ✅ Liste des workflows disponibles
- ✅ Outils de contexte (current_state, roadmap, etc.)
- ✅ Registre des outils par agent
- ✅ Parsing des workflows réels
- ✅ Intégration GitHub agents ↔ workflows

### Test 3: Exécution CLI

```bash
# Lister les workflows disponibles
uv run paracle workflow list

# Exécuter un workflow simple (simulation)
uv run paracle workflow run bugfix \
  --inputs '{"bug_description": "Test bug", "files": ["test.py"]}' \
  --dry-run

# Exécuter réellement un code review
uv run paracle workflow run code_review \
  --inputs '{"changed_files": ["packages/paracle_tools/reviewer_tools.py"]}' \
  --mode safe
```

## 🔄 Workflows Testables

### 1. Code Review (Recommandé pour débuter)

```yaml
# .parac/workflows/definitions/code_review.yaml
Workflow: code_review
Agents: reviewer, tester
Steps: 6
Durée: ~2-5 minutes
```

**Test :**
```bash
uv run paracle workflow run code_review \
  --inputs '{"changed_files": ["README.md"], "review_depth": "quick"}'
```

### 2. Bugfix

```yaml
# .parac/workflows/definitions/bugfix.yaml
Workflow: bugfix
Agents: coder, tester, reviewer
Steps: 5
Durée: ~5-10 minutes
```

**Test :**
```bash
uv run paracle workflow run bugfix \
  --inputs '{"bug_description": "Fix YAML parsing error", "files": ["test.py"]}'
```

### 3. Feature Development (Complet)

```yaml
# .parac/workflows/definitions/feature_development.yaml
Workflow: feature_development
Agents: architect, coder, tester, reviewer, documenter, pm
Steps: 9
Durée: ~15-30 minutes
```

**Test :**
```bash
uv run paracle workflow run feature_development \
  --inputs '{"feature_name": "user-authentication", "requirements": "Basic JWT auth"}'
```

## 🔧 Configuration des Agents

### Agents GitHub Disponibles

| Agent              | Fichier                                  | Outils | Description    |
| ------------------ | ---------------------------------------- | ------ | -------------- |
| **architect**      | `.github/agents/architect.agent.md`      | 3      | Design système |
| **coder**          | `.github/agents/coder.agent.md`          | 16     | Implémentation |
| **reviewer**       | `.github/agents/reviewer.agent.md`       | 3      | Code review    |
| **tester**         | `.github/agents/tester.agent.md`         | 5      | Tests QA       |
| **pm**             | `.github/agents/pm.agent.md`             | 3      | Gestion projet |
| **documenter**     | `.github/agents/documenter.agent.md`     | 3      | Documentation  |
| **releasemanager** | `.github/agents/releasemanager.agent.md` | 21     | Releases       |
| **security**       | `.github/agents/security.agent.md`       | 12     | Sécurité       |

### Exemple: Agent Security

```markdown
---
description: Security auditing, vulnerability detection, and compliance
tools:
  - paracle/*
handoffs:
  - label: Fix Vulnerabilities
    agent: coder
  - label: Add Security Tests
    agent: tester
---

# Security Agent

## Tools
- bandit, safety, semgrep, detect-secrets
- vulnerability_detector, secret_scanner
- compliance_checker (OWASP, GDPR, SOC2)
```

## 🎬 Scénarios de Test

### Scénario 1: Code Review Simple

```bash
# 1. Créer un fichier de test
echo "def hello(): print('world')" > test_file.py

# 2. Lancer le review
uv run paracle workflow run code_review \
  --inputs '{"changed_files": ["test_file.py"], "review_depth": "quick"}'

# 3. Vérifier le résultat
cat .parac/memory/logs/agent_actions.log
```

**Résultat attendu :**
- ✅ Analyse statique (lint, type check)
- ✅ Vérification sécurité
- ✅ Revue qualité code
- ✅ Couverture tests
- ✅ Rapport final avec verdict

### Scénario 2: Security Audit

```bash
# 1. Utiliser l'agent security via workflow
uv run paracle workflow run code_review \
  --inputs '{"changed_files": ["packages/paracle_api/"], "review_depth": "thorough"}' \
  --agent security

# 2. L'agent security exécute ses 12 outils
# - bandit (vulnérabilités Python)
# - safety (dépendances)
# - semgrep (patterns)
# - detect-secrets (secrets hardcodés)
# - etc.
```

### Scénario 3: Feature Development avec Adapters

```bash
# 1. Développer avec LangChain adapter
uv run paracle workflow run feature_development \
  --inputs '{
    "feature_name": "rag-search",
    "requirements": "RAG-based search with LangChain",
    "adapter": "langchain"
  }'

# Le workflow va :
# - Architect: Concevoir avec LangChain patterns
# - Coder: Implémenter avec LangChainAdapter
# - Tester: Tester l'intégration LangChain
```

## 🔌 Utilisation des Adapters

### LangChain Adapter

```python
# Dans un workflow step:
steps:
  - id: implement_rag
    agent: coder
    adapter: langchain
    config:
      model: gpt-4
      use_langgraph: true
    task: "Implement RAG system"
```

### AutoGen Adapter

```python
# Dans un workflow step:
steps:
  - id: team_collaboration
    agent: pm
    adapter: autogen
    config:
      llm_config:
        model: gpt-4
        max_consecutive_auto_reply: 3
    task: "Coordinate team"
```

## 📊 Monitoring

### Logs d'Actions

```bash
# Voir toutes les actions des agents
tail -f .parac/memory/logs/agent_actions.log

# Filtrer par agent
grep "ReviewerAgent" .parac/memory/logs/agent_actions.log
```

### État Actuel

```bash
# Voir l'état du projet
cat .parac/memory/context/current_state.yaml

# Voir la roadmap
cat .parac/roadmap/roadmap.yaml
```

### Décisions

```bash
# Voir les décisions architecturales
cat .parac/roadmap/decisions.md | grep -A 20 "ADR-020"
```

## 🐛 Dépannage

### Problème: MCP tool bug "r.content is not iterable"

**Workaround :**
```bash
# Utiliser CLI directement au lieu de MCP tools
uv run paracle workflow run <workflow_id> --inputs '{...}'
```

### Problème: Agent non trouvé

```bash
# Vérifier que l'agent existe
ls .github/agents/ | grep <agent_name>

# Vérifier dans manifest
cat .parac/agents/manifest.yaml | grep <agent_name>
```

### Problème: Workflow échoue

```bash
# Exécuter en mode dry-run pour validation
uv run paracle workflow run <workflow_id> --dry-run

# Exécuter en mode verbose
uv run paracle workflow run <workflow_id> --verbose
```

## 📈 Résultats Attendus

### Tests de Simulation

```
======================================================================
🏁 FINAL RESULTS
======================================================================
Test 1 (Integration): ✅ PASSED
Test 2 (Code Review): ✅ PASSED
======================================================================

✅ GitHub agent loaded (.github/agents/coder.agent.md)
✅ Workflow loaded (.parac/workflows/definitions/code_review.yaml)
✅ Agent spec parsed
✅ Workflow simulation completed (6 steps)
✅ MCP tool discovery tested (41 tools loaded)
✅ Adapter registry tested
```

### Exécution Réelle

```
🔄 Executing workflow: code_review

[1/6] static_analysis ✅
[2/6] security_check ✅
[3/6] code_quality ✅
[4/6] test_coverage ✅
[5/6] performance_check ✅
[6/6] final_verdict ✅

📋 Review Summary:
   - Quality Score: 92/100
   - Issues Found: 2 (1 minor, 1 info)
   - Security: No vulnerabilities
   - Test Coverage: 95%
   - Recommendation: ✅ APPROVED with minor suggestions
```

## 🚀 Prochaines Étapes

1. **Fixer le bug MCP** : workflow_run tool
2. **Tester avec adaptateurs réels** : LangChain, AutoGen
3. **Créer workflows personnalisés** : Vos propres workflows
4. **Intégrer dans CI/CD** : GitHub Actions

## 📚 Références

- [Agent Specs](.parac/agents/specs/) - Spécifications complètes
- [Workflows](.parac/workflows/) - Catalogue des workflows
- [MCP Server](packages/paracle_mcp/) - Serveur MCP
- [Adapters](packages/paracle_adapters/) - Adaptateurs frameworks

---

**Créé par :** Security Agent + PM Agent
**Date :** 2026-01-06
**Version :** 1.0
