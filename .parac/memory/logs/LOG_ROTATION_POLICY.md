# Agent Actions Log - Rotation Policy

## 📊 État Actuel

**Lignes actuelles**: ~1535 lignes
**Taille du fichier**: Variable (dépend de la verbosité)
**Rotation**: ❌ Non implémentée

## 🎯 Recommandations

### **Limite Maximale Recommandée**

| Métrique             | Limite            | Raison                                    |
| -------------------- | ----------------- | ----------------------------------------- |
| **Nombre de lignes** | **10,000 lignes** | Équilibre entre historique et performance |
| **Taille fichier**   | **1 MB max**      | Lecture rapide, git-friendly              |
| **Période**          | **1 an**          | Archive annuelle pour audit               |

### **Stratégie de Rotation**

```
agent_actions.log           ← Actif (0-10,000 lignes)
agent_actions.log.1         ← Archive récente
agent_actions.log.2         ← Archive -1 mois
agent_actions.log.3         ← Archive -2 mois
archives/2025/
  ├── agent_actions.2025-01.log
  ├── agent_actions.2025-02.log
  └── agent_actions.2025-12.log
```

## 🔄 Implémentation

### **Option 1: Rotation par Nombre de Lignes** (Recommandé)

```python
# Dans agent-logger.py
MAX_LOG_LINES = 10_000
ARCHIVE_DIR = parac_dir / "memory" / "logs" / "archives"

def _rotate_if_needed(self):
    """Rotate log if exceeds MAX_LOG_LINES"""
    if not self.actions_log.exists():
        return

    with open(self.actions_log, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if len(lines) >= MAX_LOG_LINES:
        # Create archive directory
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

        # Archive old logs
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        archive_path = ARCHIVE_DIR / f"agent_actions.{timestamp}.log"

        with open(archive_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        # Keep only recent N lines
        recent_lines = lines[-1000:]  # Keep last 1000 for continuity
        with open(self.actions_log, 'w', encoding='utf-8') as f:
            f.writelines(recent_lines)

        print(f"✓ Log rotated: {len(lines)} → {len(recent_lines)} lines")
        print(f"  Archived to: {archive_path}")
```

### **Option 2: Rotation par Taille**

```python
MAX_LOG_SIZE_MB = 1

def _rotate_if_needed(self):
    if not self.actions_log.exists():
        return

    size_mb = self.actions_log.stat().st_size / (1024 * 1024)
    if size_mb >= MAX_LOG_SIZE_MB:
        # Rotate logic...
```

### **Option 3: Rotation Périodique (Mensuelle)**

```python
def _rotate_if_month_changed(self):
    """Rotate at the beginning of each month"""
    if not self.actions_log.exists():
        return

    # Check if current month differs from log's last modified month
    log_mtime = datetime.fromtimestamp(self.actions_log.stat().st_mtime)
    current_month = datetime.now().strftime("%Y-%m")
    log_month = log_mtime.strftime("%Y-%m")

    if current_month != log_month:
        # Archive for previous month
        archive_name = f"agent_actions.{log_month}.log"
        # Rotate logic...
```

## 📋 Comparaison des Options

| Option         | Avantages                      | Inconvénients            | Recommandé   |
| -------------- | ------------------------------ | ------------------------ | ------------ |
| **Par Lignes** | Prédictible, contrôle précis   | Besoin de compter        | ⭐ OUI        |
| **Par Taille** | Performance (stat() rapide)    | Variable selon verbosité | 🔶 Acceptable |
| **Périodique** | Organisation temporelle claire | Peut créer gros fichiers | 🔷 Complément |

**Recommandation finale**: **Par Lignes (10,000) + Archives mensuelles**

## 🛠️ Script de Maintenance

### **Nettoyage des Archives Anciennes**

```python
# .parac/tools/hooks/cleanup-logs.py
from pathlib import Path
from datetime import datetime, timedelta

ARCHIVE_DIR = Path(".parac/memory/logs/archives")
MAX_ARCHIVE_AGE_DAYS = 365  # 1 an

def cleanup_old_archives():
    """Remove archives older than MAX_ARCHIVE_AGE_DAYS"""
    if not ARCHIVE_DIR.exists():
        return

    cutoff_date = datetime.now() - timedelta(days=MAX_ARCHIVE_AGE_DAYS)

    for archive in ARCHIVE_DIR.glob("*.log"):
        mtime = datetime.fromtimestamp(archive.stat().st_mtime)
        if mtime < cutoff_date:
            archive.unlink()
            print(f"✓ Deleted old archive: {archive.name}")

if __name__ == "__main__":
    cleanup_old_archives()
```

