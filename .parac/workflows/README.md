# Workflows Directory

Ce dossier contient les définitions de workflows réutilisables pour orchestrer les agents.

## Structure

- `catalog.yaml` - Catalogue des workflows disponibles
- `templates/` - Templates de workflows réutilisables
- `definitions/` - Définitions de workflows spécifiques au projet

## Définition d'un workflow

Un workflow définit une séquence d'étapes exécutées par des agents :

```yaml
name: code_review_workflow
description: Automated code review process
version: 1.0.0

steps:
  - name: analyze_code
    agent: code_analyzer
    tools: [file_reader, code_executor]

  - name: review_security
    agent: security_reviewer
    depends_on: [analyze_code]

  - name: generate_report
    agent: documenter
    depends_on: [review_security]
```

## Types de workflows

### Sequential

Étapes exécutées l'une après l'autre

### Parallel

Plusieurs agents travaillent simultanément

### Conditional

Branches conditionnelles basées sur les résultats

### Loop

Répétition jusqu'à satisfaction d'une condition

## Exécution

Les workflows sont exécutés via la CLI :

```bash
paracle workflow run <workflow_name>
```

Ou via l'API :

```python
from paracle.orchestration import WorkflowRunner

runner = WorkflowRunner()
result = await runner.run("code_review_workflow")
```
