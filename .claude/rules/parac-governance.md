# .parac Governance Rules for Claude Code

## Principe Fondamental

> **`.parac/` est la source unique et immuable de vérité.**

Toute information concernant l'état du projet DOIT être reflétée dans `.parac/`.
Ne jamais contredire ce qui est documenté dans `.parac/`.

---

## Règles Obligatoires

### Règle 1: Lecture au Début de Session

**AVANT** de commencer tout travail, TOUJOURS lire:

```
1. .parac/memory/context/current_state.yaml  → État actuel
2. .parac/roadmap/roadmap.yaml               → Phase et priorités
3. .parac/memory/context/open_questions.md   → Questions en attente
```

Format de confirmation:
```
SESSION START
=============
Phase: [current_phase.id] - [current_phase.name]
Progress: [current_phase.progress]
Focus: [current_phase.focus_areas]

Source of truth verified: .parac/
```

### Règle 2: Ne Jamais Contredire .parac/

Si une information diffère entre:
- La conversation et `.parac/` → `.parac/` a raison
- Ta mémoire et `.parac/` → `.parac/` a raison
- Une demande utilisateur et `.parac/` → Signaler l'incohérence

```
INCOHÉRENCE DÉTECTÉE
====================
Source: [conversation/demande]
Dit: [X]

.parac/ dit: [Y]

.parac/ est la source de vérité.
Voulez-vous mettre à jour .parac/ pour refléter [X]?
```

### Règle 3: Mise à Jour en Fin de Session

**APRÈS** chaque session significative, PROPOSER des mises à jour:

```
SESSION END - Mises à jour .parac/ proposées
=============================================

1. current_state.yaml:
   - progress: [ancien] → [nouveau]
   - completed: + [nouveaux items]
   - in_progress: [changements]

2. decisions.md (si applicable):
   - ADR-XXX: [nouvelle décision]

3. open_questions.md (si applicable):
   - Nouvelle question: [Q]
   - Question résolue: [Q]

Voulez-vous que j'applique ces mises à jour?
```

### Règle 4: Documenter Immédiatement les Décisions

Toute décision architecturale significative DOIT être documentée:

```markdown
### ADR-XXX: [Titre]

**Date:** [YYYY-MM-DD]
**Status:** Accepted

**Context:**
[Pourquoi cette décision était nécessaire]

**Decision:**
[Ce qui a été décidé]

**Rationale:**
[Pourquoi cette option a été choisie]

**Consequences:**
- [Impact positif/négatif]

**Alternatives Rejected:**
- [Option rejetée]: [Raison]
```

### Règle 5: Questions avec Owners et Deadlines

Toute nouvelle question DOIT avoir:
- Un owner (qui décide)
- Une deadline (quand décider)
- Une priorité (High/Medium/Low)

```markdown
### Q#: [Titre]

**Status:** Open
**Priority:** [High/Medium/Low]
**Owner:** [Agent/Role]
**Deadline:** [Phase X End / Date]
**Context:** [Contexte]
```

---

## Checkpoints Automatiques

### Après Chaque Tâche Majeure

Quand un deliverable est complété:

1. Proposer mise à jour `current_state.yaml`:
   ```yaml
   deliverables:
     - name: "[Deliverable]"
       status: completed
       completion: 100%
       completed_date: "[Date]"
   ```

2. Recalculer le progress de la phase

### Après Chaque Décision

1. Ajouter à `decisions.md`
2. Si résout une question → mettre à jour `open_questions.md`

### Après Chaque Erreur/Blocage

1. Documenter dans `current_state.yaml` sous `blockers:`
2. Créer une question si décision nécessaire

---

## Format de Commit .parac/

Quand des fichiers `.parac/` sont modifiés:

```
docs(parac): [description courte]

- [Changement 1]
- [Changement 2]

Refs: [Phase/ADR/Question]
```

Exemples:
```
docs(parac): update phase 1 progress to 25%

- Mark domain_models as in_progress
- Update metrics

Refs: Phase 1

docs(parac): add ADR-009 for event store decision

- Decision: Use SQLite for v0.0.1
- Resolves Q2

Refs: ADR-009, Q2
```

---

## Validation Avant Proposition

Avant de proposer des changements `.parac/`:

- [ ] Les fichiers YAML sont syntaxiquement corrects
- [ ] `current_state.yaml` et `roadmap.yaml` sont cohérents
- [ ] Les questions ont owners et deadlines
- [ ] Les décisions sont complètes (context, decision, rationale)
- [ ] Les métriques sont réalistes

---

## Fichiers Critiques

| Fichier | Quand Mettre à Jour |
|---------|---------------------|
| `current_state.yaml` | Chaque session |
| `roadmap.yaml` | Changement de phase, milestone |
| `decisions.md` | Chaque décision architecturale |
| `open_questions.md` | Nouvelle question ou résolution |

---

## Anti-Patterns

### ❌ Ne PAS Faire

1. **Ignorer `.parac/`** et travailler de mémoire
2. **Modifier sans proposer** - toujours demander confirmation
3. **Omettre les décisions** - tout doit être tracé
4. **Laisser les questions sans owner**
5. **Ne pas mettre à jour le progress**

### ✅ Faire

1. **Lire `.parac/` systématiquement** au début
2. **Proposer les mises à jour** en fin de session
3. **Documenter immédiatement** les décisions
4. **Maintenir la cohérence** entre fichiers
5. **Signaler les incohérences** détectées

---

## Intégration avec Session Protocol

Ce fichier complète `.claude/rules/session-protocol.md`:

- **session-protocol.md** : Comment gérer les sessions
- **parac-governance.md** : Comment maintenir `.parac/` à jour

Les deux DOIVENT être suivis ensemble.
