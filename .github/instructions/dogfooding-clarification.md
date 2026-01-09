# Clarification : Dogfooding et Relation Méta

## Résumé

Ce fichier clarifie la relation méta entre le framework PARACLE et son utilisation dans ce projet.

## La Distinction Clé

### `packages/` = Le Framework (Produit)

C'est le **code source de PARACLE** :
- `paracle_domain/` - Domain models et entities
- `paracle_core/` - Application services
- `paracle_api/` - HTTP adapters (FastAPI)
- `paracle_cli/` - CLI commands (Click)
- `paracle_store/` - Repositories et persistence
- `paracle_events/` - Event bus
- `paracle_orchestration/` - Workflow engine

**Ce code génère/crée les `.parac/` pour les utilisateurs finaux.**

### `.parac/` = Notre Workspace Utilisateur (Dogfooding)

C'est **notre propre utilisation** du framework PARACLE :
- Gouvernance de CE projet
- Roadmap de CE projet
- Mémoire de CE projet
- Décisions pour CE projet

**Ce n'est PAS le code du framework, c'est notre instance utilisateur.**

## Dogfooding

```
┌──────────────────────────────────────────┐
│         NOUS (L'équipe)                  │
│                                          │
│  Rôle 1: Développeurs de PARACLE        │
│  → Travaillons dans packages/           │
│  → Créons le framework                  │
│                                          │
│  Rôle 2: Utilisateurs de PARACLE        │
│  → Utilisons .parac/                    │
│  → Gérons le projet avec le framework  │
└──────────────────────────────────────────┘
```

Nous sommes notre propre **premier utilisateur** ("eating our own dog food").

## Implications pour les Assistants IA

### Quand tu travailles sur `packages/`

- Tu développes le **framework PARACLE**
- Tu codes en Python avec Pydantic, FastAPI, etc.
- Tu crées les fonctionnalités que les utilisateurs utiliseront
- Tu génères la capacité de créer des `.parac/`

**Exemple** :
```python
# packages/paracle_core/parac/state.py
# Ceci est le CODE DU FRAMEWORK
class CurrentStateManager:
    def load_state(self, parac_dir: Path) -> CurrentState:
        # Code qui charge le current_state.yaml d'un utilisateur
        ...
```

### Quand tu travailles sur `.parac/`

- Tu utilises le **framework PARACLE** comme un utilisateur
- Tu mets à jour la gouvernance de CE projet
- Tu documentes les décisions pour CE projet
- Tu maintiens la mémoire de CE projet

**Exemple** :
```yaml
# .parac/memory/context/current_state.yaml
# Ceci est NOTRE UTILISATION DU FRAMEWORK
project:
  name: paracle-lite
  version: 0.0.1
  phase: phase_1
```

## Workflows Distincts

### Workflow 1 : Développer le Framework

```
1. User demande : "Ajoute une feature pour gérer les workflows"
2. Adopte CoderAgent
3. Code dans packages/paracle_orchestration/
4. Ajoute tests dans tests/
5. Met à jour .parac/ pour tracer cette action
```

### Workflow 2 : Gérer Ce Projet

```
1. User demande : "Mets à jour la roadmap avec la Phase 2"
2. Adopte PMAgent
3. Modifie .parac/roadmap/roadmap.yaml
4. Documente dans .parac/roadmap/decisions.md
5. Log l'action dans .parac/memory/logs/
```

## Questions Fréquentes

### Q: `.parac/` fait-il partie du produit PARACLE ?

**Non.** `.parac/` est notre **utilisation** du produit PARACLE pour gérer ce projet.

### Q: Les utilisateurs de PARACLE auront-ils un `.parac/` ?

**Oui.** Chaque projet utilisant PARACLE aura son propre `.parac/` généré par le framework.

### Q: Notre `.parac/` est-il un exemple pour les utilisateurs ?

**Oui et Non.**
- **Oui** : Il montre comment utiliser PARACLE en production
- **Non** : Chaque projet aura son propre contexte, roadmap, agents

### Q: Dois-je modifier `.parac/` ou `packages/` ?

Ça dépend :
- **Modifier `packages/`** : Pour ajouter/changer des features du framework
- **Modifier `.parac/`** : Pour gérer/documenter ce projet

### Q: Peut-on avoir du code dans `.parac/` ?

**Oui, mais limité :**
- Scripts d'automatisation (`.parac/hooks/`)
- Utilitaires de validation
- Pas de code métier du framework

## Analogie

Imagine que nous développons Microsoft Word :

- **`packages/`** = Le code source de Word (l'application)
- **`.parac/`** = Un document Word que NOUS utilisons pour gérer le projet de développement de Word

Nous utilisons notre propre outil (Word) pour documenter comment nous créons Word. C'est du dogfooding.

## Validation

Avant toute action, demande-toi :

✅ **Suis-je en train de développer le framework ?** → `packages/`
✅ **Suis-je en train de gérer ce projet ?** → `.parac/`

---

**Date**: 2025-12-25
**Auteur**: ArchitectAgent + DocumenterAgent
**Statut**: Source de vérité pour la relation méta
