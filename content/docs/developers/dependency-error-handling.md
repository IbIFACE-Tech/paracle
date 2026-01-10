# Gestion des Erreurs de Dépendances dans Paracle

Guide complet sur la gestion des erreurs liées à l'absence de packages dans Paracle.

## 📋 Vue d'Ensemble

Paracle gère les dépendances manquantes de manière élégante avec :

1. **Exceptions structurées** - Hiérarchie d'erreurs avec codes
2. **Imports optionnels** - Pattern `try/except ImportError`
3. **Messages explicites** - Instructions d'installation claires
4. **Installation modulaire** - Extras pip pour packages optionnels

---

## 🎯 Philosophie

### Principe : "Fail Fast, Fail Clear"

- ✅ **Détection précoce** : Erreur au moment de l'import ou de la première utilisation
- ✅ **Messages clairs** : Instructions d'installation précises
- ✅ **Graceful degradation** : Fonctionnalités optionnelles ne cassent pas le core
- ✅ **Traçabilité** : Error codes PARACLE-{PKG}-XXX

---

## 🏗️ Architecture des Erreurs de Dépendances

### 1. Exception `DependencyError`

**Fichier** : `packages/paracle_core/exceptions.py`

```python
class DependencyError(ParacleError):
    """Raised when required dependencies are missing or incompatible.

    Examples:
        - Required package not installed
        - Incompatible package version
        - Native library missing
    """

    error_code = "PARACLE-CORE-005"

    def __init__(
        self,
        message: str,
        dependency: str | None = None,
        required_version: str | None = None,
    ) -> None:
        self.dependency = dependency
        self.required_version = required_version
        if dependency:
            if required_version:
                message = f"Dependency '{dependency}' (>={required_version}): {message}"
            else:
                message = f"Dependency '{dependency}': {message}"
        super().__init__(message)
```

**Utilisation** :

```python
from paracle_core.exceptions import DependencyError

raise DependencyError(
    "Not installed",
    dependency="redis",
    required_version="5.0.0"
)
# Message: "Dependency 'redis' (>=5.0.0): Not installed"
```

---

## 🔧 Patterns de Gestion

### Pattern 1 : Import Optionnel avec Flag

**Cas** : Package optionnel pour fonctionnalité non-critique

```python
# packages/paracle_transport/ssh.py

# asyncssh is an optional dependency for SSH transport
try:
    import asyncssh
    ASYNCSSH_AVAILABLE = True
except ImportError:
    asyncssh = None  # type: ignore[assignment]
    ASYNCSSH_AVAILABLE = False
```

**Vérification à l'utilisation** :

```python
class SSHTunnel:
    def __init__(self, config: TunnelConfig):
        if not ASYNCSSH_AVAILABLE:
            raise ImportError(
                "asyncssh is required for SSH transport. "
                "Install it with: pip install asyncssh"
            )
        # ... reste du code
```

**Avantages** :
- ✅ Module importable même sans dépendance
- ✅ Erreur claire au moment de l'utilisation
- ✅ Instructions d'installation précises

---

### Pattern 2 : Lazy Import dans Méthode

**Cas** : Dépendance lourde, utilisée rarement

```python
# packages/paracle_vector/embeddings.py

class OpenAIEmbeddingProvider(EmbeddingProviderBase):
    """OpenAI embedding provider."""

    def __init__(self, model: str = "text-embedding-3-small", api_key: str | None = None):
        self._model = model
        self._api_key = api_key
        self._client: Any = None  # Lazy initialization

    def _get_client(self) -> Any:
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError as e:
                raise ImportError(
                    "OpenAI package not installed. "
                    "Install with: pip install openai"
                ) from e

            self._client = AsyncOpenAI(api_key=self._api_key)
        return self._client

    async def embed(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        """Generate embeddings using OpenAI API."""
        client = self._get_client()  # Import happens here
        response = await client.embeddings.create(
            model=self._model,
            input=texts,
            **kwargs,
        )
        return [item.embedding for item in response.data]
```

**Avantages** :
- ✅ Import différé (performance)
- ✅ Erreur uniquement si utilisé
- ✅ Exception chaining avec `from e`

---

### Pattern 3 : Import au Top-Level avec Exception Wrapper

**Cas** : Dépendance critique pour un module entier

