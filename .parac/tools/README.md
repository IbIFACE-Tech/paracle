# Tools Directory

Ce dossier contient les définitions des outils et plugins disponibles pour les agents, ainsi que les outils de maintenance et automatisation du workspace .parac.

## Structure

```
tools/
├── registry.yaml       # Registre des outils disponibles pour les agents
├── custom/             # Outils personnalisés du projet
├── README.md           # Ce fichier
└── hooks/              # Scripts d'automatisation et git hooks
    ├── README.md              # Documentation complète des hooks
    ├── auto-maintain.py       # Maintenance automatique du .parac
    ├── install-hooks.ps1/sh   # Installation des git hooks
    ├── pre-commit             # Git pre-commit hook
    ├── sync-watch.py          # Watcher temps réel
    ├── agent-logger.py        # Logger d'actions agents
    ├── validate.py            # Validation .parac
    └── sync-state.py          # Synchronisation d'état
```

> **Note**: Les hooks ont été consolidés dans `tools/hooks/` pour une meilleure organisation.


## Maintenance Automatique du .parac

### Script Principal: `hooks/auto-maintain.py`

**But**: Synchronise automatiquement l'état du workspace `.parac/` avec les changements du projet.

**Utilisation**:

```bash
# Exécution manuelle
python .parac/tools/hooks/auto-maintain.py

# Mode simulation (voir ce qui serait modifié)
python .parac/tools/hooks/auto-maintain.py --dry-run

# Mode verbose
python .parac/tools/hooks/auto-maintain.py --verbose
```

**Ce qui est mis à jour**:

- `.parac/memory/context/current_state.yaml` - État actuel du projet
- `.parac/changelog.md` - Historique des changements
- `.parac/roadmap/roadmap.yaml` - Dernières réalisations

### Git Pre-Commit Hook

**Installation**:

```bash
cp .parac/tools/hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

Exécute automatiquement `hooks/auto-maintain.py` avant chaque commit.

### GitHub Action

Workflow CI/CD: `.github/workflows/maintain-parac.yml`

- Détecte les changements dans packages/, templates/, docs/, examples/
- Met à jour automatiquement le .parac
- Crée des commits auto sur main/develop
- Commente les PRs si mise à jour nécessaire

### Détection des Changements

Le système détecte automatiquement les modifications dans:
- 📦 `packages/` - Code du framework
- 📋 `templates/` - Templates utilisateurs
- 📚 `docs/` - Documentation
- 💡 `examples/` - Exemples de code
- 🗺️ `.roadmap/` - Fichiers de roadmap

### Meilleures Pratiques

✅ **À faire**:
- Installer le pre-commit hook pour sync automatique
- Tester avec `--dry-run` avant application
- Réviser les changements .parac avant push

❌ **À éviter**:
- Éditer manuellement les sections auto-générées
- Commiter sans exécuter la maintenance
- Ignorer les avertissements CI de sync

### Troubleshooting

**Hook ne s'exécute pas**:
```bash
chmod +x .git/hooks/pre-commit
```

**Dépendances Python manquantes**:
```bash
pip install pyyaml
```

---

## Types d'outils

### Outils intégrés (builtin)

- Web scraping
- API calls
- File operations
- Database queries
- Code execution

### Outils personnalisés (custom)

Créez vos propres outils en suivant l'interface standard :

```python
from paracle.tools import Tool

class MyTool(Tool):
    name = "my_tool"
    description = "Description de l'outil"

    async def execute(self, **kwargs):
        # Implementation
        pass
```

## Configuration

Les outils sont configurés dans `registry.yaml` et peuvent être attachés aux agents via leur `AgentSpec`.

## Sécurité

- Les outils ont des permissions définies dans `.parac/policies/security.yaml`
- Chaque outil doit déclarer ses besoins en termes d'accès
- Les outils externes nécessitent une approbation explicite
