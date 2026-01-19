# Paracle Logging Architecture

> **Two Separate Logging Systems** - Understanding the distinction between user and framework logs.

## Overview

Paracle utilise **DEUX systèmes de logs indépendants** avec des objectifs différents :

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. LOGS UTILISATEUR                          │
│                   (.parac/memory/logs/)                         │
│                                                                 │
│  📊 Pour les projets des utilisateurs                          │
│  ✅ Gouvernance, décisions, actions agents                     │
│  ✅ Contrôlé par l'utilisateur                                 │
│  ✅ Rotation à 10,000 lignes                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    2. LOGS FRAMEWORK                            │
│         (logs système selon plateforme)                         │
│                                                                 │
│  🔧 Pour le diagnostic du framework Paracle lui-même          │
│  ✅ Erreurs internes, debug, audit ISO 42001                   │
│  ✅ Rotation à 10 MB                                           │
│  ✅ Format JSON structuré                                      │
└─────────────────────────────────────────────────────────────────┘
```

## 1. Logs Utilisateur (.parac/)

### Objectif
Logs **créés par et pour l'utilisateur** dans le contexte de son projet.

### Emplacement
```
.parac/memory/logs/
├── agent_actions.log     # Actions des agents (PRINCIPAL)
├── decisions.log         # Décisions importantes
├── discoveries.log       # Learnings
├── archives/             # Archives rotationnées
│   └── agent_actions.YYYY-MM-DD_HH-MM-SS.log
├── runtime/              # Logs d'exécution
└── audit/                # Audit trail projet
```

### Caractéristiques
- **Rotation**: 10,000 lignes max (1,000 conservées)
- **Format**: Texte simple `[timestamp] [agent] [action] description`
- **Contrôle**: Utilisateur via `paracle logs` CLI
- **Scope**: Projet spécifique (un `.parac/` par projet)

### Gestion via CLI
```bash
# Commandes UTILISATEUR
paracle logs analyze      # État des logs projet
paracle logs rotate       # Rotation manuelle
paracle logs cleanup      # Nettoyage archives
paracle logs show         # Voir contenu
```

### API Python
```python
from paracle_core.parac.logger import AgentLogger, log_action

# Logger dans .parac/memory/logs/agent_actions.log
log_action(
    action="IMPLEMENTATION",
    description="Added authentication feature",
    agent="CoderAgent"
)
```

### Cas d'Usage
- ✅ **Traçabilité projet**: Qui a fait quoi et quand
- ✅ **Gouvernance**: Respect des politiques `.parac/policies/`
- ✅ **Audit projet**: Historique des décisions architecturales
- ✅ **Debug projet**: Comprendre l'évolution du code
- ✅ **Reporting**: Génération de rapports de progrès

### Configuration
Fichier: `.parac/project.yaml`
```yaml
file_management:
  logs:
    global:
      max_file_size_mb: 1
      compress_rotated: true
    predefined:
      actions:
        enabled: true
        rotation: "size"  # À 10,000 lignes
      decisions:
        enabled: true
        retention_days: 365
```

---

## 2. Logs Framework (Système)

### Objectif
Logs **internes au framework Paracle** pour diagnostic et debugging du framework lui-même.

### Emplacement (Selon Plateforme)

#### Windows
```
%LOCALAPPDATA%\Paracle\logs\
├── paracle.log           # Log principal framework
├── paracle.log.1.gz      # Archive compressée
└── audit\
    └── audit-YYYY-MM-DD.log  # Audit ISO 42001
```

#### Linux/macOS
```
~/.local/share/paracle/logs/    # Linux
~/Library/Logs/Paracle/         # macOS

├── paracle.log
├── paracle.log.1.gz
└── audit/
    └── audit-YYYY-MM-DD.log
```

#### Docker
```
/var/log/paracle/
├── paracle.log
├── paracle.log.1.gz
└── audit/
    └── audit-YYYY-MM-DD.log
