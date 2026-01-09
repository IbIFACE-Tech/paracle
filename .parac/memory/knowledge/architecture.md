# Paracle Architecture Knowledge Base

## Overview

Paracle utilise une **architecture hexagonale (Ports & Adapters)** avec une séparation stricte des couches pour maximiser la testabilité, l'extensibilité et la maintenabilité.

## Principes Fondamentaux

### 1. Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENTS                                │
│                CLI • SDK • Web UI • IDE                     │
├─────────────────────────────────────────────────────────────┤
│                     API LAYER                               │
│          REST (FastAPI) • WebSocket • GraphQL               │
├─────────────────────────────────────────────────────────────┤
│                 APPLICATION LAYER                           │
│     Orchestration • Memory • Observability • Governance     │
├─────────────────────────────────────────────────────────────┤
│                   DOMAIN LAYER                              │
│         Agents • Workflows • Tools • Policies               │
│               (Pure Python, No Dependencies)                │
├─────────────────────────────────────────────────────────────┤
│                INFRASTRUCTURE LAYER                         │
│    Persistence • Events • Providers • Adapters • MCP        │
└─────────────────────────────────────────────────────────────┘
```

### 2. Dependency Rule

Les dépendances pointent **uniquement vers l'intérieur** :
- Infrastructure → Application → Domain
- Le Domain ne dépend de rien d'externe
- Les couches externes implémentent les interfaces (Ports) définies par les couches internes

### 3. Domain-Driven Design

- **Entities** : Objets avec identité (Agent, Workflow)
- **Value Objects** : Objets immuables sans identité (AgentSpec, WorkflowStep)
- **Aggregates** : Groupes d'entités avec racine (Agent aggregate)
- **Repositories** : Abstraction de la persistence
- **Domain Events** : Communication entre aggregates

## Package Structure

### Packages v0.0.1

| Package | Layer | Responsabilité |
|---------|-------|----------------|
| `paracle_core` | Shared | Utilitaires, ID, config, errors |
| `paracle_domain` | Domain | Logique métier pure |
| `paracle_store` | Infrastructure | Persistence (SQLAlchemy) |
| `paracle_events` | Infrastructure | Event bus (Redis/Memory) |
| `paracle_providers` | Infrastructure | Abstraction LLM |
| `paracle_adapters` | Infrastructure | Intégrations frameworks |
| `paracle_orchestration` | Application | Moteur de workflow |
| `paracle_tools` | Application | Gestion outils & MCP |
| `paracle_api` | API | REST API (FastAPI) |
| `paracle_cli` | API | CLI (Click) |

### Packages v0.5.0 - v1.0.0 (Future)

| Package | Version | Responsabilité |
|---------|---------|----------------|
| `paracle_knowledge` | v0.5.0 | RAG, vector stores |
| `paracle_memory` | v0.5.0 | Memory management |
| `paracle_governance` | v0.7.0 | Policies, approvals |
| `paracle_risk` | v0.7.0 | Risk engine |
| `paracle_audit` | v0.7.0 | Audit trail, compliance |
| `paracle_integrations` | v0.8.0 | Git, CI/CD, PM |
| `paracle_web` | v0.9.0 | Dashboard web |
| `paracle_enterprise` | v0.9.0 | Multi-tenant, RBAC |
| `paracle_intelligence` | v1.0.0 | Auto-learning |

## Domain Models

### Agent

```python
class AgentSpec(BaseModel):
    """Spécification d'un agent (immuable, value object)."""
    name: str                          # Identifiant unique
    model: str                         # Modèle LLM (gpt-4, claude-3, etc.)
    temperature: float = 0.7           # Créativité [0.0, 2.0]
    system_prompt: str | None          # Instructions système
    tools: list[str] = []              # Outils disponibles
    parent: str | None                 # Héritage d'agent
    metadata: dict = {}                # Métadonnées extensibles

class Agent(BaseModel):
    """Instance d'un agent (entity avec identité)."""
    id: str                            # ULID unique
    spec: AgentSpec                    # Spécification
    status: AgentStatus                # pending, running, succeeded, failed
    created_at: datetime
    updated_at: datetime
