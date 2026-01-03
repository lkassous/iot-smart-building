# Analyse Complète du Cahier des Charges - IoT Smart Building

## 📋 Vue d'ensemble du projet

### Contexte général
Il s'agit d'un **projet pédagogique de plateforme de monitoring et d'analyse de logs** dans le cadre d'un système IoT Smart Building. L'objectif est de concevoir une solution complète de collecte, indexation, recherche et visualisation de données de capteurs en temps réel.

### Scénario choisi : Smart Building
Le projet se concentre sur la gestion des systèmes de monitoring d'un **bâtiment intelligent** équipé de centaines de capteurs.

## 📊 Types de logs à traiter

### 1. Logs de capteurs
- **Température** (°C)
- **Humidité** (%)
- **Luminosité** (lux)
- **CO2** (ppm)
- **Format attendu**: CSV avec colonnes `timestamp,zone,sensor_type,sensor_id,value,unit,status`

### 2. Logs d'alertes
- Anomalies détectées (seuils dépassés)
- Événements système
- **Format attendu**: JSON avec champs normalisés

### 3. Logs de maintenance
- Usure des équipements
- Pannes prédites
- Historique interventions

### 4. Logs de consommation énergétique
- Électricité (kWh)
- Eau (m³)
- Chauffage (kWh)

### 5. Logs d'occupation
- Présence dans les salles
- Taux d'utilisation des espaces
- Patterns d'occupation

## 🎯 KPI (Indicateurs clés) à implémenter

### KPI obligatoires
1. **Température moyenne** par zone et par heure
2. **Nombre d'alertes critiques** par jour
3. **Consommation énergétique** en temps réel
4. **Taux d'occupation** des espaces
5. **Prévisions de maintenance** (Machine Learning optionnel)

### Cas d'usage prioritaires
- ⚠️ **Alerte température**: Déclencher si > 30°C ou < 15°C (déjà implémenté dans `csv-pipeline.conf`)
- ⚡ **Optimisation énergétique**: Analyser les patterns de consommation
- 🔧 **Maintenance prédictive**: Prédire les pannes via analyse historique

## 🏗️ Architecture technique imposée

### Stack ELK (Core - OBLIGATOIRE)
- **Elasticsearch 8.x**: ✅ Actuellement 8.11.0
- **Logstash 8.x**: ✅ Actuellement 8.11.0
- **Kibana 8.x**: ✅ Actuellement 8.11.0

### Conteneurisation (OBLIGATOIRE)
- **Docker 24.x**: ✅ Configuré
- **Docker Compose 2.x**: ✅ `docker-compose.yml` présent

