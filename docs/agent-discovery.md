# Agent Discovery System

Le système de discovery d'agents PARACLE permet à n'importe quel IDE ou assistant IA de découvrir et intégrer automatiquement les agents définis dans `.parac/agents/specs/`.

## Problème Résolu

❌ **Avant** : Chaque IDE nécessitait une configuration manuelle avec duplication des specs d'agents
✅ **Maintenant** : Les agents sont découverts automatiquement depuis `.parac/` par tous les outils

## Architecture

```
.parac/agents/specs/*.md   →   PARACLE Framework   →   REST API + CLI
       (source)                  (discovery)            (consumers)
```

**PARACLE est API first** : Toute fonctionnalité est exposée via l'API REST, puis consommée par la CLI et autres clients.

## API REST

### Démarrer l'API

```bash
# Développement
uvicorn paracle_api.main:app --reload

# Production
uvicorn paracle_api.main:app --host 0.0.0.0 --port 8000
```

L'API est accessible sur `http://localhost:8000` avec documentation interactive :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

### Endpoints

#### GET /agents

Liste tous les agents découverts.

**Requête** :
```bash
curl http://localhost:8000/agents
```

**Réponse** (200 OK) :
```json
{
  "agents": [
    {
      "id": "pm",
      "name": "Project Manager Agent",
      "role": "Project coordination, roadmap management...",
      "spec_file": "agents/specs/pm.md",
      "capabilities": ["project planning", "progress tracking"],
      "description": "Manages project lifecycle..."
    }
  ],
  "count": 6,
  "parac_root": "/path/to/.parac"
}
```

#### GET /agents/{agent_id}

Obtient les métadonnées d'un agent spécifique.

**Requête** :
```bash
curl http://localhost:8000/agents/pm
```

**Réponse** (200 OK) :
```json
{
  "id": "pm",
  "name": "Project Manager Agent",
  "role": "Project coordination...",
  "spec_file": "agents/specs/pm.md",
  "capabilities": ["project planning", "progress tracking"],
  "description": "Manages project lifecycle..."
}
```

**Erreurs** :
- `404 Not Found` : Agent inexistant ou `.parac/` introuvable

#### GET /agents/{agent_id}/spec

Obtient la spécification complète d'un agent (markdown).

**Requête** :
```bash
curl http://localhost:8000/agents/coder/spec
```

**Réponse** (200 OK) :
```json
{
  "agent_id": "coder",
  "spec_file": "agents/specs/coder.md",
  "content": "# Coder Agent\n\n**Rôle**: Implementation...",
  "metadata": {
    "id": "coder",
    "name": "Coder Agent",
    "role": "Implementation...",
    "spec_file": "agents/specs/coder.md",
    "capabilities": ["code implementation", "code quality"],
    "description": "Implements features..."
  }
}
```

#### GET /agents/manifest

Génère et retourne le manifeste en JSON (sans écrire sur disque).

**Requête** :
```bash
curl http://localhost:8000/agents/manifest
```

**Réponse** (200 OK) :
```json
{
  "schema_version": "1.0",
  "generated_at": "2025-12-25T10:30:00",
  "workspace_root": "/path/to/project",
  "parac_root": "/path/to/.parac",
  "agents": [...],
  "count": 6
}
```

#### POST /agents/manifest

Génère et écrit le manifeste dans `.parac/manifest.yaml`.

**Requête** :
```bash
# Sans force (échoue si le fichier existe)
curl -X POST http://localhost:8000/agents/manifest

# Avec force (écrase le fichier existant)
curl -X POST "http://localhost:8000/agents/manifest?force=true"
```

**Réponse** (200 OK) :
```json
{
  "success": true,
  "manifest_path": "/path/to/.parac/manifest.yaml",
  "agents_count": 6
}
```

**Erreurs** :
- `409 Conflict` : Le manifeste existe déjà (utiliser `?force=true`)
- `404 Not Found` : `.parac/` introuvable

## Utilisation CLI

La CLI consomme l'API REST. **Assurez-vous que l'API est lancée** avant d'utiliser les commandes.

### 1. Lister les Agents

```bash
# Format table (par défaut)
paracle agents list

# Format JSON
paracle agents list --format=json

# Format YAML
paracle agents list --format=yaml
```

