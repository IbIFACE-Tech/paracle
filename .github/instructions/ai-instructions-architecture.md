# Architecture des Instructions AI pour PARACLE

## Principe Fondamental

> **Le `.parac/` est l'unique source de vérité pour les agents et la gouvernance du projet.**

Les fichiers d'instructions AI (`.cursorrules`, `.github-copilot.md`, etc.) sont de **simples adaptateurs** qui pointent vers `.parac/`. Ils ne dupliquent JAMAIS la définition des agents.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    .parac/ (Source Unique)                  │
│                                                             │
│  ├── GOVERNANCE.md          - Règles du projet             │
│  ├── agents/specs/          - Définitions des agents       │
│  │   ├── pm.md             - UNIQUE définition PM         │
│  │   ├── architect.md      - UNIQUE définition Architect  │
│  │   ├── coder.md          - UNIQUE définition Coder      │
│  │   └── ...                                              │
│  ├── memory/                - Mémoire du projet           │
│  └── roadmap/               - Roadmap et décisions        │
└─────────────────────────────────────────────────────────────┘
                          ↑ référencé par
┌─────────────────────────────────────────────────────────────┐
│              Instructions AI (Adaptateurs)                  │
│                                                             │
│  .cursorrules           → "Lis .parac/, adopte agents"    │
│  .github-copilot.md     → "Lis .parac/, adopte agents"    │
│  .clinerules            → "Lis .parac/, adopte agents"    │
│  .windsurfrules         → "Lis .parac/, adopte agents"    │
│  .deepseek-coder.md     → "Lis .parac/, adopte agents"    │
└─────────────────────────────────────────────────────────────┘
```

## Avantages

### ✅ Écrire Les Agents Une Seule Fois

Les agents sont définis dans `.parac/agents/specs/*.md` :
- `pm.md` - Project Manager
- `architect.md` - System Architect
- `coder.md` - Developer
- `tester.md` - QA Engineer
- `reviewer.md` - Code Reviewer
- `documenter.md` - Tech Writer

**Une seule définition, utilisée partout.**

### ✅ Changement d'IDE Sans Réécriture

Passer de Cursor à Copilot à Claude :
1. Change le fichier d'instructions (`.cursorrules` → `.github-copilot.md`)
2. **Les agents restent identiques** dans `.parac/agents/specs/`
3. L'assistant lit `.parac/` et adopte les mêmes agents

### ✅ Maintenance Simplifiée

Modifier un agent :
1. Édite `.parac/agents/specs/coder.md`
2. **Tous les IDE/assistants** utilisent automatiquement la nouvelle version
3. Pas de synchronisation manuelle nécessaire

### ✅ Mémoire Partagée

Tous les assistants AI consultent le même `.parac/` :
- Même contexte projet
- Même roadmap
- Même historique de décisions
- Même état actuel

## Structure des Instructions AI

Chaque fichier d'instructions AI doit :

### 1. Pointer vers .parac/

```markdown
# Instructions pour [IDE/Assistant]

## Source Unique de Vérité

Consulte `.parac/` pour toutes les informations sur :
- Agents disponibles : `.parac/agents/specs/*.md`
- Gouvernance : `.parac/GOVERNANCE.md`
- État actuel : `.parac/memory/context/current_state.yaml`
- Roadmap : `.parac/roadmap/roadmap.yaml`
```

### 2. Expliquer Comment Adopter Les Agents

```markdown
## Agents Disponibles

Les agents sont définis dans `.parac/agents/specs/`.

Pour chaque requête :
1. Identifie l'agent approprié
2. Lis sa spec dans `.parac/agents/specs/{agent}.md`
3. Adopte ses responsabilités et standards
4. Exécute la tâche selon son workflow
```

### 3. Spécificités de l'IDE

```markdown
## Spécificités [IDE]

- Format de fichier : [.cursorrules / .md / etc.]
- Limitations : [tokens, contexte, etc.]
- Commandes disponibles : [spécifique à l'IDE]
```

### 4. Ne PAS Dupliquer

```markdown
❌ NE PAS dupliquer les définitions d'agents
❌ NE PAS réécrire le GOVERNANCE.md
❌ NE PAS copier la roadmap

✅ TOUJOURS lire depuis .parac/
✅ TOUJOURS référencer la source
✅ TOUJOURS logger dans .parac/memory/logs/
```

## Templates Types

### Template Minimaliste

```markdown
# [IDE] Instructions

Consulte `.parac/` pour :
- Agents : `.parac/agents/specs/*.md`
- Gouvernance : `.parac/GOVERNANCE.md`
- Contexte : `.parac/memory/context/current_state.yaml`

Workflow :
1. Lis .parac/ pour comprendre le contexte
2. Adopte l'agent approprié depuis .parac/agents/specs/
3. Suis les standards de cet agent
4. Log l'action dans .parac/memory/logs/agent_actions.log
```

### Template Détaillé

Ajoute des explications spécifiques à l'IDE mais **toujours** pointe vers `.parac/`.

## Exemples Concrets

### Cursor → Copilot → Claude

**Même projet, différents assistants** :

```bash
# Utiliser Cursor
.cursorrules → Lit .parac/agents/specs/coder.md

# Changer pour Copilot
.github/copilot-instructions.md → Lit .parac/agents/specs/coder.md

# Changer pour Claude
.claude/instructions.md → Lit .parac/agents/specs/coder.md
```

**Résultat** : Même comportement, mêmes agents, même contexte.

## Migration des Instructions Existantes

Pour migrer des instructions qui dupliquent les définitions :

1. **Identifier les duplications** : Agents, règles, gouvernance
2. **Déplacer dans .parac/** : Une seule fois
3. **Remplacer par référence** : Pointer vers .parac/
4. **Tester** : Vérifier que l'assistant lit bien .parac/

## Validation

Un bon fichier d'instructions AI :

- ✅ Référence `.parac/` comme source de vérité
- ✅ Explique comment lire `.parac/agents/specs/`
- ✅ N'a PAS de définitions d'agents dupliquées
- ✅ Est spécifique à l'IDE (shortcuts, limitations)
- ✅ Est court (< 200 lignes idéalement)

Un mauvais fichier d'instructions AI :

- ❌ Duplique les définitions d'agents
- ❌ Contient sa propre gouvernance
- ❌ Ignore `.parac/`
- ❌ Est trop long (> 500 lignes)
- ❌ Doit être réécrit quand on change d'IDE

## Bénéfices pour les Utilisateurs

### Développeur Solo

- Configure `.parac/` une fois
- Change d'IDE sans réécrire
- Contexte toujours cohérent

### Équipe

- `.parac/` versionné dans Git
- Tous les membres ont les mêmes agents
- Changement d'agent = un seul commit

### Multi-Projet

- Template `.parac/` réutilisable
- Instructions AI pointent vers `.parac/`
- Maintenance centralisée

## Implémentation

### Étape 1 : .parac/ comme Source Unique

```
.parac/
├── agents/specs/           ← UNIQUE SOURCE pour agents
│   ├── pm.md
│   ├── architect.md
│   ├── coder.md
│   ├── tester.md
│   ├── reviewer.md
│   └── documenter.md
├── GOVERNANCE.md           ← UNIQUE SOURCE pour règles
├── memory/                 ← UNIQUE SOURCE pour contexte
└── roadmap/                ← UNIQUE SOURCE pour roadmap
```

### Étape 2 : Instructions AI comme Adaptateurs

```
.cursorrules              → "Lis .parac/, adopte agents"
.github-copilot.md        → "Lis .parac/, adopte agents"
.clinerules               → "Lis .parac/, adopte agents"
.windsurfrules            → "Lis .parac/, adopte agents"
```

### Étape 3 : Templates Génériques

Dans `templates/ai-instructions/` :
- Template minimaliste
- Template détaillé
- Guide de migration
- Exemples par IDE

## Conclusion

> **Write agents once in `.parac/`, use everywhere with any IDE.**

Cette architecture garantit :
- ✅ Cohérence entre IDEs
- ✅ Maintenance simplifiée
- ✅ Migration facile
- ✅ Mémoire partagée
- ✅ Évolutivité

---

**Date**: 2025-12-25
**Auteur**: ArchitectAgent
**Statut**: Architecture de référence
