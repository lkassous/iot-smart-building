# 🏢 IoT Smart Building - Monitoring & Log Analysis Platform

> **Projet pédagogique** - Plateforme de centralisation, indexation et visualisation de données IoT en temps réel avec la Stack ELK

<!-- Badges CI/CD -->
[![CI/CD Pipeline](https://github.com/lkassous/iot-smart-building/actions/workflows/ci.yml/badge.svg)](https://github.com/lkassous/iot-smart-building/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/lkassous/iot-smart-building/branch/main/graph/badge.svg)](https://codecov.io/gh/lkassous/iot-smart-building)

<!-- Badges Docker Images -->
[![Webapp Image](https://img.shields.io/badge/ghcr.io-webapp-blue?logo=docker)](https://ghcr.io/lkassous/iot-smart-building-webapp)
[![Logstash Image](https://img.shields.io/badge/ghcr.io-logstash-orange?logo=docker)](https://ghcr.io/lkassous/iot-smart-building-logstash)
[![Elasticsearch Image](https://img.shields.io/badge/ghcr.io-elasticsearch-yellow?logo=docker)](https://ghcr.io/lkassous/iot-smart-building-elasticsearch)
[![Kibana Image](https://img.shields.io/badge/ghcr.io-kibana-pink?logo=docker)](https://ghcr.io/lkassous/iot-smart-building-kibana)

<!-- Badges Technologies -->
[![Docker](https://img.shields.io/badge/Docker-24.x-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.11-005571?logo=elasticsearch&logoColor=white)](https://www.elastic.co/elasticsearch/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Redis](https://img.shields.io/badge/Redis-7.2-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 Table des matières

- [Vue d'ensemble](#-vue-densemble)
- [Architecture](#-architecture)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Fonctionnalités](#-fonctionnalités)
- [Structure du projet](#-structure-du-projet)
- [Documentation](#-documentation)
- [Contribution](#-contribution)

---

## 🎯 Vue d'ensemble

### Contexte

Dans un **bâtiment intelligent** équipé de **centaines de capteurs IoT**, la gestion des logs devient critique. Cette plateforme permet de :

- 📊 **Centraliser** les données de capteurs (température, humidité, CO2, luminosité)
- 🔍 **Indexer** et rechercher rapidement dans des millions de logs
- 📈 **Visualiser** les tendances et anomalies en temps réel
- 🚨 **Alerter** sur les seuils critiques dépassés
- 🔧 **Prédire** les pannes d'équipements (ML optionnel)

### Use Cases Prioritaires

| Use Case | Description | Status |
|----------|-------------|--------|
| 🌡️ **Alerte Température** | Déclencher si <15°C ou >30°C | ✅ Implémenté (Logstash + Alerting) |
| ⚡ **Optimisation Énergétique** | Analyse patterns de consommation | ✅ Implémenté (Kibana) |
| 🔧 **Maintenance Prédictive** | Prédiction pannes via historique | 📋 ML optionnel |
| 🔔 **Notifications Multi-canal** | Email, Webhook, Slack, Discord | ✅ Implémenté |
| 📊 **Dashboard Temps Réel** | WebSocket live logs + alertes | ✅ Implémenté |

### KPI Suivis

- 📊 Température moyenne par zone/heure
- 🚨 Nombre d'alertes critiques/jour
- ⚡ Consommation énergétique temps réel
- 👥 Taux d'occupation des espaces
- 🔮 Prévisions de maintenance

---

## 🏗️ Architecture

### Vue d'ensemble

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Capteurs  │────▶│  Logstash   │────▶│Elasticsearch│
│  (CSV/JSON) │     │  Pipelines  │     │   Indexing  │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
┌─────────────┐     ┌─────────────┐           │
│   MongoDB   │◀────│ Flask Webapp│◀──────────┤
│  Metadata   │     │   (Port 8000)│          │
└─────────────┘     └─────────────┘           │
                                               │
┌─────────────┐     ┌─────────────┐           │
│    Redis    │◀────│   Kibana    │◀──────────┘
│    Cache    │     │Visualisation│
└─────────────┘     └─────────────┘
```

### Stack Technologique

| Composant | Version | Port | Rôle |
|-----------|---------|------|------|
| **Elasticsearch** | 8.11.0 | 9200 | Moteur de recherche & indexation |
| **Logstash** | 8.11.0 | 5000, 9600 | Ingestion & transformation données |
| **Kibana** | 8.11.0 | 5601 | Visualisation & dashboards |
| **MongoDB** | 7.0 | 27017 | Stockage métadonnées |
| **Redis** | 7.2 | 6379 | Cache & sessions |
| **Flask** | 3.x | 8000 | Application web |

### Flux de Données

1. **Upload** : Fichiers CSV/JSON → `data/uploads/`
2. **Ingestion** : Logstash surveille le répertoire et parse les fichiers
3. **Transformation** : Filtres Logstash (validation, enrichissement, détection anomalies)
4. **Indexation** : Elasticsearch avec indices journaliers (`logs-iot-sensors-2025.10.28`)
5. **Visualisation** : Kibana dashboards + Flask webapp
6. **Cache** : Redis pour optimiser les requêtes fréquentes

---

## 📦 Prérequis

- **Docker** 24.x ou supérieur
- **Docker Compose** 2.x ou supérieur
- **8 GB RAM** minimum (recommandé: 16 GB)
- **10 GB** d'espace disque

### Vérification

```bash
docker --version          # Docker version 24.0.0+
docker-compose --version  # Docker Compose version v2.20.0+
```

---

## 🚀 Installation

### Option 1: Utiliser les images Docker prébuilt (Recommandé)

```bash
# Pull les 4 images depuis GitHub Container Registry
docker pull ghcr.io/lkassous/iot-smart-building-webapp:latest
docker pull ghcr.io/lkassous/iot-smart-building-logstash:latest
docker pull ghcr.io/lkassous/iot-smart-building-elasticsearch:latest
docker pull ghcr.io/lkassous/iot-smart-building-kibana:latest

# Cloner le repo pour docker-compose.yml
git clone https://github.com/lkassous/iot-smart-building.git
cd iot-smart-building

# Démarrer avec les images prébuilt (décommentez les lignes "image:" dans docker-compose.yml)
docker-compose up -d
```

### Option 2: Build local depuis le code source

### 1. Cloner le repository

```bash
git clone https://github.com/lkassous/iot-smart-building.git
cd iot-smart-building
```

### 2. Configuration environnement

```bash
cp .env.example .env
# Éditer .env si nécessaire (optionnel en dev)
```

### 3. Démarrer la stack complète

```bash
docker-compose up -d
```

**Temps de démarrage** : ~2-3 minutes (téléchargement des images au premier lancement)

### 4. Vérifier les services

```bash
# Vérifier que tous les conteneurs sont en cours d'exécution
docker-compose ps

# Vérifier les logs
docker-compose logs -f
```

### 5. Accéder aux interfaces

| Service | URL | Credentials |
|---------|-----|-------------|
| **Flask Webapp** | http://localhost:8000 | - |
| **Kibana** | http://localhost:5601 | - |
| **Elasticsearch** | http://localhost:9200 | - |
| **MongoDB** | mongodb://localhost:27017 | admin / admin123 |

---

## 💻 Utilisation

### Démarrage rapide

```bash
# Démarrer tous les services
docker-compose up -d

# Voir les logs en temps réel
docker-compose logs -f webapp logstash

# Arrêter tous les services
docker-compose down

# Arrêter et supprimer les volumes (⚠️ perte de données)
docker-compose down -v
```

### Upload de fichiers de logs

**Via l'interface web** (🔄 En développement) :
1. Ouvrir http://localhost:8000/upload
2. Drag & drop un fichier CSV ou JSON
3. Vérifier le statut du traitement

**Via copie manuelle** (Méthode actuelle) :
```bash
# Copier un fichier dans le répertoire surveillé
cp mon_fichier_sensors.csv data/uploads/

# Logstash traitera automatiquement le fichier
docker-compose logs -f logstash
```

### Format des fichiers

#### CSV (Capteurs)
```csv
timestamp,zone,sensor_type,sensor_id,value,unit,status
2025-10-28T10:30:00,A,temperature,1001,22.5,°C,ok
2025-10-28T10:30:00,B,humidity,1002,65.2,%,ok
2025-10-28T10:30:00,C,co2,1003,450,ppm,ok
```

#### JSON (Alertes)
```json
{
  "timestamp": "2025-10-28T10:30:00Z",
  "sensor": "1001",
  "location": "A",
  "alert_type": "temperature_high",
  "severity": "critical",
  "value": 35.2,
  "message": "Temperature exceeds threshold"
}
```

### Recherche de logs

**Via Kibana** :
1. Ouvrir http://localhost:5601
2. Aller dans **Discover**
3. Créer un index pattern : `logs-iot-*`
4. Utiliser la barre de recherche KQL

**Via API Elasticsearch** :
```bash
# Récupérer les 10 derniers logs
curl -X GET "localhost:9200/logs-iot-sensors-*/_search?pretty&size=10"

# Rechercher les alertes de température
curl -X GET "localhost:9200/logs-iot-sensors-*/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        { "term": { "sensor_type": "temperature" } },
        { "exists": { "field": "tags" } }
      ],
      "filter": [
        { "term": { "tags": "anomaly" } }
      ]
    }
  }
}
'
```

---

## ✨ Fonctionnalités

### 🟢 Module Obligatoire (12/20) - COMPLET ✅

| Module | Composants | Statut |
|--------|-----------|--------|
| **Gestion Fichiers** | Upload drag & drop, validation CSV/JSON, prévisualisation, métadonnées MongoDB | ✅ 100% |
| **Stack ELK** | Elasticsearch 8.11, Logstash pipelines CSV/JSON, Kibana dashboards, anomaly detection | ✅ 100% |
| **Interface Web** | Dashboard temps réel, 4 KPI cards, Chart.js, recherche avec filtres, résultats DataTables | ✅ 100% |
| **MongoDB** | Métadonnées fichiers, historique recherches, règles d'alertes | ✅ 100% |
| **Docker** | 6 services orchestrés, health checks, volumes persistants, Dockerfile webapp | ✅ 100% |

### 🟡 Modules Intermédiaires (16/20) - 3 COMPLETS ✅

| Module | Description | Statut |
|--------|-------------|--------|
| **Authentification** | Flask-Login, 3 rôles (Admin/User/Viewer), permissions décorateurs | ✅ 100% |
| **Cache Redis** | TTL 5min sur requêtes ES, gestion sessions, invalidation intelligente | ✅ 100% |
| **API REST + Swagger** | Endpoints CRUD complets, OpenAPI 3.0, pagination, versioning | ✅ 100% |

### � Modules Avancés (20/20) - 2 COMPLETS ✅

| Module | Description | Statut |
|--------|-------------|--------|
| **Alerting Intelligent** | Moteur de règles (threshold/range/pattern), notifications email/webhook/Slack/Discord, cooldown, historique | ✅ 100% |
| **WebSocket Temps Réel** | Flask-SocketIO, live logs dashboard, alertes critiques push, stats temps réel toutes les 5s | ✅ 100% |
| **CI/CD Pipeline** | GitHub Actions (lint, tests, intégration Docker, build), pytest 107 tests | ✅ 100% |

### 🧪 Tests & Qualité

- **107 tests unitaires** couvrant upload, Elasticsearch, MongoDB, API, règles d'alertes
- **GitHub Actions CI/CD** avec linting (flake8, black), tests, et build Docker
- **Documentation complète** avec Swagger/OpenAPI et copilot-instructions

---

## 📂 Structure du projet

```
iot-smart-building/
├── .github/
│   └── copilot-instructions.md    # Instructions pour agents IA
├── data/
│   ├── uploads/                   # 📂 Fichiers uploadés (surveillé par Logstash)
│   └── test-data/                 # 📂 Données de test générées
├── docker-compose.yml             # 🐳 Orchestration services
├── .env.example                   # 🔧 Variables d'environnement exemple
├── .gitignore                     # 🚫 Fichiers ignorés par Git
├── ANALYSE_CAHIER_DES_CHARGES.md  # 📋 Analyse détaillée du projet
├── README.md                      # 📖 Ce fichier
│
├── elasticsearch/
│   └── mappings/                  # 🗺️ Templates d'index (à créer)
│
├── kibana/
│   └── exports/                   # 📊 Dashboards exportés (à créer)
│
├── logstash/
│   ├── config/
│   │   └── logstash.yml          # ⚙️ Configuration Logstash
│   └── pipeline/
│       ├── csv-pipeline.conf     # 📄 Pipeline CSV (capteurs)
│       └── json-pipeline.conf    # 📄 Pipeline JSON (alertes)
│
├── webapp/                        # 🌐 Application Flask (en développement)
│   ├── app.py                    # 🚀 Point d'entrée (à créer)
│   ├── config.py                 # ⚙️ Configuration (à créer)
│   ├── requirements.txt          # 📦 Dépendances Python (à créer)
│   ├── Dockerfile                # 🐳 Image Docker (à créer)
│   ├── models/                   # 📊 Modèles MongoDB
│   │   ├── file_metadata.py      # Métadonnées fichiers
│   │   └── search_history.py     # Historique recherches
│   ├── routes/                   # 🛣️ Routes Flask
│   │   ├── main.py              # Dashboard
│   │   ├── upload.py            # Upload fichiers
│   │   ├── search.py            # Recherche
│   │   └── api.py               # API REST
│   ├── utils/                    # 🛠️ Utilitaires
│   │   ├── elasticsearch.py     # Client Elasticsearch
│   │   ├── mongodb.py           # Client MongoDB
│   │   ├── redis_client.py      # Client Redis
│   │   └── validators.py        # Validateurs
│   ├── static/                   # 📁 Assets frontend
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   └── templates/                # 📄 Templates Jinja2
│       ├── base.html
│       ├── index.html
│       ├── upload.html
│       ├── search.html
│       └── results.html
│
├── scripts/                       # 🔧 Scripts utilitaires
│   └── generate_test_data.py     # Génération données test (à créer)
│
└── tests/                        # 🧪 Tests (à créer)
    ├── test_upload.py
    ├── test_elasticsearch.py
    └── test_mongodb.py
```

---

## 📚 Documentation

### Documents disponibles

- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** : Guide pour agents IA
- **[ANALYSE_CAHIER_DES_CHARGES.md](ANALYSE_CAHIER_DES_CHARGES.md)** : Analyse complète du cahier des charges
- **[.env.example](.env.example)** : Variables d'environnement
- **[logstash/pipeline/](logstash/pipeline/)** : Configuration pipelines Logstash

### Ressources externes

- [Elasticsearch Reference](https://www.elastic.co/guide/en/elasticsearch/reference/8.11/)
- [Logstash Reference](https://www.elastic.co/guide/en/logstash/8.11/)
- [Kibana Guide](https://www.elastic.co/guide/en/kibana/8.11/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [MongoDB Documentation](https://www.mongodb.com/docs/)

---

## 🐛 Debugging

### Logs des services

```bash
# Tous les services
docker-compose logs -f

# Service spécifique
docker-compose logs -f elasticsearch
docker-compose logs -f logstash
docker-compose logs -f webapp
```

### Vérifier l'état des services

```bash
# Santé Elasticsearch
curl http://localhost:9200/_cluster/health?pretty

# Santé Kibana
curl http://localhost:5601/api/status

# Liste des indices
curl http://localhost:9200/_cat/indices?v

# Stats Logstash
curl http://localhost:9600/_node/stats?pretty
```

### Problèmes courants

| Problème | Solution |
|----------|----------|
| **Elasticsearch ne démarre pas** | Vérifier RAM disponible (min 4GB pour ES). Augmenter `vm.max_map_count` sur Linux : `sudo sysctl -w vm.max_map_count=262144` |
| **Logstash ne traite pas les fichiers** | Vérifier les logs : `docker-compose logs logstash`. Vérifier format CSV/JSON. |
| **Données n'apparaissent pas dans Kibana** | Vérifier que l'index pattern existe : `logs-iot-*`. Rafraîchir les champs. |
| **Webapp inaccessible** | Vérifier que le conteneur webapp est démarré : `docker-compose ps`. Vérifier les logs : `docker-compose logs webapp` |

---

## 🤝 Contribution

### Workflow Git

```bash
# Créer une branche feature
git checkout -b feature/nom-fonctionnalite

# Faire vos modifications
git add .
git commit -m "feat: description de la fonctionnalité"

# Pousser la branche
git push origin feature/nom-fonctionnalite

# Créer une Pull Request sur GitHub
```

### Conventions de commit

Utiliser [Conventional Commits](https://www.conventionalcommits.org/) :

- `feat:` Nouvelle fonctionnalité
- `fix:` Correction de bug
- `docs:` Documentation
- `style:` Formatage code
- `refactor:` Refactoring
- `test:` Ajout de tests
- `chore:` Tâches maintenance

---

## 📜 Licence

Ce projet est un **projet pédagogique** à but éducatif.

---

## 👥 Auteurs

- **Votre Nom** - *Développement initial* - [@votre-username](https://github.com/votre-username)

---

## 🙏 Remerciements

- Elastic pour la stack ELK
- Flask et la communauté Python
- MongoDB et Redis pour leurs excellentes bases de données NoSQL
- Docker pour la conteneurisation

---

## 📊 État du projet

**Dernière mise à jour** : 3 janvier 2026

| Module | Statut | Progression |
|--------|--------|-------------|
| Infrastructure Docker | ✅ Complet | 100% |
| Logstash Pipelines | ✅ Complet | 100% |
| Elasticsearch | ✅ Complet | 100% |
| Kibana Dashboards | ✅ Complet | 100% |
| Flask Webapp | ✅ Complet | 100% |
| MongoDB Integration | ✅ Complet | 100% |
| Redis Cache | ✅ Complet | 100% |
| Authentification | ✅ Complet | 100% |
| API REST + Swagger | ✅ Complet | 100% |
| WebSocket Temps Réel | ✅ Complet | 100% |
| Alerting Intelligent | ✅ Complet | 100% |
| Tests Unitaires | ✅ 107 tests | 100% |
| CI/CD Pipeline | ✅ GitHub Actions | 100% |
| Documentation | ✅ Complet | 100% |

**Note visée** : 20/20 (modules obligatoires + 3 intermédiaires + 2 avancés + CI/CD)

---

<div align="center">

**[⬆ Retour en haut](#-iot-smart-building---monitoring--log-analysis-platform)**

Made with ❤️ for IoT Smart Building

</div>