**Output** :
```
                🤖 Agents (6 found)
┌────────────┬────────────────────────┬────────────────────────┐
│ ID         │ Name                   │ Role                   │
├────────────┼────────────────────────┼────────────────────────┤
│ pm         │ Project Manager Agent  │ Project coordination   │
│ architect  │ System Architect Agent │ Architecture design    │
│ coder      │ Coder Agent            │ Implementation         │
│ tester     │ Tester Agent           │ Test design            │
│ reviewer   │ Reviewer Agent         │ Code review            │
│ documenter │ Documenter Agent       │ Technical docs         │
└────────────┴────────────────────────┴────────────────────────┘
```

### 2. Obtenir un Agent Spécifique

```bash
# Métadonnées (par défaut)
paracle agents get pm

# Spec complète en markdown
paracle agents get coder --spec

# Format JSON
paracle agents get architect --format=json
```

### 3. Exporter Tous les Agents

```bash
# JSON vers stdout
paracle agents export

# YAML vers fichier
paracle agents export --format=yaml --output=agents.yaml

# JSON vers fichier
paracle agents export --output=agents.json
```

### 4. Générer le Manifeste

```bash
# Génération automatique lors du sync
paracle parac sync --manifest

# Le manifeste est créé dans .parac/manifest.yaml
```

## Fichier Manifeste

Le fichier `.parac/manifest.yaml` contient les métadonnées de tous les agents découverts :

```yaml
schema_version: "1.0"
generated_at: "2025-12-25T10:30:00"

workspace:
  name: "paracle-lite"
  version: "0.0.1"
  parac_version: "0.0.1"

agents:
  - id: "pm"
    name: "Project Manager Agent"
    role: "Project coordination, roadmap management..."
    spec_file: "agents/specs/pm.md"
    capabilities:
      - "project planning"
      - "progress tracking"
      - "risk management"
```

## Intégration avec IDEs

### Méthode 1 : Utiliser l'API REST

Les IDEs peuvent appeler l'API REST directement :

```python
import requests

# Lister tous les agents
response = requests.get("http://localhost:8000/agents")
agents = response.json()["agents"]

for agent in agents:
    print(f"{agent['id']}: {agent['name']}")

# Obtenir un agent spécifique
response = requests.get("http://localhost:8000/agents/pm")
agent = response.json()

# Obtenir la spec complète
response = requests.get("http://localhost:8000/agents/coder/spec")
spec = response.json()
print(spec["content"])

# Générer le manifeste JSON
response = requests.get("http://localhost:8000/agents/manifest")
manifest = response.json()
```

### Méthode 2 : Lire le Manifeste

Les IDEs peuvent lire `.parac/manifest.yaml` pour découvrir les agents :

```python
import yaml

# Lire le manifeste
with open(".parac/manifest.yaml") as f:
    manifest = yaml.safe_load(f)

# Lister les agents
for agent in manifest["agents"]:
    print(f"{agent['id']}: {agent['name']}")

    # Lire la spec complète
    with open(f".parac/{agent['spec_file']}") as spec:
        agent_content = spec.read()
```

### Méthode 3 : Utiliser la CLI

Les IDEs peuvent appeler la CLI directement :

```bash
# JSON pour parsing facile
paracle agents list --format=json | jq '.[] | {id, name, role}'

# Obtenir une spec complète
paracle agents get pm --spec
```

### Méthode 4 : API Python Directe

Pour les intégrations Python avancées :

```python
from pathlib import Path
from paracle_core.parac.agent_discovery import AgentDiscovery

# Découvrir les agents
parac_root = Path(".parac")
discovery = AgentDiscovery(parac_root)

agents = discovery.discover_agents()
for agent in agents:
    print(f"{agent.id}: {agent.name}")
```

### Méthode 3 : Générateur d'Instructions (À venir - Phase 2)

```bash
# Générer instructions IDE-spécifiques
paracle generate instructions --ide=copilot
paracle generate instructions --ide=cursor
paracle generate instructions --ide=claude
```

## Architecture API First

PARACLE suit le principe **API First** :

```
                    ┌─────────────────────┐
                    │   REST API          │
                    │  (FastAPI)          │
                    │                     │
                    │  GET /agents        │
                    │  GET /agents/{id}   │
                    │  POST /manifest     │
                    └─────────┬───────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
    ┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
    │   CLI        │  │  Web App    │  │  IDE Plugin │
    │  (Click)     │  │  (React)    │  │  (Python)   │
    └──────────────┘  └─────────────┘  └─────────────┘
```