```python
# packages/paracle_adapters/llamaindex_adapter.py

try:
    from llama_index.core import VectorStoreIndex, Document
    from llama_index.llms.openai import OpenAI as LlamaIndexOpenAI
except ImportError as e:
    raise ImportError(
        "llama-index packages are required for LlamaIndex adapter. "
        "Install with: pip install llama-index llama-index-llms-openai"
    ) from e

from paracle_domain.models import AgentSpec, WorkflowSpec
from paracle_adapters.base import FrameworkAdapter

class LlamaIndexAdapter(FrameworkAdapter):
    # ... implementation
```

**Avantages** :
- ✅ Échec immédiat si package manquant
- ✅ Module non importable si dépendance absente
- ✅ Message clair pour utilisateur

---

### Pattern 4 : Graceful Degradation avec Message

**Cas** : Fonctionnalité optionnelle dans CLI

```python
# packages/paracle_cli/ai_helper.py

class AIProviderNotAvailable(Exception):
    """AI provider is not available."""
    pass

def _get_specific_provider(name: str) -> AIProvider | None:
    """Get specific AI provider by name."""
    if name == "openai":
        try:
            from paracle_providers.openai_provider import OpenAIProvider
            from paracle_cli.generation_adapter import GenerationAdapter

            base_provider = OpenAIProvider()
            return GenerationAdapter(base_provider, "openai")
        except ImportError as e:
            raise AIProviderNotAvailable(
                f"OpenAI provider not installed: {e}\n"
                "Install with: pip install paracle[openai]"
            )

    elif name == "anthropic":
        try:
            from paracle_providers.anthropic_provider import AnthropicProvider
            from paracle_cli.generation_adapter import GenerationAdapter

            base_provider = AnthropicProvider()
            return GenerationAdapter(base_provider, "anthropic")
        except ImportError as e:
            raise AIProviderNotAvailable(
                f"Anthropic provider not installed: {e}\n"
                "Install with: pip install paracle[anthropic]"
            )

    return None

def require_ai(func):
    """Decorator to require AI provider for a function."""
    def wrapper(*args, **kwargs):
        ai = get_ai_provider()
        if ai is None:
            raise AIProviderNotAvailable(
                f"{func.__name__} requires AI support.\n\n"
                "Options:\n"
                "  1. Install paracle_meta: pip install paracle[meta]\n"
                "  2. Configure: paracle config set ai.provider openai\n"
                "  3. Set API key: export OPENAI_API_KEY=sk-..."
            )
        return func(*args, ai=ai, **kwargs)
    return wrapper
```

**Utilisation dans commande CLI** :

```python
@click.command()
@require_ai  # Decorator checks dependency
async def generate_agent(description: str, ai: AIProvider):
    """Generate agent using AI."""
    result = await ai.generate_agent(description)
    console.print(result)
```

**Avantages** :
- ✅ Vérification centralisée
- ✅ Instructions multi-étapes claires
- ✅ Graceful degradation (commande disabled, pas crash)

---

## 📦 Installation Modulaire

### pyproject.toml - Extras

**Fichier** : `pyproject.toml`

```toml
[project.optional-dependencies]
# API server
api = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
]

# AI providers
openai = ["openai>=1.0.0"]
anthropic = ["anthropic>=0.18.0"]
providers = ["paracle[openai,anthropic]"]

# Vector databases
vector = [
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.29.0",
    "pgvector>=0.2.0",
    "chromadb>=0.4.0",
]

# Meta generation
meta = [
    "paracle[openai,anthropic]",
    "jinja2>=3.1.0",
]

# Sandbox
sandbox = [
    "docker>=6.1.0",
    "psutil>=5.9.0",
]

# Transport
transport = [
    "asyncssh>=2.14.0",
]

# Full installation
all = [
    "paracle[api,store,events,sandbox,providers,cloud,adapters,observability]",
]
```

### Installation Selective

```bash
# Minimal (core only)
pip install paracle

# Avec API server
pip install paracle[api]

# Avec OpenAI
pip install paracle[openai]

# Avec tous les providers
pip install paracle[providers]

# Installation complète
pip install paracle[all]
```

---

## 🎨 Messages d'Erreur Explicites

### ✅ Bon Message

```python
raise ImportError(
    "SQLAlchemy with async support not installed. "
    "Install with: pip install sqlalchemy[asyncio] asyncpg"
)
```

**Pourquoi c'est bon** :
- Nom du package exact
- Commande d'installation précise
- Extras pip mentionnés (`[asyncio]`)
- Packages supplémentaires listés (`asyncpg`)

### ❌ Mauvais Message

