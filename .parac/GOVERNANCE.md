# Paracle Governance Protocol

> **📖 Quick Reference**: See [STRUCTURE.md](STRUCTURE.md) for canonical `.parac/` folder structure and file placement rules.

## Contexte : Paracle conçoit Paracle

Ce projet utilise une approche **méta** : nous utilisons le framework Paracle pour concevoir Paracle lui-même.

```
┌─────────────────────────────────────────────────────────────┐
│                    PARACLE FRAMEWORK                        │
│                      packages/                              │
│                                                             │
│   Le PRODUIT que nous développons                          │
│   - Code source du framework                                │
│   - Génère les .parac/ pour les utilisateurs              │
└─────────────────────────────────────────────────────────────┘
                          ↓ génère
┌─────────────────────────────────────────────────────────────┐
│                   .parac/ WORKSPACE                         │
│                  (Côté utilisateur)                         │
│                                                             │
│   Ici : Notre propre utilisation du framework              │
│   - Gouvernance de notre développement                     │
│   - Source de vérité pour le projet Paracle lui-même      │
└─────────────────────────────────────────────────────────────┘
```

**Nous sommes à la fois développeurs ET utilisateurs du framework.**

---

## Principe Fondamental

> **Le répertoire `.parac/` est la source unique et immuable de vérité pour le projet.**

Ce `.parac/` est notre **dogfooding** - il représente ce qu'un utilisateur du framework aurait pour gérer son projet.

Toute information concernant l'état du projet, les décisions, les politiques, et la mémoire du projet DOIT être reflétée dans `.parac/`. Aucune information critique ne doit exister uniquement dans la mémoire d'un agent IA ou dans des conversations.

---

## Règles de Gouvernance

### Règle 1: Traçabilité Totale

Toute décision architecturale, tout changement de scope, toute modification de roadmap DOIT être documentée dans `.parac/`.

| Type de Changement      | Fichier à Mettre à Jour                                      |
| ----------------------- | ------------------------------------------------------------ |
| Décision architecturale | `roadmap/decisions.md`                                       |
| Changement de phase     | `roadmap/roadmap.yaml` + `memory/context/current_state.yaml` |
| Nouvelle question       | `memory/context/open_questions.md`                           |
| Résolution de question  | `memory/context/open_questions.md` → `roadmap/decisions.md`  |
| Nouvelle politique      | `policies/policy-pack.yaml`                                  |
| Modification d'agent    | `agents/specs/<agent>.md`                                    |
| Nouveau savoir          | `memory/knowledge/<topic>.md`                                |

### Règle 2: Immutabilité des Décisions

Une fois une décision documentée dans `decisions.md`:
- Elle ne peut PAS être modifiée sans créer une nouvelle ADR
- L'historique est préservé
- Les raisons de changement sont documentées

### Règle 3: Synchronisation Obligatoire

Avant et après chaque session de travail:
1. **Début**: Lire `current_state.yaml` pour contexte
2. **Fin**: Mettre à jour `current_state.yaml` avec les changements

---

## Protocole de Mise à Jour

### À Chaque Session

```
┌─────────────────────────────────────────────────────────────┐
│                    SESSION START                            │
├─────────────────────────────────────────────────────────────┤
│ 1. Lire .parac/memory/context/current_state.yaml           │
│ 2. Vérifier .parac/memory/context/open_questions.md        │
│ 3. Consulter .parac/roadmap/roadmap.yaml                   │
│ 4. Confirmer la phase et les priorités actuelles           │
│ 5. Exécuter `paracle sync --roadmap` pour vérifier         │
│    l'alignement roadmap/state                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    [TRAVAIL EN COURS]
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     SESSION END                             │
├─────────────────────────────────────────────────────────────┤
│ 1. Mettre à jour current_state.yaml                        │
│    - progress: X%                                          │
│    - completed: [nouveaux items]                           │
│    - in_progress: [items en cours]                         │
│                                                             │
│ 2. Documenter les décisions dans decisions.md              │
│                                                             │
│ 3. Ajouter/Résoudre les questions dans open_questions.md   │
│                                                             │
│ 4. Mettre à jour roadmap.yaml si milestone atteint         │
│                                                             │
│ 5. Exécuter `paracle sync --roadmap` pour valider          │
│    la cohérence finale                                      │
│                                                             │
│ 5. Créer weekly_summary.md si fin de semaine               │
└─────────────────────────────────────────────────────────────┘
```

