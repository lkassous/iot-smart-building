# 🔐 Identifiants de Connexion - IoT Smart Building

## Accès Application Web
**URL**: http://localhost:8000

### Comptes Utilisateurs

| Utilisateur | Mot de passe | Rôle | Permissions |
|------------|--------------|------|-------------|
| `admin` | `admin123` | Admin | Lecture, écriture, administration complète |
| `user` | `user123` | User | Lecture et écriture (upload, recherche) |
| `viewer` | `viewer123` | Viewer | Lecture seule (dashboard, recherche) |

## Accès Services Backend

### Elasticsearch
- **URL**: http://localhost:9200
- **Authentification**: Aucune (développement)
- **Indices principaux**:
  - `logs-iot-sensors-*` - Données capteurs
  - `logs-iot-alerts-*` - Alertes

### Kibana
- **URL**: http://localhost:5601
- **Authentification**: Aucune (développement)
- **Dashboard**: http://localhost:5601/app/dashboards#/view/iot-smart-building-dashboard

### MongoDB
- **Host**: localhost:27017
- **Username**: `admin`
- **Password**: `admin123`
- **Database**: `iot_smart_building`
- **Connection URI**: `mongodb://admin:admin123@localhost:27017/iot_smart_building?authSource=admin`

### Redis
- **Host**: localhost:6379
- **Authentification**: Aucune
- **Usage**: Cache (stats 5min TTL), sessions utilisateur

### Logstash
- **TCP**: localhost:5000 (CSV pipeline)
- **HTTP**: localhost:9600 (monitoring API)

## API REST

### Swagger/OpenAPI Documentation
- **URL**: http://localhost:8000/api/docs
- **OpenAPI Spec**: http://localhost:8000/apispec.json

### Endpoints Principaux
- `GET /health` - Health check
- `GET /api/v1/stats` - Statistiques globales
- `GET /api/v1/logs` - Recherche de logs (avec filtres)
- `GET /api/v1/files` - Liste des fichiers uploadés
- `POST /upload` - Upload de fichier
- `GET /api/v1/current-user` - Utilisateur connecté (requiert auth)

## Sécurité

⚠️ **AVERTISSEMENT**: Ces identifiants sont **uniquement pour l'environnement de développement**.

**Pour la production**:
1. Changer tous les mots de passe par défaut
2. Activer HTTPS (TLS/SSL)
3. Activer Elasticsearch Security (X-Pack)
4. Configurer l'authentification Redis
5. Utiliser des secrets Kubernetes/Docker Swarm
6. Activer CSRF protection dans Flask
7. Configurer un pare-feu (firewall)
8. Limiter les taux d'API (rate limiting)

## Commandes Utiles

### Connexion MongoDB via CLI
```bash
docker exec -it iot-mongodb mongosh -u admin -p admin123 --authenticationDatabase admin iot_smart_building
```

### Test API avec curl
```bash
# Login
curl -c cookies.txt -X POST http://localhost:8000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Accès dashboard (avec cookie de session)
curl -b cookies.txt http://localhost:8000/

# API current-user
curl -b cookies.txt http://localhost:8000/api/v1/current-user

# Logout
curl -b cookies.txt http://localhost:8000/logout -L
```

### Vérification des services
```bash
# Santé de l'application
curl http://localhost:8000/health | jq

# Stats Elasticsearch
curl http://localhost:9200/_cat/indices?v

# Logs Logstash
docker logs iot-logstash --tail=50

# Connexion Redis
docker exec -it iot-redis redis-cli
```

## Support

Pour toute question sur les identifiants ou l'authentification, consulter :
- `webapp/models/user.py` - Modèle utilisateur
- `webapp/utils/user_manager.py` - Gestion des utilisateurs
- `webapp/routes/auth.py` - Routes d'authentification
- `webapp/app.py` - Configuration Flask-Login (lignes 40-58)
