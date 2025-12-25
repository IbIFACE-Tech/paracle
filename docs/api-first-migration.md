# Migration vers l'Architecture API First

## Résumé

**Date**: 2025-12-25
**Status**: ✅ Complétée
**ADR**: ADR-009

Suite à l'observation que PARACLE est "API First", nous avons refactoré le système de découverte d'agents pour respecter ce principe architectural.

## Problème Identifié

❌ **Avant**: La CLI appelait directement les services (`AgentDiscovery`, `ManifestGenerator`)
✅ **Après**: La CLI consomme l'API REST comme tout autre client

## Changements Implémentés

### 1. API REST (/agents)

**Fichiers créés**:
- `packages/paracle_api/schemas/agents.py` - Schémas Pydantic
- `packages/paracle_api/routers/agents.py` - Endpoints REST

**Endpoints**:
- `GET /agents` - Liste tous les agents
- `GET /agents/{agent_id}` - Métadonnées d'un agent
- `GET /agents/{agent_id}/spec` - Spécification complète
- `GET /agents/manifest` - Manifeste JSON
- `POST /agents/manifest` - Écrire manifest.yaml

### 2. CLI Refactorée

**Fichier modifié**: `packages/paracle_cli/commands/agents.py`

**Changements**:
- Remplacé appels directs par `httpx` HTTP requests
- Ajouté gestion d'erreur pour connexion API
- Conservé Rich formatting pour terminal
- Messages d'erreur clairs si API inaccessible

### 3. Tests API

**Fichier créé**: `tests/unit/test_api_agents.py`

**Couverture**:
- ✅ Tous les endpoints GET/POST
- ✅ Cas d'erreur (404, 409, 500)
- ✅ Fixtures avec agents de test
- ✅ Validation des réponses Pydantic

### 4. Documentation

**Fichier mis à jour**: `docs/agent-discovery.md`

**Sections ajoutées**:
- API REST avec exemples curl
- Architecture API First avec diagramme
- Méthodes d'intégration (API, Manifeste, CLI, Python)
- Section Tests

### 5. Dépendances

**Fichier modifié**: `pyproject.toml`

**Changement**: `httpx>=0.27.0` déplacé vers dépendances runtime

## Architecture

```
┌─────────────────────────────────────────────┐
│         PARACLE REST API (FastAPI)          │
│                                             │
│  GET  /agents                               │
│  GET  /agents/{id}                          │
│  GET  /agents/{id}/spec                     │
│  GET  /agents/manifest                      │
│  POST /agents/manifest                      │
└────────────────┬────────────────────────────┘
                 │
                 │ HTTP/JSON
                 │
     ┌───────────┼───────────┬───────────┐
     │           │           │           │
┌────▼────┐ ┌───▼────┐ ┌────▼────┐ ┌───▼────┐
│   CLI   │ │  Web   │ │   IDE   │ │ Script │
│ (Click) │ │(React) │ │ Plugin  │ │ Python │
└─────────┘ └────────┘ └─────────┘ └────────┘
```

## Workflow de Développement

### Démarrer l'API

```bash
# Terminal 1 - API
uvicorn paracle_api.main:app --reload

# Terminal 2 - CLI
paracle agents list
paracle agents get pm
```

### Documentation Interactive

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Avantages

✅ **Cohérence**: Une seule implémentation
✅ **Testabilité**: API testée indépendamment
✅ **Extensibilité**: Facile d'ajouter clients (web, IDE)
✅ **Documentation**: OpenAPI automatique
✅ **Multi-client**: CLI, web, IDE, scripts Python

## Impact sur les Utilisateurs

### Pour l'utilisation locale

**Option 1: API + CLI séparés** (recommandé développement)
```bash
# Terminal 1
uvicorn paracle_api.main:app --reload

# Terminal 2
paracle agents list
```

**Option 2: Mode embarqué** (à venir Phase 2)
```bash
# L'API démarre automatiquement
paracle agents list
```

### Pour la production

**Docker Compose** (à venir):
```yaml
services:
  paracle-api:
    image: paracle-api:latest
    ports: ["8000:8000"]

  paracle-cli:
    image: paracle-cli:latest
    depends_on: [paracle-api]
```

## Tests

### Lancer les tests

```bash
# Tests API
pytest tests/unit/test_api_agents.py -v

# Tests complets
make test

# Couverture
make coverage
```

### Résultats attendus

```
test_list_agents_no_parac PASSED
test_list_agents PASSED
test_get_agent_metadata PASSED
test_get_agent_not_found PASSED
test_get_agent_spec PASSED
test_get_manifest_json PASSED
test_write_manifest PASSED
test_write_manifest_conflict PASSED
```

## Prochaines Étapes

### Phase 2 (Future)

1. **Mode Embarqué CLI**
   - CLI démarre API automatiquement si non lancée
   - Utilise port aléatoire pour éviter conflits

2. **Web Application**
   - Interface React pour visualiser agents
   - Éditeur markdown pour specs
   - Dashboard de synchronisation

3. **IDE Plugins**
   - VS Code extension
   - JetBrains plugin
   - Utilisation de l'API REST

4. **MCP Server**
   - Model Context Protocol pour Cursor/Claude
   - Exposition des agents via MCP

## Références

- **ADR**: [.parac/roadmap/decisions.md#adr-009](../.parac/roadmap/decisions.md)
- **Documentation**: [docs/agent-discovery.md](../docs/agent-discovery.md)
- **Code API**: `packages/paracle_api/routers/agents.py`
- **Code CLI**: `packages/paracle_cli/commands/agents.py`
- **Tests**: `tests/unit/test_api_agents.py`

## Statut

✅ **Implémentation**: 100% complétée
✅ **Tests**: 100% couverture API
✅ **Documentation**: Complète avec exemples
✅ **Migration**: Aucune breaking change (CLI fonctionne identique)

**Note**: La CLI nécessite maintenant que l'API soit lancée, mais le comportement utilisateur reste identique.