### À Chaque Milestone

Quand un deliverable majeur est complété:

1. **Mettre à jour `roadmap.yaml`**

   ```yaml
   deliverables:
     - name: "Feature X"
       status: completed  # ← Changer
       completion: 100%   # ← Mettre à 100%
       completed_date: "YYYY-MM-DD"  # ← Ajouter
   ```

2. **Mettre à jour `current_state.yaml`**

   ```yaml
   current_phase:
     progress: XX%  # ← Recalculer
     completed:
       - feature_x  # ← Ajouter
   ```

3. **Vérifier la cohérence**

   ```bash
   paracle sync --roadmap
   # Devrait montrer aucun avertissement après mise à jour
   ```

4. **Créer un résumé** dans `memory/summaries/`

### À Chaque Changement de Phase

1. Archiver le résumé de phase dans `memory/summaries/phase_N_completion.md`

2. Mettre à jour `roadmap.yaml`:

   ```yaml
   phases:
     - id: phase_N
       status: completed
       completed_date: "YYYY-MM-DD"
     - id: phase_N+1
       status: in_progress
       started_date: "YYYY-MM-DD"
   ```

3. Mettre à jour `current_state.yaml`:

   ```yaml
   current_phase:
     id: phase_N+1
     status: in_progress
     progress: 0%
   previous_phase:
     id: phase_N
     status: completed
   ```

4. **Valider l'alignement**

   ```bash
   paracle sync --roadmap
   # Devrait confirmer nouvelle phase sans avertissement
   ```

---

## Fichiers Critiques et Leur Rôle

### Source de Vérité Principale

| Fichier                             | Rôle                                  | Fréquence de MAJ |
| ----------------------------------- | ------------------------------------- | ---------------- |
| `roadmap/roadmap.yaml`              | Roadmap officielle, phases, métriques | Par milestone    |
| `memory/context/current_state.yaml` | État actuel du projet                 | Chaque session   |
| `roadmap/decisions.md`              | Décisions architecturales             | Par décision     |

### Contexte et Mémoire

| Fichier                            | Rôle                  | Fréquence de MAJ     |
| ---------------------------------- | --------------------- | -------------------- |
| `memory/context/open_questions.md` | Questions en attente  | Selon besoin         |
| `memory/knowledge/*.md`            | Base de connaissances | Quand nouveau savoir |
| `memory/summaries/*.md`            | Résumés périodiques   | Hebdomadaire/Phase   |

### Gouvernance

| Fichier                     | Rôle                  | Fréquence de MAJ |
| --------------------------- | --------------------- | ---------------- |
| `policies/policy-pack.yaml` | Politiques actives    | Rarement         |
| `policies/security.yaml`    | Règles de sécurité    | Rarement         |
| `agents/manifest.yaml`      | Registre des agents   | Par nouvel agent |
| `agents/specs/*.md`         | Spécifications agents | Par modification |

---

## Règle 4: File Placement (NEW)

> **Toujours respecter la structure canonique définie dans `STRUCTURE.md`**

Chaque fichier a une place spécifique dans `.parac/`:

| Type de Fichier         | Emplacement Correct            | ❌ Erreur Commune        |
| ----------------------- | ------------------------------ | ----------------------- |
| **Operational Data**    | `.parac/memory/data/*.db`      | `.parac/*.db` (root)    |
| **Logs**                | `.parac/memory/logs/*.log`     | `packages/*/logs/`      |
| **Knowledge**           | `.parac/memory/knowledge/*.md` | `.parac/*.md`           |
| **Decisions (ADRs)**    | `.parac/roadmap/decisions.md`  | `.parac/decisions.md`   |
| **Agent Specs**         | `.parac/agents/specs/*.md`     | `.parac/agents/*.md`    |
| **Execution Artifacts** | `.parac/runs/` (gitignored)    | `packages/*/artifacts/` |
| **User Documentation**  | `docs/` (NOT in .parac)        | `.parac/docs/`          |

**Before creating any new file in .parac/, consult [STRUCTURE.md](STRUCTURE.md) first.**

---

## Commandes de Synchronisation

### Vérification de Cohérence

```bash
# Vérifier que tous les fichiers requis existent
make parac-check

# Valider la syntaxe YAML
make parac-validate

# Valider la structure .parac/ (NEW)
paracle validate structure

# Vérifier les fichiers mal placés (NEW)
paracle validate structure --strict

# Générer un rapport d'état
make parac-status
```

