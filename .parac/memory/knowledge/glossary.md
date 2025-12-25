# Paracle Glossary

## Core Concepts

### Agent

Un **agent** est une entité autonome capable d'exécuter des tâches en utilisant un modèle LLM. Un agent possède :
- Une spécification (AgentSpec) définissant son comportement
- Un état (pending, running, succeeded, failed)
- Des outils disponibles
- Optionnellement, un agent parent pour l'héritage

### AgentSpec

La **spécification d'un agent** est un value object immuable définissant :
- Nom unique
- Modèle LLM à utiliser
- Temperature (créativité)
- System prompt (instructions)
- Tools (outils disponibles)
- Parent (pour héritage)

### Agent Inheritance

L'**héritage d'agent** permet à un agent de hériter les propriétés d'un agent parent :
- Les propriétés enfant override les propriétés parent
- La chaîne de parents doit être acyclique
- Résolu au moment de la création

### Workflow

Un **workflow** est une séquence ordonnée de steps formant un DAG (Directed Acyclic Graph) :
- Chaque step est exécuté par un agent
- Les steps peuvent avoir des dépendances
- Les outputs d'un step peuvent être inputs d'un autre

### WorkflowStep

Une **étape de workflow** définit :
- L'agent responsable
- Les inputs attendus
- Les outputs produits
- Les dépendances sur d'autres steps

## Architecture Concepts

### Hexagonal Architecture

Architecture **Ports & Adapters** où :
- Le **Domain** contient la logique métier pure
- Les **Ports** sont des interfaces définies par le domain
- Les **Adapters** implémentent les ports pour l'infrastructure

### Domain Layer

Couche contenant la **logique métier pure** :
- Aucune dépendance externe
- Pure Python avec Pydantic
- 100% testable sans mocks

### Infrastructure Layer

Couche contenant les **implémentations techniques** :
- Persistence (SQLite, PostgreSQL)
- Event Bus (Redis, In-Memory)
- LLM Providers (OpenAI, Anthropic)
- Framework Adapters

### Application Layer

Couche contenant l'**orchestration** :
- Workflow engine
- Memory management
- Observability
- Governance

### API Layer

Couche exposant les **interfaces clients** :
- REST API (FastAPI)
- WebSocket
- CLI (Click)
- SDK

## Patterns

### Repository Pattern

Abstraction de la **persistence** :
- Interface définie dans le domain
- Implémentation dans l'infrastructure
- Permet de changer de base de données sans impacter le domain

### Event Bus

Système de **communication par événements** :
- Publish/Subscribe pattern
- Découplage entre composants
- Audit trail automatique

### Factory Pattern

Création d'objets **avec logique complexe** :
- AgentFactory pour résolution d'héritage
- Centralise la logique de création
- Garantit les invariants

### Protocol (Structural Typing)

Interface basée sur la **structure** plutôt que l'héritage :
- LLMProvider Protocol
- Permet duck typing
- Extension sans modification

## LLM Concepts

### Provider

Un **provider** est une source de modèles LLM :
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)
- Local (Ollama, LM Studio)

### Temperature

Paramètre contrôlant la **créativité** du modèle :
- 0.0 = Déterministe, répétable
- 0.7 = Équilibré (défaut)
- 2.0 = Maximum créativité

### System Prompt

Instructions **système** données au modèle :
- Définit le comportement de l'agent
- Contexte permanent
- Personnalité et contraintes

### Tool Calling

Capacité du modèle à **appeler des outils** :
- Fonctions externes
- APIs
- Exécution de code

### MCP (Model Context Protocol)

**Protocole standardisé** pour la gestion des outils :
- Interface commune multi-provider
- Découverte d'outils
- Exécution sécurisée

## Governance Concepts

### Policy

Une **politique** définit des règles de gouvernance :
- Règles de code (linting, tests)
- Règles de sécurité (secrets, permissions)
- Règles de qualité (coverage, docs)

### Approval Workflow

Processus de **validation** pour actions sensibles :
- Human-in-the-loop
- Niveaux d'approbation
- Audit trail

### Kill Switch

Mécanisme d'**arrêt d'urgence** :
- Arrête tous les agents
- Préserve l'état
- Audit de l'arrêt

### ISO 42001

Norme internationale pour les **systèmes de management de l'IA** :
- Gouvernance
- Risk management
- Auditabilité
- Explainability

## Data Concepts

### ULID

**Universally Unique Lexicographically Sortable Identifier** :
- Unique comme UUID
- Triable chronologiquement
- 128 bits

### Domain Event

Événement représentant un **changement d'état** :
- Immuable
- Horodaté
- Contient le contexte

### Aggregate

Groupe d'**entités avec une racine** :
- Transactions atomiques
- Invariants garantis
- Encapsulation

## Framework Adapters

### MSAF

**Microsoft Semantic Agent Framework** :
- Framework Microsoft pour agents
- Intégration Azure

### LangChain

Framework populaire pour **applications LLM** :
- Chains, Agents, Tools
- Large écosystème

### LlamaIndex

Framework pour **RAG et indexation** :
- Document loading
- Vector stores
- Query engines

## Infrastructure

### SQLAlchemy

**ORM Python** pour la persistence :
- Mapping objet-relationnel
- Migrations avec Alembic
- Multi-database

### Redis/Valkey

**Store clé-valeur** pour :
- Event bus
- Caching
- Session state

### FastAPI

Framework **REST API** :
- Async native
- OpenAPI auto-généré
- Validation Pydantic

### Click

Framework **CLI** Python :
- Commandes décorateurs
- Auto-help
- Rich integration

## Quality Concepts

### Test Coverage

Pourcentage de code **couvert par les tests** :
- Target: >90%
- Unit + Integration + E2E

### Conventional Commits

Format standard pour **messages de commit** :
- `feat:` nouvelle fonctionnalité
- `fix:` correction de bug
- `docs:` documentation
- `refactor:` refactoring
- `test:` tests
- `chore:` maintenance

### ADR (Architecture Decision Record)

Document capturant une **décision architecturale** :
- Contexte
- Décision
- Conséquences
- Alternatives considérées

## Abbreviations

| Abbr | Full Form |
|------|-----------|
| API | Application Programming Interface |
| CLI | Command Line Interface |
| DAG | Directed Acyclic Graph |
| DDD | Domain-Driven Design |
| LLM | Large Language Model |
| MCP | Model Context Protocol |
| ORM | Object-Relational Mapping |
| RAG | Retrieval-Augmented Generation |
| RBAC | Role-Based Access Control |
| REST | Representational State Transfer |
| SDK | Software Development Kit |
| SSO | Single Sign-On |
| ULID | Universally Unique Lexicographically Sortable Identifier |