### Framework Web (Choix Flask OU Django)
**Choix recommandé**: **Flask 3.x** (plus léger, adapté au projet)
- ❌ **À CRÉER**: `webapp/app.py` (point d'entrée principal)
- ❌ **À CRÉER**: `webapp/requirements.txt`
- ❌ **À CRÉER**: `webapp/Dockerfile`

Dépendances Flask nécessaires:
```txt
Flask==3.0.0
flask-restful==0.3.10
flask-login==0.6.3 (si authentification)
gunicorn==21.2.0
python-dotenv==1.0.0
elasticsearch==8.11.0
pymongo==4.6.1
redis==5.0.1
```

### Bases NoSQL (OBLIGATOIRES)
- **MongoDB 7.x**: ✅ Configuré (v7.0)
  - Usage: Métadonnées fichiers, configs users, historique recherches
- **Redis 7.x**: ✅ Configuré (v7.2-alpine)
  - Usage: Cache requêtes ES, sessions, rate limiting

### Frontend (Recommandations)
- **HTML5 + CSS3 + JavaScript**: Base
- **Bootstrap 5 OU Tailwind CSS**: Framework CSS responsive
- **Chart.js OU Plotly.js**: Graphiques personnalisés
- **DataTables.js**: Tableaux interactifs
- **FullCalendar.js**: Sélecteurs dates (optionnel)

## 📦 Fonctionnalités par niveau

### ⭐ Niveau OBLIGATOIRE (12/20)

#### Module 1: Gestion des fichiers de logs
**État actuel**: ❌ Non implémenté

**À développer**:
- [ ] Interface web upload (drag & drop)
- [ ] Validation fichiers (CSV/JSON/TXT, max 100MB)
- [ ] Prévisualisation 10 premières lignes
- [ ] Injection automatique dans Logstash
- [ ] Liste fichiers uploadés (tableau avec tri/pagination)
- [ ] Stockage métadonnées dans MongoDB

**Schéma MongoDB pour métadonnées**:
```javascript
{
  _id: ObjectId(),
  filename: "sensors_2025_10_28.csv",
  original_name: "sensors_2025_10_28.csv",
  upload_date: ISODate("2025-10-28T10:30:00Z"),
  file_size: 2048576, // bytes
  file_type: "csv", // csv, json, txt
  status: "processed", // uploaded, processing, processed, error
  num_logs: 15420,
  user_id: "admin", // si auth
  logstash_pipeline: "csv-pipeline",
  elasticsearch_index: "logs-iot-sensors-2025.10.28",
  processing_time: 3.5, // seconds
  errors: []
}
```

#### Module 2: Configuration ELK
**État actuel**: ✅ Partiellement fait

**Déjà configuré**:
- ✅ 2 pipelines Logstash (CSV + JSON)
- ✅ Filtres appropriés (csv, json, date, mutate)
- ✅ Anomaly detection (température/humidité)
- ✅ Output Elasticsearch avec gestion erreurs
- ✅ Enrichissement données (tags, floor mapping)

**À faire**:
- [ ] ❌ Index templates Elasticsearch dans `elasticsearch/mappings/`
- [ ] ❌ 3+ visualisations Kibana spécifiques IoT
- [ ] ❌ Dashboard Kibana exporté dans `kibana/exports/`

**Visualisations Kibana requises**:
1. **Line chart**: Évolution température moyenne par zone (dernières 24h)
2. **Heat map**: Nombre d'alertes par zone et par heure
3. **Gauge**: Consommation énergétique actuelle vs objectif

#### Module 3: Interface Web de Base
**État actuel**: ❌ Non implémenté (répertoires vides)

**Pages à créer**:
1. **Page d'accueil** (`templates/index.html`)
   - 4 KPI en temps réel: Total logs, Logs aujourd'hui, Erreurs, Fichiers uploadés
   - Graphiques Chart.js (tendances)
   - Design responsive

2. **Page upload** (`templates/upload.html`)
   - Formulaire drag & drop
   - Validation client (taille, format)
   - Barre progression
   - Liste uploads récents

3. **Page recherche** (`templates/search.html`)
   - Barre texte libre
   - Filtres: Niveau, Zone, Sensor_type, Date range
   - Date picker calendrier
   - Sauvegarde recherches dans MongoDB

4. **Page résultats** (`templates/results.html`)
   - Tableau DataTables.js (50 logs/page)
   - Tri par colonnes
   - Modal détails log
   - Export CSV

**Routes Flask à créer** (`webapp/routes/`):
```python
# routes/main.py
GET  /                    # Dashboard principal
GET  /upload              # Page upload
POST /upload              # Traitement upload
GET  /search              # Page recherche
GET  /results             # Résultats recherche
GET  /api/v1/stats        # Stats temps réel (AJAX)
```

#### Module 4: Intégration MongoDB
**État actuel**: ✅ MongoDB configuré, ❌ Code non écrit

**Schémas MongoDB à créer**:
1. **Collection `uploaded_files`** (métadonnées)
2. **Collection `search_history`**:
```javascript
{
  _id: ObjectId(),
  user_id: "admin",
  query: "level:ERROR AND zone:A",
  filters: {
    level: "ERROR",
    zone: "A",
    date_from: ISODate("2025-10-28T00:00:00Z"),
    date_to: ISODate("2025-10-28T23:59:59Z")
  },
  num_results: 247,
  execution_time: 0.152, // seconds
  timestamp: ISODate("2025-10-28T14:30:00Z")
}
```

3. **Collection `user_configs`** (pour futures fonctionnalités)

#### Module 5: Déploiement Docker
**État actuel**: ✅ Presque complet

**Déjà fait**:
- ✅ `docker-compose.yml` complet avec 6 services
- ✅ Health checks (ES, Kibana, MongoDB, Redis)
- ✅ Réseau `iot-network`
- ✅ Volumes persistants
- ✅ Variables environnement
- ✅ `.env.example`

**À faire**:
- [ ] ❌ `webapp/Dockerfile` à créer
- [ ] ❌ `webapp/requirements.txt` à créer
- [ ] ❌ Documentation déploiement complète dans README
- [ ] ❌ Script génération données test

**Dockerfile Flask recommandé**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code application
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Exposition port
EXPOSE 8000

# Démarrage
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "app:app"]
```

### ⭐⭐ Niveau INTERMÉDIAIRE (+4 points → 16/20)

**Choisir 3 modules parmi**:

#### Option A: Authentification + Rôles
- Flask-Login pour sessions
- Rôles: Admin, User, Viewer
- MongoDB pour stockage users
- Protection routes avec decorators

#### Option B: Cache Redis avancé
- ✅ Redis déjà configuré
- Cache résultats recherches Elasticsearch (TTL 5min)
- Cache stats dashboard (TTL 1min)
- Rate limiting API (100 req/min par IP)

#### Option C: API RESTful + Documentation
- API REST complète avec Flask-RESTful
- Swagger/OpenAPI documentation
- Endpoints CRUD complets
- Versioning API (v1, v2)

#### Option D: Dashboards personnalisés
- Sauvegarde layouts dashboards dans MongoDB
- Widgets drag & drop
- Export/import configurations

#### Option E: Export avancé
- Export CSV, JSON, PDF
- Génération rapports automatiques
- Templates rapports personnalisables
- Envoi email rapports

### ⭐⭐⭐ Niveau AVANCÉ (+4 points → 20/20)

**Choisir 2 modules parmi**:

#### Module G: Système d'Alerting Intelligent
**Pertinent pour IoT Smart Building**

**Règles d'alertes à implémenter**:
```python
# Exemples règles alerting
{
  "name": "Température critique Zone A",
  "condition": {
    "field": "value",
    "operator": ">",
    "threshold": 30,
    "window": "5m"
  },
  "filters": {
    "zone": "A",
    "sensor_type": "temperature"
  },
  "severity": "critical",
  "notifications": ["email", "slack"]
}
```

**Composants**:
- Worker Python (Celery ou threading)
- Vérification périodique (cron-like)
- Multi-canal: Email (SMTP), Webhook (Slack/Discord)
- Dashboard alertes actives
- Escalation automatique

#### Module H: Analyse Temps Réel
**Très pertinent pour monitoring IoT**

**Technologies**:
- WebSocket (Flask-SocketIO)
- Server-Sent Events (SSE)
- Streaming Logstash (TCP/UDP input)
- Live tail des logs
- Graphiques animés Chart.js

**Use case IoT**: 
- Dashboard temps réel température toutes les 5 secondes
- Alertes visuelles instant si anomalie

#### Module I: Machine Learning
**Excellent pour prédiction maintenance**

**Fonctionnalités**:
- Elasticsearch ML jobs (anomaly detection)
- Détection patterns inhabituels (température, consommation)
- Prédiction pannes équipements
- Auto-tagging logs par catégorie
- Dashboard anomalies avec scores

**Modèles possibles**:
- Régression linéaire: Prédiction consommation énergétique
- Classification: Type d'alerte automatique
- Clustering: Groupement zones similaires
- Time series: Prédiction température future

#### Module J: Multi-tenancy
**Moins prioritaire pour ce projet**

#### Module K: CI/CD et Tests
**Recommandé pour qualité projet**

**Pipeline GitHub Actions**:
```yaml
# .github/workflows/ci.yml
- Linting (flake8, black)
- Tests unitaires (pytest, coverage >70%)
- Tests intégration (Docker Compose)
- Build Docker image
- Push registry
```

**Tests à écrire**:
- `tests/test_upload.py`: Validation fichiers
- `tests/test_elasticsearch.py`: Requêtes ES
- `tests/test_mongodb.py`: CRUD métadonnées
- `tests/test_api.py`: Endpoints Flask

#### Module L: Observabilité Prometheus/Grafana
**Très professionnel**

**Métriques business IoT**:
- Nombre capteurs actifs
- Alertes/heure par zone
- Latence ingestion Logstash
- Taux erreurs parsing

## 📅 Planning de réalisation suggéré

### Phase 1: Analyse & Conception (Déjà partiellement fait)
**Durée**: 2-3 jours

**Livrables attendus**:
- [ ] Document analyse fonctionnelle (5-8 pages)
  - Contexte IoT Smart Building
  - Diagramme cas d'utilisation UML
  - 10 user stories priorisées
  - Règles métier (seuils alertes)

- [ ] Architecture technique (8-12 pages)
  - Schéma C4 Model (contexte + conteneurs)
  - Diagramme déploiement Docker (déjà fait ✅)
  - 2-3 diagrammes séquence (upload, recherche, alerte)
  - Mapping Elasticsearch détaillé
  - Schémas MongoDB

- [ ] Maquettes UI/UX
  - Wireframes 5 pages (Figma/Draw.io)
  - Design system (couleurs, typo)
  - User journey map

**État actuel**: ✅ Architecture Docker faite, ❌ Documentation à rédiger

### Phase 2: Setup Infrastructure (Fait ✅)
**Durée**: 1-2 jours

**Checklist**:
- ✅ Repository Git créé
- ✅ `docker-compose.yml` complet
- ✅ Elasticsearch accessible (9200)
- ✅ Kibana accessible (5601)
- ✅ Logstash pipelines (CSV + JSON)
- ✅ MongoDB configuré (27017)
- ✅ Redis configuré (6379)
- ❌ Webapp conteneurisée
- ❌ Script génération données test

**Prochaines étapes**:
1. Créer `webapp/Dockerfile`
2. Créer `webapp/requirements.txt`
3. Créer `webapp/app.py` minimal
4. Tester `docker-compose up -d`
5. Générer données test CSV/JSON

### Phase 3: Backend Core (URGENT)
**Durée**: 4-5 jours

**Sprint 1 - Structure Flask** (1 jour):
```
webapp/
├── app.py                 # Point d'entrée Flask
├── config.py             # Configuration (env vars)
├── requirements.txt      # Dépendances
├── Dockerfile           # Conteneurisation
├── models/
│   ├── __init__.py
│   ├── file_metadata.py # Modèle MongoDB fichiers
│   └── search_history.py # Modèle MongoDB recherches
├── routes/
│   ├── __init__.py
│   ├── main.py          # Routes pages (GET /)
│   ├── upload.py        # Routes upload
│   ├── search.py        # Routes recherche
│   └── api.py           # API REST
├── utils/
│   ├── __init__.py
│   ├── elasticsearch.py # Client ES
│   ├── mongodb.py       # Client MongoDB
│   ├── redis_client.py  # Client Redis
│   └── validators.py    # Validation fichiers
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── main.js
│   │   ├── upload.js
│   │   └── search.js
│   └── img/
└── templates/
    ├── base.html         # Template de base
    ├── index.html        # Dashboard
    ├── upload.html       # Page upload
    ├── search.html       # Page recherche
    └── results.html      # Page résultats