**Avantages** :
- ✅ **Cohérence** : Une seule implémentation partagée
- ✅ **Testabilité** : API testée indépendamment
- ✅ **Extensibilité** : Facile d'ajouter de nouveaux clients
- ✅ **Documentation** : OpenAPI/Swagger automatique
- ✅ **Multi-client** : CLI, web, IDE, scripts Python...

**Exemple de flow** :
1. User : `paracle agents list`
2. CLI → HTTP GET `/agents`
3. API → `AgentDiscovery.discover_agents()`
4. API ← Agents list
5. CLI ← JSON response
6. CLI → Rich table formatting
7. User ← Beautiful terminal output

## Workflow de Développement

### 1. Créer un Nouvel Agent

```bash
# 1. Créer le fichier spec
echo "# Mon Agent\n\n## Role\n..." > .parac/agents/specs/mon-agent.md

# 2. Régénérer le manifeste
paracle parac sync --manifest

# 3. Vérifier
paracle agents list
```

### 2. Mettre à Jour un Agent

```bash
# 1. Modifier le fichier
vim .parac/agents/specs/coder.md

# 2. Régénérer le manifeste
paracle parac sync --manifest

# 3. Régénérer les instructions IDE (à venir)
paracle generate instructions --all
```

### 3. Synchronisation Automatique

Pour regénérer automatiquement le manifeste à chaque modification :

```bash
# Option 1: Intégrer dans git pre-commit hook
echo "paracle parac sync --manifest" >> .git/hooks/pre-commit

# Option 2: Utiliser un watcher (à venir)
paracle watch .parac/agents/specs/ --regenerate
```

## API Python

Le système peut aussi être utilisé directement en Python :

```python
from pathlib import Path
from paracle_core.parac.agent_discovery import AgentDiscovery
from paracle_core.parac.manifest_generator import ManifestGenerator

# Découvrir les agents
parac_root = Path(".parac")
discovery = AgentDiscovery(parac_root)

agents = discovery.discover_agents()
for agent in agents:
    print(f"{agent.id}: {agent.name}")

# Obtenir un agent spécifique
agent = discovery.get_agent("pm")
print(agent.role)
print(agent.capabilities)

# Obtenir la spec complète
spec_content = discovery.get_agent_spec_content("coder")

# Générer le manifeste
generator = ManifestGenerator(parac_root)
manifest = generator.generate_manifest()
generator.write_manifest()
```

## Avantages

✅ **Zero Duplication** : Agents définis une seule fois dans `.parac/agents/specs/`
✅ **Auto-Discovery** : Tout outil peut scanner et découvrir les agents
✅ **API First** : Architecture REST avec clients multiples (CLI, web, IDE)
✅ **IDE Agnostic** : Fonctionne avec n'importe quel IDE/assistant
✅ **Machine-Readable** : Format YAML/JSON standard
✅ **Versionné** : Le manifeste suit le versioning du projet
✅ **Extensible** : Facile d'ajouter de nouveaux agents
✅ **Testable** : API et CLI entièrement testés

## Tests

Le système est couvert par des tests unitaires complets :

```bash
# Tester l'API
pytest tests/unit/test_api_agents.py -v

# Tester le discovery
pytest tests/unit/test_domain.py -v

# Tester la CLI (nécessite l'API lancée)
paracle agents list
paracle agents get pm
```

**Couverture** :
- ✅ Agent discovery et parsing markdown
- ✅ Manifest generation (JSON/YAML)
- ✅ API REST endpoints (GET /agents, POST /manifest)
- ✅ CLI commands (list, get, export)
- ✅ Error handling (404, 409, 500)

## Prochaines Étapes

Phase actuelle (✅ Implémenté) :
- [x] Agent discovery (scan `.parac/agents/specs/`)
- [x] Manifeste generator (`.parac/manifest.yaml`)
- [x] CLI introspection (`paracle agents list/get/export`)
- [x] Auto-sync avec `paracle parac sync`

Phase suivante (🚧 En cours) :
- [ ] Generator d'instructions IDE (`paracle generate instructions`)
- [ ] Templates Jinja2 pour chaque IDE
- [ ] Watcher pour auto-régénération
- [ ] MCP (Model Context Protocol) support

## Références

- [ADR-008: Agent Discovery System](.parac/roadmap/decisions.md#adr-008)
- [Agent Specifications](.parac/agents/specs/)
- [PARACLE Documentation](docs/)
