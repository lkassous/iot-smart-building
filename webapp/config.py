"""
Configuration de l'application Flask
Charge les variables d'environnement et définit les paramètres
"""
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()


class Config:
    """Configuration de base"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    TESTING = False
    
    # Elasticsearch
    ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST', 'http://localhost:9200')
    ELASTICSEARCH_INDEX_SENSORS = 'logs-iot-sensors-*'
    ELASTICSEARCH_INDEX_ALERTS = 'logs-iot-alerts-*'
    
    # MongoDB
    MONGODB_URI = os.getenv(
        'MONGODB_URI',
        'mongodb://admin:admin123@localhost:27017/iot_smart_building?authSource=admin'
    )
    MONGODB_DB = os.getenv('MONGODB_DB', 'iot_smart_building')
    
    # Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_CACHE_TTL = 300  # 5 minutes
    
    # Upload
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/app/uploads')
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 100))
    MAX_CONTENT_LENGTH = MAX_FILE_SIZE_MB * 1024 * 1024  # Conversion en bytes
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'csv,json,txt').split(','))
    
    # Pagination
    RESULTS_PER_PAGE = 50
    
    # Zones du bâtiment (pour validation)
    BUILDING_ZONES = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
    
    # Types de capteurs
    SENSOR_TYPES = ['temperature', 'humidity', 'luminosity', 'co2']
    
    # Seuils d'alerte (utilisés pour validation et affichage)
    THRESHOLDS = {
        'temperature': {'min': 15, 'max': 30, 'unit': '°C'},
        'humidity': {'min': 30, 'max': 80, 'unit': '%'},
        'co2': {'min': 0, 'max': 1000, 'unit': 'ppm'},
        'luminosity': {'min': 0, 'max': 1000, 'unit': 'lux'}
    }
    
    # Configuration Email (Flask-Mail)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@iot-smart-building.local')
    
    # Configuration des notifications
    NOTIFICATIONS_ENABLED = os.getenv('NOTIFICATIONS_ENABLED', 'False').lower() == 'true'
    SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')
    DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')


class DevelopmentConfig(Config):
    """Configuration de développement"""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Configuration de test"""
    TESTING = True
    DEBUG = True
    # Utiliser des bases de données de test
    MONGODB_DB = 'iot_smart_building_test'
    REDIS_DB = 1


class ProductionConfig(Config):
    """Configuration de production"""
    DEBUG = False
    TESTING = False
    # En production, SECRET_KEY doit absolument être définie
    def __init__(self):
        super().__init__()
        if not os.getenv('SECRET_KEY'):
            raise ValueError("SECRET_KEY must be set in production!")


# Mapping des configurations
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Retourne la configuration selon l'environnement"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