```

**Sprint 2 - Module Upload** (2 jours):
- Route POST `/upload`
- Validation fichiers (mimetype, taille)
- Sauvegarde dans `data/uploads/`
- Métadonnées MongoDB
- Feedback utilisateur

**Sprint 3 - Module Recherche** (2 jours):
- Construction Query DSL Elasticsearch
- Pagination résultats
- Historique MongoDB
- API `/api/v1/search`

### Phase 4: Frontend & Visualisation (3-4 jours)

**Sprint 1 - Pages HTML** (2 jours):
- `base.html` avec Bootstrap 5
- Dashboard avec 4 KPI cards
- Page upload drag & drop
- Page recherche avec filtres

**Sprint 2 - JavaScript & AJAX** (1 jour):
- Appels API fetch()
- Chart.js graphiques
- DataTables.js résultats
- Date picker

**Sprint 3 - Kibana** (1 jour):
- 3 visualisations IoT
- Dashboard exporté
- Intégration iframe dans webapp

### Phase 5: Fonctionnalités Avancées (3-5 jours)

**Stratégie recommandée pour 16/20**:
1. **Cache Redis** (1 jour) - Améliore perfs
2. **API REST + Swagger** (2 jours) - Valorise backend
3. **Authentification basique** (2 jours) - Protection routes

**Stratégie ambitieuse pour 20/20**:
1. Modules intermédiaires ci-dessus (3-4 jours)
2. **Alerting intelligent** (2 jours) - Pertinent IoT
3. **ML anomaly detection** (2 jours) - Très valorisant

### Phase 6: Tests & Documentation (2-3 jours)

**Tests**:
- [ ] Tests unitaires pytest (coverage >70%)
- [ ] Tests intégration (upload → ES)
- [ ] Tests UI (navigateurs multiples)
- [ ] Tests responsive

**Documentation**:
- [ ] README.md complet avec screenshots
- [ ] PDF technique (15-25 pages)
- [ ] Slides présentation (15-20 slides)
- [ ] Vidéo démo (5-10 min)

## 🎯 Recommandations stratégiques

### Pour viser 16/20 (Réaliste)
**Temps estimé**: 15-20 jours

**Focus**:
1. ✅ Tous modules obligatoires (solide)
2. ✅ 3 modules intermédiaires bien finis
3. ✅ Documentation complète
4. ✅ Tests de base

**Modules intermédiaires conseillés**:
- Cache Redis (impact perfs visible)
- API REST + Swagger (professionnel)
- Dashboards personnalisés (différenciant)

### Pour viser 20/20 (Ambitieux)
**Temps estimé**: 25-30 jours

**Focus**:
1. ✅ Tous modules obligatoires (parfait)
2. ✅ 3 modules intermédiaires excellents
3. ✅ 2 modules avancés fonctionnels
4. ✅ Tests complets (>80% coverage)
5. ✅ CI/CD GitHub Actions
6. ✅ Documentation exemplaire

**Modules avancés conseillés IoT**:
- **Alerting intelligent** (très pertinent Smart Building)
- **Temps réel WebSocket** (dashboard live capteurs)

OU

- **Machine Learning** (prédiction pannes/conso)
- **CI/CD + Tests** (qualité logicielle)

## ⚠️ Points critiques identifiés

### Urgent (Bloquants)
1. ❌ **Pas de webapp Flask** → Créer structure complète
2. ❌ **Pas de Dockerfile webapp** → Conteneurisation impossible
3. ❌ **Pas de données test** → Impossible de tester
4. ❌ **Pas de visualisations Kibana** → Module obligatoire

### Important (Impact note)
5. ❌ **Pas de templates Elasticsearch** → Mapping non optimisé
6. ❌ **Pas de tests unitaires** → Qualité non prouvée
7. ❌ **Documentation minimale** → Livrables incomplets

### Améliorations (Bonus)
8. ⚠️ **Security disabled** → OK dev, risque en prod
9. ⚠️ **Sincedb `/dev/null`** → Retraitement systématique
10. ⚠️ **Pas de monitoring** → Observabilité limitée

## 📚 Ressources et références

### Documentation officielle
- Elasticsearch: https://www.elastic.co/guide/en/elasticsearch/reference/8.11/
- Logstash: https://www.elastic.co/guide/en/logstash/8.11/
- Kibana: https://www.elastic.co/guide/en/kibana/8.11/
- Flask: https://flask.palletsprojects.com/
- MongoDB: https://www.mongodb.com/docs/
- Redis: https://redis.io/docs/

### Exemples de requêtes Elasticsearch pour IoT

```json
# Température moyenne par zone (dernières 24h)
GET /logs-iot-sensors-*/_search
{
  "size": 0,
  "query": {
    "bool": {
      "must": [
        { "term": { "sensor_type": "temperature" } },
        { "range": { "@timestamp": { "gte": "now-24h" } } }
      ]
    }
  },
  "aggs": {
    "by_zone": {
      "terms": { "field": "zone.keyword" },
      "aggs": {
        "avg_temp": { "avg": { "field": "value" } }
      }
    }
  }
}

