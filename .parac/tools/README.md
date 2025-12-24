# Tools Directory

Ce dossier contient les définitions des outils et plugins disponibles pour les agents, ainsi que les outils de maintenance du workspace .parac.

## Structure

- `registry.yaml` - Registre des outils disponibles
- `custom/` - Outils personnalisés du projet
- `builtin/` - Outils intégrés au framework
- `auto-maintain.py` - **Script de maintenance automatique du .parac** 🔄
- `hooks/` - Git hooks pour automatisation

## Maintenance Automatique du .parac

### Script Principal: `auto-maintain.py`

**But**: Synchronise automatiquement l'état du workspace `.parac/` avec les changements du projet.

**Utilisation**:
```bash
# Exécution manuelle
python .parac/tools/auto-maintain.py

# Mode simulation (voir ce qui serait modifié)
python .parac/tools/auto-maintain.py --dry-run

# Mode verbose
python .parac/tools/auto-maintain.py --verbose
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

Exécute automatiquement `auto-maintain.py` avant chaque commit.

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