### Mise à Jour Automatique (Future)

```bash
# Mettre à jour current_state depuis git
paracle sync state

# Corriger automatiquement les fichiers mal placés (NEW)
paracle validate structure --fix

# Générer le résumé hebdomadaire
paracle summary weekly

# Archiver une phase complétée
paracle phase complete phase_1
```

---

## Intégration avec Claude Code

### Règles pour l'Agent IA

L'agent IA (Claude, GitHub Copilot, etc.) DOIT:

**IMPORTANT**: Les agents Paracle sont des **programmes exécutables**, pas des personas à adopter.
- ✅ **Dire**: "Je vais exécuter CoderAgent..." ou "Suivant les standards CoderAgent..."
- ❌ **Ne PAS dire**: "J'adopte le persona CoderAgent..."
- 📖 **Voir**: `docs/agent-execution-model.md` pour explication complète

1. **Lire `.parac/` au début de chaque session**
   ```
   SOURCE OF TRUTH: .parac/memory/context/current_state.yaml
   ```

2. **Ne jamais contredire `.parac/`**
   - Si une information diffère entre la conversation et `.parac/`, `.parac/` a raison
   - Signaler les incohérences et proposer une mise à jour

3. **Proposer des mises à jour `.parac/`**
   - Après chaque décision significative
   - À la fin de chaque session
   - Quand un deliverable est complété

4. **Documenter les décisions**
   - Toute décision architecturale → `decisions.md`
   - Toute question → `open_questions.md`
   - Tout rejet d'approche → documenté avec raison

### Prompts Obligatoires

**Début de session:**
```
Je vais lire l'état actuel du projet depuis .parac/memory/context/current_state.yaml
pour m'assurer de travailler avec le contexte correct.
```

**Fin de session:**
```
Avant de terminer, je propose les mises à jour suivantes pour .parac/:
1. current_state.yaml: [changements]
2. decisions.md: [nouvelles décisions]
3. open_questions.md: [questions ajoutées/résolues]

Voulez-vous que j'applique ces mises à jour?
```

---

## Validation et Audit

### Checklist de Validation

Avant chaque commit touchant `.parac/`:

- [ ] `current_state.yaml` reflète l'état réel
- [ ] `roadmap.yaml` a les bons statuts de phase
- [ ] Toutes les décisions sont dans `decisions.md`
- [ ] Les questions ouvertes ont des owners et deadlines
- [ ] Les métriques sont à jour
- [ ] La syntaxe YAML est valide

### Audit Périodique

**Hebdomadaire:**
- Vérifier cohérence `current_state.yaml` vs réalité
- Mettre à jour les métriques
- Créer `weekly_summary.md`

**Par Phase:**
- Audit complet de `.parac/`
- Vérifier toutes les décisions documentées
- Archiver les artefacts de phase

---

## Anti-Patterns à Éviter

### ❌ Ne PAS Faire

1. **Décider sans documenter**
   - Toute décision significative DOIT être dans `decisions.md`

2. **Modifier le passé**
   - Ne pas supprimer ou modifier les décisions passées
   - Créer une nouvelle ADR si changement nécessaire

3. **Ignorer les questions ouvertes**
   - Chaque question DOIT avoir un owner et une deadline

4. **Laisser `current_state.yaml` devenir obsolète**
   - Mise à jour obligatoire à chaque session

5. **Créer des sources de vérité parallèles**
   - Pas de TODO.md séparé
   - Pas de notes dans d'autres fichiers
   - Tout dans `.parac/`

### ✅ Faire

1. **Documenter immédiatement** les décisions
2. **Lire `.parac/` avant** de commencer à travailler
3. **Mettre à jour `.parac/` après** chaque session
4. **Utiliser les templates** fournis
5. **Maintenir la cohérence** entre tous les fichiers

---

## Évolution de ce Protocole

Ce document (`GOVERNANCE.md`) peut être mis à jour pour:
- Ajouter de nouvelles règles
- Clarifier des processus existants
- Documenter des exceptions approuvées

Toute modification DOIT être documentée dans `roadmap/decisions.md`.

---

## Références

- Roadmap: `roadmap/roadmap.yaml`
- État actuel: `memory/context/current_state.yaml`
- Décisions: `roadmap/decisions.md`
- Questions: `memory/context/open_questions.md`
- Claude Code Config: `../.claude/CLAUDE.md`