```

### Caractéristiques
- **Rotation**: 10 MB max, 5 backups compressés (gzip)
- **Format**: JSON structuré avec metadata
- **Contrôle**: Framework automatique
- **Scope**: Installation système (partagé entre tous les projets)

### Format JSON Structuré
```json
{
  "timestamp": "2026-01-10T15:30:00Z",
  "level": "INFO",
  "logger": "paracle.orchestration",
  "message": "Agent execution started",
  "correlation_id": "01HN8X3QGPZ9K2M1V0E4R5T6W7",
  "context": {
    "agent_id": "coder",
    "task": "Fix bug #42",
    "user": "dev@example.com"
  }
}
```

### Gestion Programmatique
```python
from paracle_core.logging import (
    configure_logging,
    get_logger,
    LogLevel
)

# Configuration au démarrage de l'application
configure_logging(
    level=LogLevel.INFO,
    json_format=True,
    log_to_file=True,
    log_file_path="/var/log/paracle/paracle.log"
)

# Utilisation dans le code
logger = get_logger(__name__)
logger.info("Operation completed", extra={
    "duration_ms": 1234,
    "success": True
})
```

### Cas d'Usage
- ✅ **Debug framework**: Erreurs internes Paracle
- ✅ **Performance**: Métriques de performance du framework
- ✅ **Sécurité**: Détection d'attaques, tentatives non autorisées
- ✅ **Audit ISO 42001**: Compliance réglementaire
- ✅ **Monitoring**: Intégration avec Datadog, Splunk, etc.
- ✅ **Troubleshooting**: Support technique Paracle

### Configuration
Fichier: `~/.paracle/config.yaml` ou variables d'environnement
```bash
# Variables d'environnement
export PARACLE_LOG_LEVEL=DEBUG
export PARACLE_LOG_JSON=true
export PARACLE_LOG_FILE=/var/log/paracle/debug.log
export PARACLE_LOG_AUDIT=true
```

Ou programmatique :
```python
from paracle_core.logging import LogConfig

config = LogConfig.from_env()
# Ou
config = LogConfig(
    level=LogLevel.DEBUG,
    json_format=True,
    log_to_file=True,
    audit_enabled=True
)
```

---

## Comparaison des Deux Systèmes

| Aspect            | 🧑 Logs Utilisateur    | 🔧 Logs Framework         |
| ----------------- | --------------------- | ------------------------ |
| **Emplacement**   | `.parac/memory/logs/` | Plateforme système       |
| **Scope**         | Projet spécifique     | Installation globale     |
| **Format**        | Texte simple          | JSON structuré           |
| **Rotation**      | 10,000 lignes         | 10 MB                    |
| **Compression**   | Non (archives)        | Oui (gzip)               |
| **Contrôle**      | Utilisateur           | Framework automatique    |
| **Configuration** | `.parac/project.yaml` | `~/.paracle/config.yaml` |
| **CLI**           | `paracle logs`        | Pas de CLI dédié         |
| **Objectif**      | Gouvernance projet    | Debug framework          |
| **API Python**    | `AgentLogger`         | `get_logger()`           |
| **Audit**         | Projet                | ISO 42001                |

---

## Quand Utiliser Quel Système ?

### Utilisez les Logs Utilisateur (.parac/) pour :
- ✅ Logger les actions de vos agents custom
- ✅ Documenter les décisions architecturales
- ✅ Tracer l'évolution de votre projet
- ✅ Auditer le respect de vos politiques internes
- ✅ Générer des rapports de progrès

**Exemple** :
```python
from paracle_core.parac.logger import log_action

log_action(
    action="IMPLEMENTATION",
    description="Implemented user authentication with JWT",
    agent="CoderAgent",
    details={"files": ["auth.py", "middleware.py"]}
)
```

### Utilisez les Logs Framework pour :
- ✅ Debug d'erreurs internes au framework
- ✅ Monitoring de performance du framework
- ✅ Audit de compliance ISO 42001
- ✅ Intégration avec systèmes de monitoring externes
- ✅ Support technique Paracle

**Exemple** :
```python
from paracle_core.logging import get_logger

logger = get_logger(__name__)
logger.error(
    "Failed to load provider",
    exc_info=True,
    extra={"provider": "openai", "model": "gpt-4"}
)
```

---

## Workflows Typiques

### Workflow Utilisateur (Projet)
```bash
# 1. Vérifier état des logs projet
paracle logs analyze

# 2. Voir activité récente
paracle logs show -n 100

# 3. Si log trop gros (> 80%)
paracle logs rotate

