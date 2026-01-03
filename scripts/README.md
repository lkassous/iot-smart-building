# Scripts Utilitaires

Ce dossier contient les scripts utilitaires pour le projet IoT Smart Building.

## Scripts disponibles

### `generate_test_data.py`

Génère des données de test pour l'application :
- **Logs de capteurs** (CSV) : température, humidité, luminosité, CO2
- **Alertes** (JSON) : anomalies, pannes, alertes critiques

#### Utilisation

```bash
cd scripts
python generate_test_data.py
```

#### Configuration

Le script génère par défaut :
- **10,000 logs de capteurs** sur les 7 derniers jours
- **1,000 alertes** de différents niveaux de sévérité
- **Échantillons** pour tests rapides (100 logs + 20 alertes)

Les fichiers sont créés dans :
- `data/uploads/` : surveillé par Logstash (ingestion automatique)
- `data/test-data/` : sauvegarde pour versioning

#### Données générées

**Capteurs CSV** :
- 9 zones (A-I, 3 étages)
- 4 types de capteurs par zone
- ~10% de valeurs anormales (déclenchent alertes Logstash)

**Alertes JSON** :
- Sévérités : low (40%), medium (35%), high (20%), critical (5%)
- 8 types d'alertes différents
- Horodatage réaliste sur 7 jours

## Ajout de nouveaux scripts

Pour ajouter un nouveau script utilitaire :
1. Créer le fichier Python dans ce dossier
2. Documenter son utilisation dans ce README
3. Ajouter les dépendances dans `webapp/requirements.txt` si nécessaire
