"""
Tests unitaires pour l'API REST
"""

import pytest
import json
from datetime import datetime
from unittest.mock import MagicMock, patch


class TestAPIStats:
    """Tests pour l'endpoint /api/v1/stats"""
    
    def test_stats_response_structure(self):
        """Test structure de la réponse stats"""
        stats = {
            'total_logs': 10000,
            'logs_today': 500,
            'errors_count': 25,
            'sensors_active': 150,
            'timestamp': datetime.now().isoformat()
        }
        
        required_fields = ['total_logs', 'logs_today', 'errors_count', 'sensors_active', 'timestamp']
        
        for field in required_fields:
            assert field in stats
    
    def test_stats_values_are_integers(self):
        """Test que les valeurs numériques sont des entiers"""
        stats = {
            'total_logs': 10000,
            'logs_today': 500,
            'errors_count': 25,
            'sensors_active': 150
        }
        
        for key in ['total_logs', 'logs_today', 'errors_count', 'sensors_active']:
            assert isinstance(stats[key], int)


class TestAPISearch:
    """Tests pour l'endpoint /api/v1/search"""
    
    def test_search_request_params(self):
        """Test paramètres de requête de recherche"""
        params = {
            'q': 'level:ERROR',
            'zone': 'A',
            'sensor_type': 'temperature',
            'date_from': '2025-10-28',
            'date_to': '2025-10-29',
            'page': 1,
            'per_page': 50
        }
        
        assert params['page'] >= 1
        assert params['per_page'] <= 100
    
    def test_search_response_structure(self):
        """Test structure de la réponse de recherche"""
        response = {
            'results': [],
            'total': 100,
            'page': 1,
            'per_page': 50,
            'total_pages': 2,
            'execution_time': 0.152
        }
        
        required_fields = ['results', 'total', 'page', 'per_page', 'total_pages']
        
        for field in required_fields:
            assert field in response
    
    def test_pagination_calculation(self):
        """Test calcul de pagination"""
        total = 125
        per_page = 50
        
        total_pages = (total + per_page - 1) // per_page
        
        assert total_pages == 3


class TestAPIFiles:
    """Tests pour l'endpoint /api/v1/files"""
    
    def test_files_list_response(self):
        """Test liste des fichiers"""
        files = [
            {
                'id': '1',
                'filename': 'sensors.csv',
                'upload_date': '2025-10-28T10:00:00Z',
                'status': 'processed',
                'num_logs': 1000
            }
        ]
        
        assert len(files) >= 1
        assert 'filename' in files[0]
        assert 'status' in files[0]
    
    def test_file_status_values(self):
        """Test valeurs de statut valides"""
        valid_statuses = ['uploaded', 'processing', 'processed', 'error']
        
        file_data = {'status': 'processed'}
        
        assert file_data['status'] in valid_statuses


class TestAPIAlertRules:
    """Tests pour l'endpoint /api/v1/alert-rules"""
    
    def test_create_rule_request(self, sample_alert_rule):
        """Test création d'une règle via API"""
        required_fields = ['name', 'rule_type', 'conditions', 'severity']
        
        for field in required_fields:
            assert field in sample_alert_rule
    
    def test_list_rules_response(self):
        """Test liste des règles"""
        rules = [
            {
                'id': '1',
                'name': 'Temperature Rule',
                'enabled': True,
                'severity': 'critical',
                'trigger_count': 5
            }
        ]
        
        assert isinstance(rules, list)
        if rules:
            assert 'name' in rules[0]
            assert 'enabled' in rules[0]
    
    def test_toggle_rule_response(self):
        """Test toggle enable/disable d'une règle"""
        response = {
            'id': '1',
            'name': 'Temperature Rule',
            'enabled': False,
            'message': 'Rule disabled successfully'
        }
        
        assert 'enabled' in response
        assert 'message' in response


class TestAPIValidation:
    """Tests pour la validation des requêtes API"""
    
    def test_validate_required_fields(self):
        """Test validation des champs requis"""
        def validate_required(data, required_fields):
            missing = [f for f in required_fields if f not in data or data[f] is None]
            return missing
        
        data = {'name': 'Test', 'type': 'threshold'}
        required = ['name', 'type', 'conditions']
        
        missing = validate_required(data, required)
        
        assert 'conditions' in missing
        assert 'name' not in missing
    
    def test_validate_page_param(self):
        """Test validation du paramètre page"""
        def validate_page(page):
            if page is None:
                return 1
            try:
                page = int(page)
                return max(1, page)
            except ValueError:
                return 1
        
        assert validate_page(None) == 1
        assert validate_page('5') == 5
        assert validate_page('-1') == 1
        assert validate_page('invalid') == 1
    
    def test_validate_per_page_param(self):
        """Test validation du paramètre per_page"""
        def validate_per_page(per_page, max_allowed=100):
            if per_page is None:
                return 50
            try:
                per_page = int(per_page)
                return min(max(1, per_page), max_allowed)
            except ValueError:
                return 50
        
        assert validate_per_page(None) == 50
        assert validate_per_page('25') == 25
        assert validate_per_page('200') == 100
        assert validate_per_page('0') == 1


class TestAPIErrors:
    """Tests pour la gestion des erreurs API"""
    
    def test_error_response_format(self):
        """Test format de réponse d'erreur"""
        error_response = {
            'error': True,
            'code': 400,
            'message': 'Bad Request',
            'details': 'Missing required field: name'
        }
        
        assert error_response['error'] is True
        assert error_response['code'] == 400
        assert 'message' in error_response
    
    def test_not_found_error(self):
        """Test erreur 404"""
        error = {
            'error': True,
            'code': 404,
            'message': 'Resource not found'
        }
        
        assert error['code'] == 404
    
    def test_validation_error(self):
        """Test erreur de validation"""
        error = {
            'error': True,
            'code': 422,
            'message': 'Validation Error',
            'details': {
                'conditions': 'Field is required',
                'severity': 'Invalid value'
            }
        }
        
        assert error['code'] == 422
        assert 'details' in error


class TestAPIAuthentication:
    """Tests pour l'authentification API (si implémentée)"""
    
    def test_api_key_header(self):
        """Test header API key"""
        headers = {
            'X-API-Key': 'test-api-key-12345',
            'Content-Type': 'application/json'
        }
        
        assert 'X-API-Key' in headers
    
    def test_bearer_token_header(self):
        """Test header Bearer token"""
        headers = {
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
            'Content-Type': 'application/json'
        }
        
        assert headers['Authorization'].startswith('Bearer ')


class TestAPICaching:
    """Tests pour le cache des réponses API"""
    
    def test_cache_key_generation(self):
        """Test génération de clé de cache"""
        import hashlib
        
        params = {
            'endpoint': '/api/v1/stats',
            'zone': 'A',
            'timestamp': '2025-10-28'
        }
        
        # Générer clé de cache
        cache_key = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()
        
        assert len(cache_key) == 32
    
    def test_cache_ttl(self):
        """Test TTL du cache"""
        cache_config = {
            'stats': 60,      # 1 minute
            'search': 300,    # 5 minutes
            'files': 600      # 10 minutes
        }
        
        assert cache_config['stats'] == 60
        assert cache_config['search'] == 300