# Alertes par niveau de gravité
GET /logs-iot-alerts-*/_search
{
  "size": 0,
  "aggs": {
    "by_severity": {
      "terms": { "field": "alert_level.keyword" }
    }
  }
}

# Top 5 zones avec le plus d'anomalies
GET /logs-iot-sensors-*/_search
{
  "size": 0,
  "query": {
    "term": { "tags": "anomaly" }
  },
  "aggs": {
    "top_zones": {
      "terms": { 
        "field": "zone.keyword",
        "size": 5,
        "order": { "_count": "desc" }
      }
    }
  }
}
```

## ✅ Checklist de démarrage immédiat

### À faire cette semaine (Priorité MAX)

1. **Jour 1-2: Structure Flask**
   - [ ] Créer `webapp/app.py` minimal
   - [ ] Créer `webapp/requirements.txt`
   - [ ] Créer `webapp/Dockerfile`
   - [ ] Tester `docker-compose up -d`
   - [ ] Page "Hello World" accessible sur localhost:8000

2. **Jour 2-3: Données de test**
   - [ ] Script Python `scripts/generate_test_data.py`
   - [ ] Générer 10,000 logs CSV (température, humidité)
   - [ ] Générer 1,000 alertes JSON
   - [ ] Copier dans `data/uploads/`
   - [ ] Vérifier dans Kibana (Discover)

3. **Jour 3-4: Dashboard basique**
   - [ ] Template Bootstrap `templates/base.html`
   - [ ] Dashboard `templates/index.html` avec 4 KPI
   - [ ] API `/api/v1/stats` (total logs, errors, etc.)
   - [ ] Graphique Chart.js simple

4. **Jour 4-5: Module Upload**
   - [ ] Page `templates/upload.html`
   - [ ] Route POST `/upload`
   - [ ] Validation fichier
   - [ ] Sauvegarde métadonnées MongoDB
   - [ ] Test upload fichier CSV

5. **Fin semaine: Documentation**
   - [ ] Mettre à jour README.md
   - [ ] Screenshots dashboard
   - [ ] Documenter API
   - [ ] Commit + push GitHub

## 🎓 Objectifs pédagogiques atteints

Ce projet permet de maîtriser:

### Compétences techniques
- ✅ **Big Data**: Elasticsearch, indexation, recherche full-text
- ✅ **NoSQL**: MongoDB (documents), Redis (cache)
- ✅ **DevOps**: Docker, Docker Compose, orchestration multi-services
- ✅ **Backend**: Flask/Django, API REST, architecture MVC
- ✅ **Frontend**: HTML/CSS/JS, Bootstrap, Chart.js
- 🔄 **Data Engineering**: Logstash pipelines, ETL, data transformation
- 🔄 **Visualisation**: Kibana dashboards, graphiques interactifs
- 📊 **Architecture**: Microservices, design patterns, intégration

### Compétences transversales
- 📝 **Documentation**: README, PDF technique, API docs
- 🧪 **Qualité**: Tests unitaires, intégration, bonnes pratiques
- 🚀 **Déploiement**: Conteneurisation, environnements multiples
- 👥 **Collaboration**: Git, GitHub, méthodologies Agile
- 🎯 **Analyse**: Traduire besoin métier en spécifications techniques

## 📝 Conclusion de l'analyse

### Points forts du projet actuel
1. ✅ **Infrastructure Docker solide** - Tous services configurés et fonctionnels
2. ✅ **Pipelines Logstash avancés** - Anomaly detection déjà implémentée
3. ✅ **Architecture claire** - Séparation composants, volumes partagés
4. ✅ **Bases NoSQL prêtes** - MongoDB et Redis opérationnels
5. ✅ **Sécurité dev appropriée** - X-Pack disabled pour faciliter développement

### Lacunes majeures à combler
1. ❌ **Absence totale de webapp Flask** - Bloquant pour 80% des fonctionnalités
2. ❌ **Pas de visualisations Kibana** - Module obligatoire non fait
3. ❌ **Pas de données de test** - Impossible de valider le système
4. ❌ **Pas de tests automatisés** - Qualité non mesurée
5. ❌ **Documentation incomplète** - Livrables manquants

### Feuille de route recommandée

**Semaine 1-2**: Fondations (Obligatoire)
- Créer webapp Flask complète
- Implémenter upload + recherche
- Générer données test IoT
- 3 visualisations Kibana

**Semaine 3**: Consolidation (16/20)
- 3 modules intermédiaires
- Tests unitaires basiques
- Documentation README

**Semaine 4**: Excellence (20/20)
- 2 modules avancés (Alerting + ML ou Temps réel)
- Tests complets (>70% coverage)
- Documentation PDF complète
- Vidéo démo professionnelle

### Estimation réaliste

**Niveau 12/20 (Obligatoire uniquement)**:
- Temps: 10-12 jours
- Faisable: ✅ Oui, avec focus et rigueur

**Niveau 16/20 (+ 3 modules inter)**:
- Temps: 18-22 jours
- Faisable: ✅ Oui, recommandé

**Niveau 20/20 (+ 2 modules avancés)**:
- Temps: 28-35 jours
- Faisable: ⚠️ Ambitieux mais possible avec bonne organisation

### Message final

Le projet est **bien structuré au niveau infrastructure** mais nécessite un **développement applicatif complet**. La priorité absolue est de créer la webapp Flask fonctionnelle avec les modules obligatoires, puis d'ajouter progressivement les fonctionnalités avancées selon le temps disponible.

**Recommandation**: Viser 16/20 de manière solide plutôt que 20/20 précipité. La qualité du code, la documentation et la démo comptent autant que les fonctionnalités.

---

**Document créé le**: 28 octobre 2025  
**Projet**: IoT Smart Building - Monitoring & Analyse de Logs  
**Stack**: ELK (Elasticsearch, Logstash, Kibana) + Flask + MongoDB + Redis + Docker