```

### Workflow

```python
class WorkflowStep(BaseModel):
    """Étape d'un workflow (value object)."""
    name: str                          # Identifiant de l'étape
    agent: str                         # Agent responsable
    inputs: dict = {}                  # Entrées
    outputs: list[str] = []            # Sorties attendues
    depends_on: list[str] = []         # Dépendances (DAG)

class WorkflowSpec(BaseModel):
    """Spécification d'un workflow."""
    name: str
    description: str | None
    steps: list[WorkflowStep]
    metadata: dict = {}
```

## Patterns Architecturaux

### 1. Repository Pattern

```python
class AgentRepository(ABC):
    """Port pour la persistence des agents."""

    @abstractmethod
    async def get_by_id(self, id: str) -> Agent | None: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Agent | None: ...

    @abstractmethod
    async def save(self, agent: Agent) -> None: ...

    @abstractmethod
    async def delete(self, id: str) -> None: ...

# Implémentation (Infrastructure)
class SQLiteAgentRepository(AgentRepository):
    """Adapter SQLite pour AgentRepository."""
    ...
```

### 2. Event-Driven Architecture

```python
class DomainEvent(BaseModel):
    """Base pour tous les événements domaine."""
    event_id: str
    event_type: str
    aggregate_id: str
    timestamp: datetime
    data: dict

class AgentCreatedEvent(DomainEvent):
    event_type: str = "agent.created"

class EventBus(ABC):
    """Port pour le bus d'événements."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None: ...

    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable) -> None: ...
```

### 3. Factory Pattern

```python
class AgentFactory:
    """Factory pour création d'agents avec résolution d'héritage."""

    def __init__(self, registry: AgentRegistry):
        self.registry = registry

    def create(self, spec: AgentSpec) -> Agent:
        resolved = self._resolve_inheritance(spec)
        return Agent(spec=resolved)

    def _resolve_inheritance(self, spec: AgentSpec) -> AgentSpec:
        if not spec.parent:
            return spec
        parent = self.registry.get(spec.parent)
        merged = self._merge_specs(parent, spec)
        return self._resolve_inheritance(merged)
```

### 4. Provider Abstraction

```python
class LLMProvider(Protocol):
    """Interface pour tous les providers LLM."""

    async def complete(
        self,
        messages: list[Message],
        model: str,
        temperature: float
    ) -> CompletionResult: ...

    async def stream(
        self,
        messages: list[Message],
        model: str,
        temperature: float
    ) -> AsyncIterator[StreamChunk]: ...
```

## Flux de Données

### Exécution d'un Agent

```
1. Client (CLI/API) → Requête
2. API Layer → Validation, Auth
3. Application Layer → Orchestration
4. Domain Layer → Business Logic
5. Infrastructure → Provider LLM
6. Retour inverse avec événements
```

### Workflow Execution

```
1. Workflow créé → DAG construit
2. Steps ordonnés par dépendances
3. Chaque step → Agent exécuté
4. Outputs passés aux steps suivants
5. Événements émis à chaque transition
6. État final retourné
```

## Invariants Système

### Agent Invariants

1. Un agent DOIT avoir un nom unique dans son scope
2. La chaîne de parents DOIT être acyclique
3. Un agent DOIT avoir une référence de modèle valide
4. Temperature DOIT être dans [0.0, 2.0]
5. Toutes les actions DOIVENT être auditables

### Workflow Invariants

1. Un workflow DOIT avoir au moins un step
2. Les dépendances DOIVENT former un DAG valide
3. Chaque step DOIT référencer un agent existant
4. Les outputs DOIVENT être définis avant référence

## Extensibilité

### Extension Points

1. **Providers** : Nouveaux LLM via Protocol
2. **Adapters** : Nouveaux frameworks via interface
3. **Tools** : Nouveaux outils via MCP
4. **Policies** : Nouvelles politiques via PolicyEngine
5. **Events** : Nouveaux handlers via EventBus

### Plugin Architecture

```python
@paracle.register_provider("custom-llm")
class CustomProvider:
    ...

@paracle.register_tool("custom-tool")
class CustomTool:
    ...
```

## Références

- ADRs : `.parac/roadmap/decisions.md`
- Roadmap : `.parac/roadmap/roadmap.yaml`
- Global Roadmap : `.roadmap/ROADMAP_GLOBALE.yaml`
- Documentation : `docs/architecture.md`
