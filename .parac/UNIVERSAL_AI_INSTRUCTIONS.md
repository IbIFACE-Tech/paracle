# Instructions Universelles pour Assistant IA
# Fonctionne avec: Cursor, Cline, Windsurf, Claude, Copilot, ChatGPT, et TOUT autre IDE/assistant

---

## 🎯 PRINCIPE FONDAMENTAL

> **Le répertoire `.parac/` est la SOURCE UNIQUE DE VÉRITÉ du projet.**

Avant TOUTE action, consulte `.parac/` pour comprendre le contexte, les règles, et l'état actuel.

## 🚨 CHECKLIST OBLIGATOIRE

**Avant TOUTE implémentation, lis le Pre-Flight Checklist:**

👉 **[.parac/PRE_FLIGHT_CHECKLIST.md](PRE_FLIGHT_CHECKLIST.md)**

**Version courte (4 minutes):**

```
✅ 1. Lire GOVERNANCE.md
✅ 2. Vérifier current_state.yaml (phase, progrès, en cours)
✅ 3. Consulter roadmap.yaml (focus phase, priorités)
✅ 4. Vérifier open_questions.md (blockers)
✅ 5. VALIDER: Tâche dans roadmap? Phase actuelle? Priorité? Dépendances?
✅ 6. Adopter agent persona
✅ 7. Vérifier policies
✅ 8. APRÈS: Logger dans agent_actions.log
✅ 9. APRÈS: Mettre à jour current_state.yaml si milestone
```

**PAS D'EXCEPTION. Cela garantit que tu travailles sur LA BONNE CHOSE au BON MOMENT.**

---

## 📖 LECTURE OBLIGATOIRE (Dans l'ordre)

Quand tu commences à travailler sur ce projet, lis ces 5 fichiers EN PREMIER:

```
1. .parac/GOVERNANCE.md                      # Règles du projet
2. .parac/manifest.yaml                      # Configuration workspace
3. .parac/agents/manifest.yaml               # Agents disponibles
4. .parac/memory/context/current_state.yaml  # État actuel du projet
5. .parac/roadmap/roadmap.yaml               # Phase et priorités
```

**Ces 5 fichiers te donnent le contexte complet. Ne commence JAMAIS sans les avoir lus.**

---

## 🚀 WORKFLOW STANDARD

### AVANT chaque tâche:

```
□ Quel est l'état actuel?    → .parac/memory/context/current_state.yaml
□ Quelle phase sommes-nous?  → .parac/roadmap/roadmap.yaml
□ Quelles sont les règles?   → .parac/GOVERNANCE.md
□ Quel agent adopter?        → .parac/agents/specs/{agent}.md
□ Y a-t-il des questions?    → .parac/memory/context/open_questions.md
```

### PENDANT la tâche:

1. **Adopte le bon agent persona** (voir `.parac/agents/specs/`)
   - Nouvelle feature → `coder`
   - Architecture → `architect`
   - Documentation → `documenter`
   - Planification → `pm`
   - Code review → `reviewer`
   - Tests → `tester`

2. **Suis les standards du projet**
   - Code style → `.parac/policies/CODE_STYLE.md`
   - Testing → `.parac/policies/TESTING.md`
   - Security → `.parac/policies/SECURITY.md`

3. **Documente les décisions importantes**
   - Architecture Decision Records → `.parac/roadmap/decisions.md`

### APRÈS chaque action significative:

```bash
# 1. Logger l'action
[TIMESTAMP] [AGENT] [ACTION] Description brève
→ Destination: .parac/memory/logs/agent_actions.log

# 2. Si décision importante
→ Ajoute dans .parac/roadmap/decisions.md

# 3. Si changement d'état du projet
→ Mise à jour .parac/memory/context/current_state.yaml

# 4. Si nouvelle connaissance
→ Ajoute dans .parac/memory/knowledge/

# 5. Si question en suspens
→ Ajoute dans .parac/memory/context/open_questions.md
```

---

## 📝 FORMAT DE LOG

**Format Standard:**
```
[YYYY-MM-DD HH:MM:SS] [Agent] [ACTION_TYPE] Description
```

**Types d'actions:**
- `IMPLEMENTATION` - Implémentation de code
- `DECISION` - Décision importante
- `REVIEW` - Revue de code
- `TEST` - Ajout/modification de tests
- `DOCUMENTATION` - Documentation
- `PLANNING` - Planification
- `REFACTORING` - Refactoring
- `BUGFIX` - Correction de bug
- `UPDATE` - Mise à jour fichiers .parac/