```python
raise ImportError("SQLAlchemy not found")
```

**Pourquoi c'est mauvais** :
- Pas de commande d'installation
- Pas de mention des extras nécessaires
- Utilisateur doit chercher comment installer

---

## 🔍 Cas d'Usage par Package

### 1. `paracle_vector` - Bases de données vectorielles

**Dépendances** :
- PostgreSQL + pgvector : `sqlalchemy[asyncio]`, `asyncpg`
- ChromaDB : `chromadb`
- Sentence transformers : `sentence-transformers`

**Pattern** : Lazy import dans méthode `_get_engine()` ou `_get_client()`

```python
async def _get_engine(self) -> Any:
    """Get or create async database engine."""
    if self._async_engine is None:
        try:
            from sqlalchemy.ext.asyncio import create_async_engine
        except ImportError as e:
            raise ImportError(
                "SQLAlchemy with async support not installed. "
                "Install with: pip install sqlalchemy[asyncio] asyncpg"
            ) from e
        # ... reste du code
```

---

### 2. `paracle_transport` - SSH et Remote Execution

**Dépendances** :
- SSH : `asyncssh`

**Pattern** : Import avec flag + vérification dans `__init__`

```python
try:
    import asyncssh
    ASYNCSSH_AVAILABLE = True
except ImportError:
    asyncssh = None
    ASYNCSSH_AVAILABLE = False

class SSHTunnel:
    def __init__(self, config: TunnelConfig):
        if not ASYNCSSH_AVAILABLE:
            raise ImportError(
                "asyncssh is required for SSH transport. "
                "Install it with: pip install asyncssh"
            )
```

---

### 3. `paracle_tools` - Outils Spécialisés

**Dépendances** :
- Testing : `pytest`, `pytest-cov`
- HTTP : `aiohttp`

**Pattern** : Import optionnel avec fallback

```python
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

# Dans l'outil
if not AIOHTTP_AVAILABLE:
    raise ImportError("aiohttp required. Install with: pip install aiohttp")
```

---

### 4. `paracle_adapters` - Frameworks Externes

**Dépendances** :
- LlamaIndex : `llama-index`, `llama-index-llms-openai`
- LangChain : `langchain`, `langchain-anthropic`

**Pattern** : Import au top-level avec exception wrapper (dépendance critique)

```python
try:
    from llama_index.core import VectorStoreIndex
except ImportError as e:
    raise ImportError(
        "llama-index packages are required for LlamaIndex adapter. "
        "Install with: pip install llama-index llama-index-llms-openai"
    ) from e
```

---

## 🧪 Tests de Gestion d'Erreurs

### Test de DependencyError

**Fichier** : `tests/unit/core/test_exceptions.py`

```python
class TestDependencyError:
    """Test DependencyError exception."""

    def test_basic_dependency_error(self):
        """Test basic dependency error."""
        error = DependencyError("Not installed")
        assert str(error) == "Not installed"
        assert error.error_code == "PARACLE-CORE-005"
        assert error.dependency is None
        assert error.required_version is None

    def test_dependency_error_with_name(self):
        """Test dependency error with dependency name."""
        error = DependencyError("Not found", dependency="redis")
        assert "redis" in str(error)
        assert error.dependency == "redis"

    def test_dependency_error_with_version(self):
        """Test dependency error with version requirement."""
        error = DependencyError(
            "Incompatible version",
            dependency="pydantic",
            required_version="2.0.0",
        )
        assert "pydantic" in str(error)
        assert "2.0.0" in str(error)
        assert error.required_version == "2.0.0"
```

### Test d'Import Optionnel

```python
import pytest

def test_optional_import_graceful():
    """Test that optional import fails gracefully."""
    with pytest.raises(ImportError) as exc_info:
        from paracle_vector.pgvector import PgVectorStore
        store = PgVectorStore("postgresql://localhost/db")
        # This should raise ImportError if sqlalchemy not installed

    assert "sqlalchemy" in str(exc_info.value).lower()
    assert "pip install" in str(exc_info.value)
```

---

## 📚 Documentation Utilisateur

### Guide d'Installation

**Fichier** : `content/docs/users/guides/installation.md`

```markdown
## Troubleshooting

### ModuleNotFoundError

```bash
# Ensure correct Python
python --version  # Should be 3.10+

# Reinstall
pip uninstall paracle
pip install paracle
```

### Missing Optional Dependencies

If you see errors like:

```
ImportError: openai package not installed.
Install with: pip install openai
```

Install the required extra:

```bash
# For OpenAI support
pip install paracle[openai]

