"""
Fixtures partagées pour tous les tests
"""

import pytest
import os
import sys
import tempfile
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Ajouter le chemin webapp pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'webapp'))


@pytest.fixture
def app():
    """Crée une instance de l'application Flask pour les tests"""
    from app import app as flask_app
    flask_app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'UPLOAD_FOLDER': tempfile.mkdtemp(),
        'MAX_CONTENT_LENGTH': 100 * 1024 * 1024  # 100MB
    })
    
    yield flask_app


@pytest.fixture
def client(app):
    """Client de test Flask"""
    return app.test_client()


@pytest.fixture
def mock_elasticsearch():
    """Mock du client Elasticsearch"""
    mock_es = MagicMock()
    
    # Simuler une réponse de recherche
    mock_es.search.return_value = {
        'took': 5,
        'timed_out': False,
        '_shards': {'total': 5, 'successful': 5, 'skipped': 0, 'failed': 0},
        'hits': {
            'total': {'value': 100, 'relation': 'eq'},
            'max_score': 1.0,
            'hits': [
                {
                    '_index': 'logs-iot-sensors-2025.10.28',
                    '_id': '1',
                    '_score': 1.0,
                    '_source': {
                        '@timestamp': '2025-10-28T10:00:00Z',
                        'zone': 'A',
                        'sensor_type': 'temperature',
                        'sensor_id': '1001',
                        'value': 22.5,
                        'unit': '°C',
                        'status': 'ok'
                    }
                }
            ]
        }
    }
    
    # Simuler count
    mock_es.count.return_value = {'count': 100}
    
    # Simuler index
    mock_es.index.return_value = {'result': 'created', '_id': 'test-id'}
    
    # Simuler cluster health
    mock_es.cluster.health.return_value = {'status': 'green'}
    
    return mock_es


@pytest.fixture
def mock_mongodb():
    """Mock du client MongoDB"""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    
    # Simuler insert
    mock_collection.insert_one.return_value = MagicMock(inserted_id='test-id')
    
    # Simuler find
    mock_collection.find.return_value = [
        {
            '_id': 'test-id-1',
            'filename': 'test.csv',
            'upload_date': datetime.now(),
            'status': 'processed'
        }
    ]
    
    # Simuler find_one
    mock_collection.find_one.return_value = {
        '_id': 'test-id',
        'filename': 'test.csv',
        'upload_date': datetime.now(),
        'status': 'processed'
    }
    
    mock_db.__getitem__ = lambda self, name: mock_collection
    
    return mock_db


@pytest.fixture
def mock_redis():
    """Mock du client Redis"""
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.exists.return_value = 0
    mock_redis.expire.return_value = True
    
    return mock_redis


@pytest.fixture
def sample_sensor_csv():
    """Données CSV de capteurs exemple"""
    return """timestamp,zone,sensor_type,sensor_id,value,unit,status
2025-10-28T10:00:00Z,A,temperature,1001,22.5,°C,ok
2025-10-28T10:01:00Z,A,temperature,1001,22.7,°C,ok
2025-10-28T10:02:00Z,B,humidity,2001,45.2,%,ok
2025-10-28T10:03:00Z,C,co2,3001,450,ppm,ok
2025-10-28T10:04:00Z,A,temperature,1001,35.5,°C,warning"""


@pytest.fixture
def sample_alert_json():
    """Données JSON d'alertes exemple"""
    return [
        {
            "timestamp": "2025-10-28T10:00:00Z",
            "zone": "A",
            "sensor_id": "1001",
            "severity": "critical",
            "message": "Température critique détectée",
            "value": 35.5
        },
        {
            "timestamp": "2025-10-28T10:01:00Z",
            "zone": "B",
            "sensor_id": "2001",
            "severity": "high",
            "message": "Humidité anormale",
            "value": 85.0
        }
    ]


@pytest.fixture
def temp_upload_folder():
    """Crée un dossier temporaire pour les uploads"""
    folder = tempfile.mkdtemp()
    yield folder
    # Cleanup
    import shutil
    shutil.rmtree(folder, ignore_errors=True)


@pytest.fixture
def sample_alert_rule():
    """Règle d'alerte exemple"""
    return {
        'name': 'Test Temperature Rule',
        'description': 'Alerte si température > 30°C',
        'rule_type': 'threshold',
        'enabled': True,
        'conditions': {
            'field': 'value',
            'operator': '>',
            'threshold': 30
        },
        'filters': {
            'sensor_type': 'temperature',
            'zone': 'A'
        },
        'severity': 'critical',
        'actions': [
            {
                'type': 'email',
                'config': {
                    'recipients': ['admin@example.com']
                }
            }
        ],
        'cooldown_seconds': 300
    }


@pytest.fixture
def sample_logs_for_evaluation():
    """Logs exemple pour évaluation des règles"""
    return [
        {
            '@timestamp': datetime.now().isoformat(),
            'zone': 'A',
            'sensor_type': 'temperature',
            'sensor_id': '1001',
            'value': 35.5,
            'building': 'Smart Building A'
        },
        {
            '@timestamp': datetime.now().isoformat(),
            'zone': 'A',
            'sensor_type': 'temperature',
            'sensor_id': '1002',
            'value': 36.2,
            'building': 'Smart Building A'
        },
        {
            '@timestamp': datetime.now().isoformat(),
            'zone': 'B',
            'sensor_type': 'temperature',
            'sensor_id': '1003',
            'value': 22.0,
            'building': 'Smart Building A'
        }
    ]
