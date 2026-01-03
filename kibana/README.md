# Kibana - IoT Smart Building Dashboard

## 🎯 Vue d'ensemble

Ce dossier contient les exports et templates pour Kibana, utilisé pour visualiser les données IoT du smart building.

## 📊 Dashboard Principal

**Accès direct**: http://localhost:5601/app/dashboards#/view/iot-smart-building-dashboard

### Visualisations incluses

1. **Température par zone (dernières 24h)** 📈
   - Type: Line chart
   - Données: Température moyenne par zone et par heure
   - Index: `logs-iot-sensors-*`
   - Filtre: `sensor_type:temperature`

2. **Heatmap des alertes** 🔥
   - Type: Heatmap
   - Données: Distribution des alertes par zone et heure
   - Index: `logs-iot-alerts-*`
   - Affiche les zones les plus problématiques

3. **KPI - Métriques** 📊
   - Type: Metric
   - Données: Total logs + Capteurs actifs (cardinality)
   - Index: `logs-iot-sensors-*`
   - Rafraîchissement: 1 minute

## 🚀 Installation / Configuration

### Méthode automatique (recommandé)

```bash
# Exécuter le script de configuration
python3 scripts/setup_kibana.py
```

Ce script crée automatiquement :
- ✅ Index patterns (`logs-iot-sensors-*`, `logs-iot-alerts-*`)
- ✅ 3 visualisations
- ✅ 1 dashboard complet

### Méthode manuelle

1. **Créer les index patterns**
   - Aller dans Stack Management > Index Patterns
   - Créer `logs-iot-sensors-*` avec `@timestamp`
   - Créer `logs-iot-alerts-*` avec `@timestamp`

2. **Importer le dashboard**
   ```bash
   # Via l'API
   curl -X POST "http://localhost:5601/api/saved_objects/_import" \
     -H "kbn-xsrf: true" \
     --form file=@kibana/exports/iot-dashboard-export.ndjson
   ```

   Ou via l'interface :
   - Stack Management > Saved Objects
   - Import > Sélectionner `iot-dashboard-export.ndjson`

## 📁 Fichiers exportés

### `exports/iot-dashboard-export.ndjson`

Export complet du dashboard au format NDJSON incluant :
- Dashboard principal
- Toutes les visualisations
- Index patterns
- Toutes les références

**Utilisation** :
- Sauvegarde / versionnement
- Restauration après réinitialisation
- Déploiement sur un autre environnement

## 🔧 Personnalisation

### Modifier les visualisations

1. Ouvrir Kibana: http://localhost:5601
2. Aller dans Dashboard > "IoT Smart Building - Dashboard Principal"
3. Cliquer sur "Edit" en haut à droite
4. Modifier les panneaux existants ou ajouter de nouveaux
5. Sauvegarder

### Créer de nouvelles visualisations

**Exemples de requêtes utiles** :

```lucene
# Anomalies de température
sensor_type:temperature AND tags:anomaly

# Alertes critiques zone A
zone:A AND severity:critical

# Humidité warnings
sensor_type:humidity AND status:warning

# Logs du dernier jour
@timestamp:[now-1d TO now]

# Capteur spécifique
sensor_id:2001
```

### Agrégations utiles

- **Count** : Nombre de logs
- **Cardinality** : Nombre de capteurs uniques
- **Avg/Min/Max** : Statistiques sur `value`
- **Terms** : Grouper par `zone`, `sensor_type`, `status`
- **Date Histogram** : Timeline avec interval (1h, 1d)

## 📈 Métriques disponibles

### Sensors (`logs-iot-sensors-*`)

| Champ | Type | Description |
|-------|------|-------------|
| `@timestamp` | date | Timestamp d'indexation |
| `timestamp` | date | Timestamp original du log |
| `zone` | keyword | Zone du bâtiment (A-I) |
| `sensor_type` | keyword | Type de capteur (temperature, humidity, co2, luminosity) |
| `sensor_id` | keyword | ID unique du capteur |
| `value` | float | Valeur mesurée |
| `unit` | keyword | Unité de mesure (°C, %, ppm, lux) |
| `status` | keyword | Statut (ok, warning, error) |
| `floor` | keyword | Étage (1, 2, 3) |
| `building` | keyword | Nom du bâtiment |
| `tags` | keyword | Tags (anomaly, temperature_alert, humidity_alert) |

### Alerts (`logs-iot-alerts-*`)

| Champ | Type | Description |
|-------|------|-------------|
| `@timestamp` | date | Timestamp d'indexation |
| `timestamp` | date | Timestamp original de l'alerte |
| `zone` | keyword | Zone concernée |
| `sensor_id` | keyword | ID du capteur |
| `message` | text | Description de l'alerte |
| `severity` | keyword | Niveau (low, medium, high, critical) |
| `event_type` | keyword | Type d'événement |
| `value` | float | Valeur associée |
| `floor` | keyword | Étage |

## 🔄 Rafraîchissement des données

Le dashboard est configuré pour se rafraîchir automatiquement **toutes les 1 minute**.

Pour modifier :
1. Ouvrir le dashboard
2. Cliquer sur l'icône ⏰ en haut à droite
3. Ajuster l'intervalle de rafraîchissement

## 🎨 Thèmes et couleurs

### Palette de couleurs utilisée

- **Température** : Gradient bleu → rouge (froid → chaud)
- **Alertes** : Rouge (heatmap "Reds")
- **Status** :
  - 🟢 OK : Vert
  - 🟡 Warning : Jaune
  - 🔴 Error : Rouge

## 📊 Bonnes pratiques

1. **Filtrage temporel** : Utiliser toujours un filtre temporel pour les performances
2. **Index patterns avec wildcard** : Utiliser `*` pour couvrir tous les indices
3. **Refresh interval** : Ajuster selon les besoins (désactiver pour économiser les ressources)
4. **Sauvegarde régulière** : Exporter le dashboard après modifications importantes

## 🐛 Dépannage

### Dashboard vide / Pas de données

```bash
# Vérifier les indices
curl "http://localhost:9200/_cat/indices/logs-iot-*?v"

# Compter les documents
curl "http://localhost:9200/logs-iot-*/_count"

# Vérifier les index patterns dans Kibana
# Stack Management > Index Patterns
```

### Visualisations cassées

1. Vérifier que les index patterns existent
2. Vérifier les champs utilisés dans les agrégations
3. Re-créer les visualisations avec le script :
   ```bash
   python3 scripts/setup_kibana.py
   ```

### Performances lentes

- Réduire la plage temporelle (ex: 24h au lieu de 7j)
- Désactiver le refresh automatique
- Augmenter les ressources Elasticsearch (docker-compose.yml)

## 📚 Ressources

- [Kibana Documentation](https://www.elastic.co/guide/en/kibana/current/index.html)
- [Visualize Guide](https://www.elastic.co/guide/en/kibana/current/dashboard.html)
- [Lucene Query Syntax](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-query-string-query.html#query-string-syntax)

## 🔗 Liens rapides

- **Kibana Home** : http://localhost:5601
- **Dashboard** : http://localhost:5601/app/dashboards#/view/iot-smart-building-dashboard
- **Discover** : http://localhost:5601/app/discover
- **Visualize** : http://localhost:5601/app/visualize
- **Dev Tools** : http://localhost:5601/app/dev_tools#/console
