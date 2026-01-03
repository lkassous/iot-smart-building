"""
Configuration Swagger/OpenAPI pour l'API IoT Smart Building
Documentation interactive de l'API REST
"""

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "IoT Smart Building API",
        "description": "API REST pour la gestion et l'analyse des données IoT du smart building. "
                      "Cette API permet de gérer les uploads de fichiers, rechercher dans les logs, "
                      "et accéder aux statistiques en temps réel.",
        "contact": {
            "name": "IoT Smart Building Team",
            "email": "support@iot-smart-building.com"
        },
        "version": "1.0.0",
        "termsOfService": "https://iot-smart-building.com/terms"
    },
    "host": "localhost:8000",
    "basePath": "/",
    "schemes": [
        "http"
    ],
    "tags": [
        {
            "name": "Health",
            "description": "Endpoints de santé et monitoring du système"
        },
        {
            "name": "Statistics",
            "description": "Statistiques et KPIs en temps réel"
        },
        {
            "name": "Logs",
            "description": "Recherche et consultation des logs IoT"
        },
        {
            "name": "Files",
            "description": "Gestion des fichiers uploadés"
        },
        {
            "name": "Upload",
            "description": "Upload de fichiers de données IoT"
        }
    ],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Token d'authentification JWT. Format: 'Bearer {token}'"
        }
    },
    "definitions": {
        "HealthResponse": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "example": "healthy",
                    "description": "Statut global du système"
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Timestamp du check"
                },
                "service": {
                    "type": "string",
                    "example": "iot-webapp"
                },
                "version": {
                    "type": "string",
                    "example": "1.0.0"
                },
                "elasticsearch": {
                    "type": "string",
                    "example": "connected"
                },
                "mongodb": {
                    "type": "string",
                    "example": "connected"
                },
                "redis": {
                    "type": "string",
                    "example": "connected"
                }
            }
        },
        "StatsResponse": {
            "type": "object",
            "properties": {
                "total_logs": {
                    "type": "integer",
                    "example": 24934,
                    "description": "Nombre total de logs"
                },
                "logs_today": {
                    "type": "integer",
                    "example": 1092,
                    "description": "Logs créés aujourd'hui"
                },
                "errors_count": {
                    "type": "integer",
                    "example": 245,
                    "description": "Nombre d'erreurs/anomalies"
                },
                "files_uploaded": {
                    "type": "integer",
                    "example": 3,
                    "description": "Fichiers uploadés"
                },
                "zones_active": {
                    "type": "integer",
                    "example": 9,
                    "description": "Zones actives (A-I)"
                },
                "sensors_active": {
                    "type": "integer",
                    "example": 712,
                    "description": "Capteurs actifs uniques"
                },
                "last_update": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Dernière mise à jour"
                }
            }
        },
        "LogEntry": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID unique du log"
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Timestamp du log"
                },
                "zone": {
                    "type": "string",
                    "example": "A",
                    "description": "Zone du bâtiment"
                },
                "sensor_type": {
                    "type": "string",
                    "example": "temperature",
                    "description": "Type de capteur"
                },
                "sensor_id": {
                    "type": "string",
                    "example": "2001",
                    "description": "ID du capteur"
                },
                "value": {
                    "type": "number",
                    "example": 22.5,
                    "description": "Valeur mesurée"
                },
                "unit": {
                    "type": "string",
                    "example": "°C",
                    "description": "Unité de mesure"
                },
                "status": {
                    "type": "string",
                    "example": "ok",
                    "enum": ["ok", "warning", "error"]
                },
                "floor": {
                    "type": "string",
                    "example": "1",
                    "description": "Étage du bâtiment"
                }
            }
        },
        "LogsResponse": {
            "type": "object",
            "properties": {
                "logs": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/LogEntry"
                    }
                },
                "total": {
                    "type": "integer",
                    "example": 2821,
                    "description": "Nombre total de résultats"
                },
                "page": {
                    "type": "integer",
                    "example": 1,
                    "description": "Page actuelle"
                },
                "pages": {
                    "type": "integer",
                    "example": 57,
                    "description": "Nombre total de pages"
                },
                "per_page": {
                    "type": "integer",
                    "example": 50,
                    "description": "Résultats par page"
                }
            }
        },
        "FileMetadata": {
            "type": "object",
            "properties": {
                "_id": {
                    "type": "string",
                    "description": "ID MongoDB du fichier"
                },
                "filename": {
                    "type": "string",
                    "example": "sensors_test.csv",
                    "description": "Nom du fichier"
                },
                "file_size": {
                    "type": "integer",
                    "example": 310,
                    "description": "Taille en bytes"
                },
                "file_type": {
                    "type": "string",
                    "example": "csv",
                    "enum": ["csv", "json", "txt"]
                },
                "num_logs": {
                    "type": "integer",
                    "example": 5,
                    "description": "Nombre de logs dans le fichier"
                },
                "status": {
                    "type": "string",
                    "example": "processed",
                    "enum": ["uploaded", "processing", "processed", "error"]
                },
                "upload_date": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Date d'upload"
                },
                "processing_time": {
                    "type": "number",
                    "example": 0.5,
                    "description": "Temps de traitement en secondes"
                }
            }
        },
        "FilesResponse": {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/FileMetadata"
                    }
                },
                "count": {
                    "type": "integer",
                    "example": 3,
                    "description": "Nombre de fichiers"
                }
            }
        },
        "UploadResponse": {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "example": True
                },
                "filename": {
                    "type": "string",
                    "example": "test_upload.csv"
                },
                "file_size": {
                    "type": "integer",
                    "example": 310
                },
                "num_logs": {
                    "type": "integer",
                    "example": 5
                },
                "file_id": {
                    "type": "string",
                    "description": "ID MongoDB du fichier uploadé"
                },
                "message": {
                    "type": "string",
                    "example": "Fichier uploadé avec succès. Logstash va traiter 5 logs."
                },
                "preview": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "description": "Aperçu des premières lignes"
                }
            }
        },
        "ErrorResponse": {
            "type": "object",
            "properties": {
                "error": {
                    "type": "string",
                    "example": "Fichier invalide",
                    "description": "Message d'erreur"
                },
                "validation_errors": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Détails des erreurs de validation"
                }
            }
        }
    }
}
