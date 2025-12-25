# Architecture de Synchronisation PARACLE

## Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                   MODIFICATIONS AGENTS                          │
│              .parac/agents/specs/*.md                           │
└─────────────┬───────────────────────────────────────────────────┘
              │
              ├─────────────────────────────────────┐
              │                                     │
              ▼                                     ▼
┌─────────────────────────────┐    ┌────────────────────────────┐
│     WORKFLOW MANUEL         │    │    WORKFLOW AUTOMATIQUE    │
│                             │    │                            │
│  paracle parac sync         │    │  1. Git Hooks             │
│         --manifest          │    │     (pre-commit)          │
│                             │    │                            │
│  • Contrôle total          │    │  2. Sync Watch            │
│  • Batch updates           │    │     (temps réel)          │
│  • Validation manuelle     │    │                            │
└─────────────┬───────────────┘    └──────────────┬─────────────┘
              │                                     │
              └──────────────┬──────────────────────┘
                             ▼
              ┌──────────────────────────────┐
              │   PARACLE FRAMEWORK          │
              │                              │
              │  • agent_discovery.py        │
              │  • manifest_generator.py     │
              │                              │
              │  Scanne .parac/agents/specs/ │
              │  Parse markdown              │
              │  Extrait métadonnées         │
              └──────────────┬───────────────┘
                             ▼
              ┌──────────────────────────────┐
              │    .parac/manifest.yaml      │
              │                              │
              │  • Auto-généré               │
              │  • Machine-readable          │
              │  • Versionné git             │
              │  • 6 agents découverts       │
              └──────────────┬───────────────┘
                             │
              ┌──────────────┴───────────────┐
              ▼                              ▼
┌──────────────────────────┐   ┌──────────────────────────┐
│   INTÉGRATION IDE        │   │   CLI & API PYTHON       │
│                          │   │                          │
│  • Copilot               │   │  paracle agents list     │
│  • Cursor                │   │  paracle agents get pm   │
│  • Claude                │   │  paracle agents export   │
│  • Cline                 │   │                          │
│  • Windsurf              │   │  AgentDiscovery()        │
│                          │   │  ManifestGenerator()     │
│  (Phase 2: Generator)    │   │                          │
└──────────────────────────┘   └──────────────────────────┘
```

## Flux de Synchronisation Détaillé

### 1. Modification d'un Agent

```
User Action:
  vim .parac/agents/specs/coder.md
  [Modifie les capabilities]
  :wq

           ↓

Git Add/Commit:
  git add .parac/agents/specs/coder.md
  git commit -m "Updated coder capabilities"

           ↓

Git Hook Triggered:
  .git/hooks/pre-commit
  ├─ Détecte: .parac/agents/specs/coder.md modifié
  ├─ Execute: paracle parac sync --manifest
  └─ Stage: git add .parac/manifest.yaml

           ↓

Framework Discovery:
  agent_discovery.py
  ├─ Scanne: .parac/agents/specs/
  ├─ Parse: coder.md
  ├─ Extrait:
  │   ├─ name: "Coder Agent"
  │   ├─ role: "Implementation..."
  │   └─ capabilities: [code impl, quality, integration]
  └─ Return: AgentMetadata

           ↓

Manifest Generation:
  manifest_generator.py
  ├─ Collecte tous les agents
  ├─ Génère YAML structuré
  └─ Écrit: .parac/manifest.yaml

           ↓

Commit Completed:
  .parac/agents/specs/coder.md     (modifié)
  .parac/manifest.yaml              (auto-généré)
```

### 2. Mode Watch (Développement Actif)

```
Terminal 1:
  python .parac/hooks/sync-watch.py
  👀 Watching .parac/agents/specs/ for changes...

           ↓

Terminal 2:
  code .parac/agents/specs/architect.md
  [Modification et sauvegarde]

           ↓

Watcher Détecte:
  📝 Detected change: architect.md

           ↓

Auto-Regeneration:
  🔄 Regenerating manifest...

  agent_discovery.py
    ↓
  manifest_generator.py
    ↓
  .parac/manifest.yaml

           ↓

Feedback:
  ✅ Manifest regenerated

  [Continue watching...]
```

### 3. API Python (Programmatique)

```python
# Script personnalisé
from paracle_core.parac.agent_discovery import AgentDiscovery
from paracle_core.parac.manifest_generator import ManifestGenerator

# Découvrir
discovery = AgentDiscovery(Path(".parac"))
agents = discovery.discover_agents()

# Générer
generator = ManifestGenerator(Path(".parac"))
generator.write_manifest()

           ↓

Output:
  .parac/manifest.yaml (régénéré)
```

## Diagramme de Séquence

### Workflow Git Hook

```
┌──────┐        ┌─────┐      ┌────────┐     ┌──────────┐     ┌──────────┐
│ User │        │ Git │      │ Hook   │     │ PARACLE  │     │ manifest │
└──┬───┘        └──┬──┘      └───┬────┘     └────┬─────┘     └────┬─────┘
   │               │              │               │                │
   │ edit agent.md │              │               │                │
   ├──────────────>│              │               │                │
   │               │              │               │                │
   │ git commit    │              │               │                │
   ├──────────────>│              │               │                │
   │               │              │               │                │
   │               │ pre-commit   │               │                │
   │               ├─────────────>│               │                │
   │               │              │               │                │
   │               │              │ paracle sync  │                │
   │               │              ├──────────────>│                │
   │               │              │               │                │
   │               │              │               │ discover()     │
   │               │              │               ├────────┐       │
   │               │              │               │        │       │
   │               │              │               │<───────┘       │
   │               │              │               │                │
   │               │              │               │ generate()     │
   │               │              │               ├───────────────>│
   │               │              │               │                │
   │               │              │               │<───────────────│
   │               │              │               │                │
   │               │              │<──────────────│                │
   │               │              │               │                │
   │               │ git add      │               │                │
   │               │<─────────────│               │                │
   │               │              │               │                │
   │ commit done   │              │               │                │
   │<──────────────│              │               │                │
   │               │              │               │                │
```

## États du Système

```
┌────────────────────────────────────────────────────────────────┐
│                      ÉTAT SYNCHRONISÉ ✅                       │
│                                                                │
│  • agents specs == manifest                                    │
│  • git clean                                                   │
│  • `paracle agents list` == `cat manifest.yaml`               │
└────────────────────────────────────────────────────────────────┘

                              ↓ ↑
                    Modification détectée

┌────────────────────────────────────────────────────────────────┐
│                   ÉTAT NON-SYNCHRONISÉ ⚠️                      │
│                                                                │
│  • agents specs modifiés                                       │
│  • manifest obsolète                                           │
│  • git dirty (uncommitted changes)                            │
└────────────────────────────────────────────────────────────────┘

                              ↓
                    paracle parac sync --manifest
                              ↓

┌────────────────────────────────────────────────────────────────┐
│                      ÉTAT SYNCHRONISÉ ✅                       │
└────────────────────────────────────────────────────────────────┘
```

## Composants du Système

```
.parac/
├── agents/
│   └── specs/                    ← SOURCE DE VÉRITÉ
│       ├── pm.md                 │  (édité manuellement)
│       ├── architect.md          │
│       ├── coder.md              │
│       ├── tester.md             │
│       ├── reviewer.md           │
│       └── documenter.md         │
│                                 │
├── manifest.yaml                 ← AUTO-GÉNÉRÉ
│   (ne pas éditer manuellement) │  (par le framework)
│                                 │
└── hooks/                        ← AUTOMATION
    ├── install-hooks.ps1         │  (scripts helper)
    ├── install-hooks.sh          │
    └── sync-watch.py             │
                                  ↓
.git/hooks/
└── pre-commit                    ← AUTOMATION
    (auto-installé)                  (git integration)

packages/paracle_core/parac/
├── agent_discovery.py            ← FRAMEWORK
├── manifest_generator.py         │  (logique core)
└── ...                           │

packages/paracle_cli/commands/
├── agents.py                     ← CLI
└── parac.py                      │  (interface utilisateur)
```

## Points d'Extension

```
┌─────────────────────────────────────────────────────────────┐
│                    EXTENSIBILITÉ                            │
└─────────────────────────────────────────────────────────────┘

1. Nouveau Watcher Type
   └─> .parac/hooks/sync-watch-custom.py

2. Nouveau Format Export
   └─> agent_discovery.py: add to_xml(), to_toml()

3. Nouveaux Hooks Git
   └─> .git/hooks/post-commit, post-merge, etc.

4. CI/CD Integration
   └─> .github/workflows/sync-agents.yml

5. IDE Extension
   └─> Read manifest.yaml directement

6. MCP Server (Future)
   └─> Real-time sync via Model Context Protocol
```

## Métriques de Performance

```
Opération                    Temps Typique    Impact
─────────────────────────────────────────────────────────
Discovery (6 agents)         ~50ms            Très rapide
Manifest generation          ~20ms            Très rapide
Git hook overhead            ~100ms           Négligeable
Watch mode detection         <1s              Temps réel
Full sync (--manifest)       ~150ms           Très rapide
```

## Garanties du Système

✅ **Atomicité** : Manifeste toujours complet ou inchangé
✅ **Idempotence** : Regénérer plusieurs fois = même résultat
✅ **Isolation** : Pas de side-effects sur autres fichiers
✅ **Traçabilité** : Tout versionné dans git
✅ **Performance** : <200ms pour synchronisation complète

## Pour en Savoir Plus

- [Guide de Synchronisation](synchronization-guide.md)
- [Agent Discovery System](agent-discovery.md)
- [ADR-008](.parac/roadmap/decisions.md#adr-008)
