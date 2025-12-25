# Agent Action Logs

Ce dossier contient les logs de **gouvernance** du projet : actions des agents (humains et IA), décisions, et sessions de développement.

## ⚠️ Distinction Importante

Ce projet utilise **deux types de logs** :

| Type            | Localisation                  | Contenu                              | Versionné |
| --------------- | ----------------------------- | ------------------------------------ | --------- |
| **Framework**   | `~/.paracle/logs/`            | Logs du moteur Paracle (système)     | ❌ Non     |
| **Gouvernance** | `.parac/memory/logs/`         | Actions, décisions, sessions         | ✅ Oui     |
| **Runtime**     | `.parac/memory/logs/runtime/` | Exécution agents/workflows du projet | ❌ Non     |

### Framework Logs (`~/.paracle/logs/`)

Logs du **moteur Paracle** installé via pip :
- Démarrage/arrêt du framework
- Erreurs système de Paracle
- Performance du framework

**Exemple** : `Paracle framework v0.0.1 started`

### Gouvernance Logs (`.parac/memory/logs/`)

Logs de **développement et gouvernance** de ce projet :
- Actions des agents (Coder, Architect, etc.)
- Décisions architecturales
- Sessions de travail

**Exemple** : `[CoderAgent] [IMPLEMENTATION] Implemented webhook system`

### Runtime Logs (`.parac/memory/logs/runtime/`)

Logs d'**exécution** des agents et workflows de ce projet :
- Exécution des agents du projet
- Workflows lancés
- Erreurs d'exécution

**Exemple** : `Agent 'pm' started task T-123`

Voir [runtime/README.md](runtime/README.md) pour détails.

---

## Structure

```
logs/
├── agent_actions.log      # Log principal des actions (gouvernance)
├── decisions.log          # Log des décisions importantes
├── sessions/              # Logs par session de développement
│   └── 2025-12-25_session_001.md
└── runtime/               # Logs d'exécution (voir runtime/README.md)
    ├── agents/
    ├── workflows/
    └── errors/
```

## Format des Logs

### agent_actions.log

Format : `[TIMESTAMP] [AGENT] [ACTION] Description`

```
[2025-12-25 10:30:00] [CoderAgent] [IMPLEMENTATION] Implemented webhook system in packages/paracle_events/webhooks.py
[2025-12-25 10:35:00] [TesterAgent] [TEST] Added unit tests for webhook system
[2025-12-25 10:40:00] [ReviewerAgent] [REVIEW] Reviewed webhook implementation - APPROVED
```

### decisions.log

Format : `[TIMESTAMP] [AGENT] [DECISION] Description | Rationale | Impact`

```
[2025-12-25 10:30:00] [ArchitectAgent] [DECISION] Use event sourcing for webhooks | Better auditability | Medium impact on persistence layer
```

## Types d'Actions

- **IMPLEMENTATION** : Implémentation de code
- **TEST** : Ajout/modification de tests
- **REVIEW** : Revue de code
- **DOCUMENTATION** : Écriture de documentation
- **DECISION** : Décision architecturale ou technique
- **PLANNING** : Planification, roadmap
- **REFACTORING** : Refactoring de code
- **BUGFIX** : Correction de bug
- **UPDATE** : Mise à jour de fichiers .parac

## Git

✅ **Les logs de gouvernance sont versionnés** (`.parac/memory/logs/*.log`, `sessions/`)
❌ **Les logs runtime ne sont PAS versionnés** (`.parac/memory/logs/runtime/` → `.gitignore`)

## Consultation

```bash
# Dernières actions
tail -n 20 .parac/memory/logs/agent_actions.log

# Actions d'un agent spécifique
grep "CoderAgent" .parac/memory/logs/agent_actions.log

# Décisions importantes
cat .parac/memory/logs/decisions.log

# Logs runtime (exécution)
tail -f .parac/memory/logs/runtime/agents/coder.log
```
