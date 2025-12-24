# Logs Directory

Ce dossier contient les logs d'exécution du framework Paracle.

## Structure

- `paracle.log` - Log principal du framework
- `agents/` - Logs spécifiques aux agents
- `workflows/` - Logs des workflows exécutés
- `errors/` - Logs d'erreurs et exceptions

## Configuration

Les logs sont configurés via `project.yaml` avec les paramètres suivants:

```yaml
logging:
  level: INFO
  format: json
  rotation: daily
  retention_days: 30
```

## Niveaux de log

- **DEBUG**: Informations détaillées pour le débogage
- **INFO**: Confirmation que les choses fonctionnent comme prévu
- **WARNING**: Indication que quelque chose d'inattendu s'est produit
- **ERROR**: Problème plus sérieux, le logiciel n'a pas pu effectuer une fonction
- **CRITICAL**: Erreur grave, le programme pourrait ne pas pouvoir continuer

## Rotation

Les logs sont automatiquement archivés quotidiennement et conservés pendant 30 jours par défaut.