**Exemples:**
```
[2026-01-04 14:30:00] [CoderAgent] [IMPLEMENTATION] Added API-first fallback to workflow commands
[2026-01-04 15:00:00] [ArchitectAgent] [DECISION] Use hexagonal architecture for core modules
[2026-01-04 15:30:00] [ReviewerAgent] [REVIEW] Approved PR #42 with minor suggestions
[2026-01-04 16:00:00] [TesterAgent] [TEST] Added 15 unit tests for workflow execution
```

---

## 🎨 AGENTS DISPONIBLES

Consulte `.parac/agents/specs/` pour les spécifications complètes:

### Architect (`architect`)
**Rôle**: Design système, architecture, décisions techniques
**Quand**: Nouvelle architecture, refactoring majeur, décisions techniques

### Coder (`coder`)
**Rôle**: Implémentation de features, code production-quality
**Quand**: Nouvelle feature, bug fix, amélioration de code

### Reviewer (`reviewer`)
**Rôle**: Code review, assurance qualité, standards
**Quand**: Pull request, validation de code, contrôle qualité

### Tester (`tester`)
**Rôle**: Design et implémentation de tests, validation
**Quand**: Tests unitaires, tests d'intégration, validation

### PM (`pm`)
**Rôle**: Planification, coordination, roadmap
**Quand**: Planification de features, priorisation, tracking

### Documenter (`documenter`)
**Rôle**: Documentation technique, API reference, guides
**Quand**: Documentation de code, guides utilisateur, API docs

---

## 🔍 STRUCTURE DU .parac/

```
.parac/
├── GOVERNANCE.md              # ⭐ Règles du projet (LIRE EN PREMIER)
├── manifest.yaml              # Configuration workspace
├── project.yaml               # Métadonnées projet
├── STRUCTURE.md               # Documentation structure
├── USING_PARAC.md             # Guide d'utilisation (ce fichier)
│
├── agents/                    # Configuration agents
│   ├── manifest.yaml          # ⭐ Liste des agents (LIRE)
│   ├── specs/                 # Spécifications agents
│   └── skills/                # Bibliothèque de skills
│
├── memory/                    # 🧠 Mémoire du projet
│   ├── context/
│   │   ├── current_state.yaml # ⭐ État actuel (LIRE)
│   │   └── open_questions.md  # Questions en suspens
│   ├── knowledge/             # Connaissances accumulées
│   ├── logs/                  # 📋 Logs des actions (ÉCRIRE)
│   │   ├── agent_actions.log  # ⭐ Actions principales
│   │   └── decisions.log      # Décisions importantes
│   └── summaries/             # Résumés périodiques
│
├── roadmap/                   # 🗺️ Planification
│   ├── roadmap.yaml           # ⭐ Phases et milestones (LIRE)
│   └── decisions.md           # Architecture Decision Records
│
├── workflows/                 # Workflows automatisés
├── tools/                     # Outils personnalisés
├── adapters/                  # Adaptateurs externes
├── policies/                  # 📜 Politiques (CODE_STYLE, TESTING, etc.)
└── integrations/              # Intégrations IDE
```

**Légende:**
- ⭐ = Fichier critique à lire
- 🧠 = Mémoire du projet
- 📋 = Logging (écriture fréquente)
- 🗺️ = Planification
- 📜 = Standards et règles

---

## ✅ CHECKLIST RAPIDE

### Pour Commencer une Session

```
□ J'ai lu .parac/GOVERNANCE.md
□ J'ai lu .parac/memory/context/current_state.yaml
□ J'ai lu .parac/roadmap/roadmap.yaml
□ Je sais quel agent adopter
□ Je connais les standards du projet
```

### Pendant le Travail

```
□ Je suis le persona de l'agent approprié
□ Je respecte les standards de .parac/policies/
□ Je documente mes décisions importantes
□ Je pose des questions si quelque chose n'est pas clair
```

### Après Chaque Action

```
□ J'ai loggé l'action dans .parac/memory/logs/agent_actions.log
□ J'ai mis à jour .parac/ si nécessaire
□ J'ai documenté les décisions importantes
□ J'ai vérifié la cohérence
```

---

## 🎯 EXEMPLES CONCRETS

### Exemple 1: Demande "Ajoute une nouvelle feature"