# For vector databases
pip install paracle[vector]

# For SSH transport
pip install paracle[transport]

# For everything
pip install paracle[all]
```
```

---

## 🎯 Bonnes Pratiques

### ✅ DO

1. **Utiliser `DependencyError` pour dépendances Python**
   ```python
   from paracle_core.exceptions import DependencyError
   raise DependencyError("Not installed", dependency="redis", required_version="5.0.0")
   ```

2. **Inclure instructions d'installation dans ImportError**
   ```python
   raise ImportError("Package X not installed. Install with: pip install X")
   ```

3. **Faire des imports lazy pour dépendances lourdes**
   ```python
   def _get_client(self):
       if self._client is None:
           try:
               from heavy_package import Client
           except ImportError as e:
               raise ImportError("...") from e
   ```

4. **Utiliser exception chaining (`from e`)**
   ```python
   except ImportError as e:
       raise ImportError("Custom message") from e
   ```

5. **Documenter les extras pip dans pyproject.toml**
   ```toml
   [project.optional-dependencies]
   vector = ["sqlalchemy[asyncio]>=2.0.0", "asyncpg>=0.29.0"]
   ```

### ❌ DON'T

1. **Ne pas masquer les ImportError**
   ```python
   # ❌ MAUVAIS
   try:
       import optional_package
   except:
       pass  # Silent failure
   ```

2. **Ne pas utiliser `import *` avec dépendances optionnelles**
   ```python
   # ❌ MAUVAIS
   from optional_package import *  # Non-explicit, hard to catch
   ```

3. **Ne pas oublier `from e` dans exception chaining**
   ```python
   # ❌ MAUVAIS
   except ImportError as e:
       raise ImportError("Message")  # Perd la stack trace originale

   # ✅ BON
   except ImportError as e:
       raise ImportError("Message") from e  # Préserve la stack trace
   ```

4. **Ne pas importer au top-level si optionnel**
   ```python
   # ❌ MAUVAIS (si optionnel)
   from optional_package import Client  # Crash immédiat

   # ✅ BON
   def use_optional():
       try:
           from optional_package import Client
       except ImportError:
           raise ImportError("...")
   ```

---

## 🔗 Références

### Fichiers Clés

| Fichier                                 | Description                                           |
| --------------------------------------- | ----------------------------------------------------- |
| `packages/paracle_core/exceptions.py`   | Définition de `DependencyError`                       |
| `packages/paracle_vector/pgvector.py`   | Pattern lazy import pour SQLAlchemy                   |
| `packages/paracle_vector/embeddings.py` | Pattern lazy import pour OpenAI/sentence-transformers |
| `packages/paracle_transport/ssh.py`     | Pattern import optionnel avec flag                    |
| `packages/paracle_cli/ai_helper.py`     | Pattern graceful degradation pour AI providers        |
| `pyproject.toml`                        | Définition des extras pip                             |
| `tests/unit/core/test_exceptions.py`    | Tests de `DependencyError`                            |

### Documentation Liée

- [Installation Guide](../users/guides/installation.md) - Guide d'installation avec extras
- [Architecture Overview](architecture.md) - Architecture des packages
- [Exception Handling](exception-handling.md) - Hiérarchie d'exceptions complète

---

## 📊 Résumé

Paracle gère les dépendances manquantes avec **4 patterns principaux** :

| Pattern                  | Cas d'Usage                                             | Exemple                                  |
| ------------------------ | ------------------------------------------------------- | ---------------------------------------- |
| **Import avec flag**     | Fonctionnalité optionnelle, module doit être importable | `paracle_transport/ssh.py`               |
| **Lazy import**          | Dépendance lourde, utilisée rarement                    | `paracle_vector/embeddings.py`           |
| **Top-level import**     | Dépendance critique, module inutilisable sans           | `paracle_adapters/llamaindex_adapter.py` |
| **Graceful degradation** | CLI, fonctionnalité optionnelle avec fallback           | `paracle_cli/ai_helper.py`               |

**Tous les patterns partagent** :
- ✅ Messages d'erreur clairs avec instructions d'installation
- ✅ Exception chaining (`from e`)
- ✅ Error codes tracés (`PARACLE-CORE-005`)
- ✅ Documentation des extras pip dans `pyproject.toml`

---

**Status**: Active | **Version**: 1.0 | **Last Updated**: 2026-01-10