### **Analyse des Logs**

```python
# .parac/tools/hooks/analyze-logs.py
def analyze_log_size():
    """Analyze current log size and recommend rotation"""
    log_path = Path(".parac/memory/logs/agent_actions.log")

    if not log_path.exists():
        print("No log file found")
        return

    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    size_kb = log_path.stat().st_size / 1024
    size_mb = size_kb / 1024

    print(f"📊 Log Statistics:")
    print(f"  Lines: {len(lines):,}")
    print(f"  Size: {size_mb:.2f} MB ({size_kb:.2f} KB)")

    if len(lines) > 10_000:
        print(f"  ⚠️  Rotation recommended (> 10,000 lines)")
    elif size_mb > 1:
        print(f"  ⚠️  Rotation recommended (> 1 MB)")
    else:
        print(f"  ✅ Size OK")

if __name__ == "__main__":
    analyze_log_size()
```

## 🎯 Actions Recommandées

### **Phase 1: Immédiat (Aujourd'hui)**

1. **Archiver le log actuel** (1535 lignes → baseline)
   ```bash
   mkdir -p .parac/memory/logs/archives
   cp .parac/memory/logs/agent_actions.log \
      .parac/memory/logs/archives/agent_actions.2026-01-10_baseline.log
   ```

2. **Documenter la politique** dans `.parac/GOVERNANCE.md`

### **Phase 2: Court terme (Cette semaine)**

1. **Implémenter rotation dans agent-logger.py**
   - Limite: 10,000 lignes
   - Archive automatique
   - Garde 1,000 dernières lignes

2. **Créer script analyze-logs.py**
   - Monitoring de la taille
   - Alertes si > limite

### **Phase 3: Moyen terme (Ce mois)**

1. **Créer cleanup-logs.py**
   - Nettoyage automatique archives > 1 an

2. **Ajouter à git hooks**
   - Pre-commit: Vérifier taille log
   - Post-merge: Analyser log

### **Phase 4: Long terme**

1. **Dashboard de logs** (optionnel)
   - Visualisation actions par agent
   - Métriques temporelles
   - Export en CSV/JSON

## 📊 Monitoring

### **Métriques à Suivre**

| Métrique        | Cible          | Alerte si         |
| --------------- | -------------- | ----------------- |
| Lignes totales  | < 10,000       | > 10,000          |
| Taille fichier  | < 1 MB         | > 1 MB            |
| Croissance/jour | ~10-50 lignes  | > 100 lignes/jour |
| Archives        | 12 fichiers/an | > 20 fichiers     |

### **Commandes de Monitoring**

```powershell
# Windows PowerShell
Get-Content .\.parac\memory\logs\agent_actions.log | Measure-Object -Line

# Taille du fichier
(Get-Item .\.parac\memory\logs\agent_actions.log).Length / 1MB

# Nombre d'archives
(Get-ChildItem .\.parac\memory\logs\archives\).Count
```

```bash
# Linux/Mac
wc -l .parac/memory/logs/agent_actions.log
du -h .parac/memory/logs/agent_actions.log
ls -1 .parac/memory/logs/archives/ | wc -l
```

## 🔗 Références

- **Rotation des logs**: [Linux logrotate](https://linux.die.net/man/8/logrotate)
- **Best practices**: [The Twelve-Factor App - Logs](https://12factor.net/logs)
- **Python logging**: [RotatingFileHandler](https://docs.python.org/3/library/logging.handlers.html#rotatingfilehandler)

## 📝 Notes

- **Git**: Archives sont gitignorées (`.parac/memory/logs/archives/` dans `.gitignore`)
- **Backup**: Archives importantes peuvent être sauvegardées séparément
- **Performance**: Lecture de 10,000 lignes = ~100ms (acceptable)

---

**Recommandation Finale**: **10,000 lignes max** avec rotation automatique et archives mensuelles.

**Prochaine Action**: Implémenter la rotation dans `agent-logger.py` (voir Option 1 ci-dessus).

**État Actuel (2026-01-10)**: 1,535 lignes ✅ OK (< 10,000)