```
1. Lire .parac/memory/context/current_state.yaml
   → Phase actuelle? Priorités?

2. Lire .parac/roadmap/roadmap.yaml
   → Cette feature est planifiée? Quelle priorité?

3. Adopter Coder persona
   → Lire .parac/agents/specs/coder.md

4. Vérifier standards
   → Lire .parac/policies/CODE_STYLE.md

5. Implémenter la feature
   → Suivre architecture et standards

6. Logger l'action
   → [2026-01-04 15:00:00] [CoderAgent] [IMPLEMENTATION] Added feature X

7. Mettre à jour l'état
   → .parac/memory/context/current_state.yaml
```

### Exemple 2: Demande "Review ce code"

```
1. Adopter Reviewer persona
   → Lire .parac/agents/specs/reviewer.md

2. Vérifier standards
   → Lire .parac/policies/CODE_STYLE.md
   → Lire .parac/policies/TESTING.md

3. Analyser le code
   → Comparer avec les standards

4. Fournir feedback
   → Suggestions constructives

5. Logger la review
   → [2026-01-04 15:30:00] [ReviewerAgent] [REVIEW] Reviewed PR #42
```

### Exemple 3: Demande "Planifie la prochaine phase"

```
1. Adopter PM persona
   → Lire .parac/agents/specs/pm.md

2. Analyser l'état actuel
   → Lire .parac/memory/context/current_state.yaml
   → Lire .parac/roadmap/roadmap.yaml

3. Consulter questions ouvertes
   → Lire .parac/memory/context/open_questions.md

4. Proposer planification
   → Basée sur roadmap et état actuel

5. Documenter
   → Mettre à jour .parac/roadmap/roadmap.yaml

6. Logger
   → [2026-01-04 16:00:00] [PMAgent] [PLANNING] Planned Phase 5 milestones
```

---

## 🚨 ERREURS COURANTES À ÉVITER

### ❌ Ne PAS Faire

1. **Ignorer le .parac/**
   - Ne jamais agir sans consulter le contexte

2. **Ne pas logger**
   - Toute action significative doit être loggée

3. **Inventer des règles**
   - Suivre uniquement les règles de .parac/GOVERNANCE.md

4. **État incohérent**
   - Toujours mettre à jour .parac/ après changements

5. **Mémoire privée**
   - Tout doit être dans .parac/, pas dans la mémoire de l'assistant

### ✅ À Faire

1. **Toujours consulter .parac/ en premier**
2. **Logger toutes les actions importantes**
3. **Suivre les standards du projet**
4. **Mettre à jour la mémoire**
5. **Documenter les décisions**

---

## 🔄 COMPATIBILITÉ IDE

**Ces instructions fonctionnent avec:**

- ✅ **Cursor** (.cursorrules)
- ✅ **Cline** (.clinerules)
- ✅ **Windsurf** (.windsurfrules)
- ✅ **Claude Code** (.claude/CLAUDE.md)
- ✅ **GitHub Copilot** (.github/copilot-instructions.md)
- ✅ **ChatGPT** (via contexte)
- ✅ **Claude** (via contexte)
- ✅ **Gemini** (via contexte)
- ✅ **Tout autre assistant IA**

**Le contenu est IDE-agnostique. Seul le format du fichier change.**

---

## 📚 DOCUMENTATION COMPLÈTE

Pour plus de détails, consulte:

- **`.parac/USING_PARAC.md`** - Guide complet (ce fichier)
- **`.parac/GOVERNANCE.md`** - Règles de gouvernance
- **`.parac/STRUCTURE.md`** - Structure détaillée
- **`.parac/MAINTENANCE.md`** - Guide de maintenance
- **`.parac/agents/SKILL_ASSIGNMENTS.md`** - Skills par agent

---

## 💡 LE MANTRA PARACLE

> **"Consulte .parac/, suis .parac/, logue dans .parac/"**

**Le `.parac/` n'est pas une option. C'est obligatoire.**

---

## ⚡ RACCOURCIS UTILES

```bash
# Voir l'état du projet
cat .parac/memory/context/current_state.yaml

# Voir le roadmap
cat .parac/roadmap/roadmap.yaml

# Voir les logs récents
tail -n 20 .parac/memory/logs/agent_actions.log

# Lister les agents
cat .parac/agents/manifest.yaml

# Voir les questions ouvertes
cat .parac/memory/context/open_questions.md

# Ajouter un log rapidement
echo "[$(date +"%Y-%m-%d %H:%M:%S")] [CoderAgent] [ACTION] Description" >> .parac/memory/logs/agent_actions.log
```

---

**🧠 Le `.parac/` est le cerveau de votre projet. Utilisez-le. ✨**
