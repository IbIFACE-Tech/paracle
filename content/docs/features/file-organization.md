# Quick Reference: Où placer les fichiers ?

> **Paracle utilise Paracle pour se développer (dogfooding)**

## 🎯 Règle d'Or

**"Un client utilisant Paracle aurait-il ce fichier ?"**

- ✅ **OUI** → `.parac/` (dogfooding - gouvernance)
- ❌ **NON** → `scripts/` (développement) ou `packages/` (produit)

---

## 📁 Structure

```
paracle/
│
├── packages/              # PRODUIT (publié sur PyPI)
│   ├── paracle_core/     # Code du framework
│   ├── paracle_api/
│   └── paracle_cli/
│
├── .parac/               # UTILISATEUR (dogfooding)
│   ├── agents/           # Nos agents
│   ├── memory/           # État du projet
│   ├── roadmap/          # Notre roadmap
│   └── tools/hooks/      # Outils de gouvernance
│
└── scripts/              # DÉVELOPPEMENT
    ├── bump_version.py   # Version du framework
    ├── generate_changelog.py
    └── git_commit_automation.py
```

---

## 📋 Exemples

| Fichier              | Emplacement              | Raison                                 |
| -------------------- | ------------------------ | -------------------------------------- |
| `agent-logger.py`    | `.parac/tools/hooks/`    | Gouvernance (client l'aurait)          |
| `bump_version.py`    | `scripts/`               | Dev framework (client ne l'aurait pas) |
| `current_state.yaml` | `.parac/memory/context/` | État projet (client l'aurait)          |
| `governance.py`      | `packages/paracle_core/` | Code framework (publié PyPI)           |

---

## 📖 Documentation Complète

Voir **[.parac/DOGFOODING_SEPARATION.md](.parac/DOGFOODING_SEPARATION.md)** pour la documentation complète.

---

**Principe**: Séparation claire entre ce que nous DÉVELOPPONS (framework) et comment nous l'UTILISONS (dogfooding).