# 4. Nettoyage annuel
paracle logs cleanup
```

### Workflow Framework (Debug)
```python
# 1. Configurer niveau de log
from paracle_core.logging import set_log_level, LogLevel

set_log_level(LogLevel.DEBUG)

# 2. Exécuter code problématique
# Les logs iront dans /var/log/paracle/ ou équivalent

# 3. Analyser les logs JSON
# Utiliser jq, grep, ou outils externes
```

```bash
# Analyser logs framework
cat ~/.local/share/paracle/logs/paracle.log | jq '.level == "ERROR"'

# Suivre en temps réel
tail -f ~/.local/share/paracle/logs/paracle.log | jq .
```

---

## Intégration des Deux Systèmes

### Correlation ID
Les deux systèmes peuvent partager un **correlation_id** pour tracer une opération de bout en bout :

```python
from paracle_core.logging import set_correlation_id, get_logger
from paracle_core.parac.logger import log_action

# Framework génère un ID
correlation_id = "01HN8X3QGPZ9K2M1V0E4R5T6W7"
set_correlation_id(correlation_id)

# Log framework
logger = get_logger(__name__)
logger.info("Starting agent execution")
# → {"correlation_id": "01HN8...", "message": "..."}

# Log utilisateur
log_action(
    action="IMPLEMENTATION",
    description="Task completed",
    details={"correlation_id": correlation_id}
)
# → [2026-01-10] [CoderAgent] [IMPLEMENTATION] Task completed
```

### Workflow Combiné (Debug + Gouvernance)
```python
from paracle_core.logging import get_logger, correlation_id
from paracle_core.parac.logger import log_action

logger = get_logger(__name__)

with correlation_id() as cid:
    # Log framework (debug interne)
    logger.info("Processing task", extra={"task_id": "T-123"})

    try:
        # Exécution logique
        result = do_work()

        # Log utilisateur (traçabilité projet)
        log_action(
            action="IMPLEMENTATION",
            description="Task T-123 completed successfully",
            details={"correlation_id": cid}
        )

    except Exception as e:
        # Log framework (erreur interne)
        logger.error("Task failed", exc_info=True)

        # Log utilisateur (incident projet)
        log_action(
            action="BUGFIX",
            description=f"Task T-123 failed: {e}",
            details={"correlation_id": cid, "error": str(e)}
        )
```

---

## Best Practices

### Pour les Utilisateurs
1. ✅ **Utilisez les logs utilisateur** pour la traçabilité de votre projet
2. ✅ **Ignorez les logs framework** sauf en cas de bug Paracle
3. ✅ **Monitorer avec `paracle logs analyze`** hebdomadairement
4. ✅ **Exporter régulièrement** : `paracle logs export -o backup.json`

### Pour les Développeurs Framework
1. ✅ **Utilisez `get_logger()`** dans le code framework
2. ✅ **Structurez en JSON** pour parsing automatique
3. ✅ **Incluez correlation_id** pour traçabilité
4. ✅ **Loggez les erreurs avec stack trace** : `exc_info=True`

### Pour les Admins Système
1. ✅ **Centralisez les logs framework** dans Splunk/ELK
2. ✅ **Configurez rotation automatique** avec logrotate
3. ✅ **Surveillez les logs audit** pour compliance
4. ✅ **Backupez régulièrement** les logs système

---

## Références

### Documentation Logs Utilisateur
- [Log Management Guide](logs-management.md)
- [Log Rotation Policy](../.parac/memory/logs/LOG_ROTATION_POLICY.md)
- [Hooks README](../.parac/tools/hooks/README.md)

### Documentation Logs Framework
- API: `paracle_core.logging`
- Config: `paracle_core.logging.config.LogConfig`
- Handlers: `paracle_core.logging.handlers`
- Platform paths: `paracle_core.logging.platform`

### Standards
- ISO 42001:2023 - AI Management System (audit logs)
- 12-Factor App - Logs as event streams
- OpenTelemetry - Distributed tracing

---

**Conclusion** : Les logs utilisateur (`.parac/`) sont pour **votre projet**, les logs framework sont pour **Paracle lui-même**. Utilisez `paracle logs` pour gérer les premiers, ignorez les seconds sauf debug. 🎯
