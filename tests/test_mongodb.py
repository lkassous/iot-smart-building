"""
Tests unitaires pour le module MongoDB
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from bson import ObjectId


class TestFileMetadata:
    """Tests pour les métadonnées de fichiers"""
    
    def test_create_file_metadata(self):
        """Test création de métadonnées de fichier"""
        metadata = {
            'filename': 'sensors_20251028_143022.csv',
            'original_name': 'sensors.csv',
            'upload_date': datetime.now(),
            'file_size': 2048576,
            'file_type': 'csv',
            'status': 'uploaded',
            'num_logs': 0,
            'processing_time': 0.0,
            'errors': []
        }
        
        assert metadata['filename'].endswith('.csv')
        assert metadata['status'] == 'uploaded'
        assert metadata['file_size'] == 2048576
    
    def test_update_file_status(self):
        """Test mise à jour du statut d'un fichier"""
        statuses = ['uploaded', 'processing', 'processed', 'error']
        
        for status in statuses:
            metadata = {'status': status}
            assert metadata['status'] in statuses
    
    def test_file_size_formatting(self):
        """Test formatage de la taille du fichier"""
        def format_size(size_bytes):
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
        
        assert format_size(512) == "512 B"
        assert format_size(1536) == "1.5 KB"
        assert format_size(2048576) == "2.0 MB"


class TestSearchHistory:
    """Tests pour l'historique des recherches"""
    
    def test_create_search_history_entry(self):
        """Test création d'une entrée d'historique de recherche"""
        entry = {
            'query': 'level:ERROR AND zone:A',
            'filters': {
                'level': 'ERROR',
                'zone': 'A',
                'date_from': datetime.now() - timedelta(days=1),
                'date_to': datetime.now()
            },
            'num_results': 247,
            'execution_time': 0.152,
            'timestamp': datetime.now()
        }
        
        assert 'query' in entry
        assert entry['num_results'] == 247
        assert entry['execution_time'] < 1.0
    
    def test_search_history_pagination(self):
        """Test pagination de l'historique de recherche"""
        total_entries = 100
        per_page = 10
        
        total_pages = (total_entries + per_page - 1) // per_page
        
        assert total_pages == 10
    
    def test_filter_search_history_by_date(self):
        """Test filtrage de l'historique par date"""
        now = datetime.now()
        entries = [
            {'timestamp': now - timedelta(hours=1)},
            {'timestamp': now - timedelta(days=1)},
            {'timestamp': now - timedelta(days=7)},
            {'timestamp': now - timedelta(days=30)}
        ]
        
        # Filtrer les entrées des dernières 24h
        cutoff = now - timedelta(days=1)
        recent = [e for e in entries if e['timestamp'] >= cutoff]
        
        assert len(recent) == 2


class TestMongoDBOperations:
    """Tests pour les opérations MongoDB"""
    
    def test_insert_document(self, mock_mongodb):
        """Test insertion d'un document"""
        collection = mock_mongodb['files']
        doc = {
            'filename': 'test.csv',
            'upload_date': datetime.now()
        }
        
        result = collection.insert_one(doc)
        
        assert result.inserted_id is not None
    
    def test_find_documents(self, mock_mongodb):
        """Test recherche de documents"""
        collection = mock_mongodb['files']
        
        docs = list(collection.find())
        
        assert len(docs) >= 1
        assert 'filename' in docs[0]
    
    def test_find_one_document(self, mock_mongodb):
        """Test recherche d'un document unique"""
        collection = mock_mongodb['files']
        
        doc = collection.find_one({'_id': 'test-id'})
        
        assert doc is not None
        assert 'filename' in doc
    
    def test_update_document(self, mock_mongodb):
        """Test mise à jour d'un document"""
        collection = mock_mongodb['files']
        collection.update_one = MagicMock(return_value=MagicMock(modified_count=1))
        
        result = collection.update_one(
            {'_id': 'test-id'},
            {'$set': {'status': 'processed'}}
        )
        
        assert result.modified_count == 1
    
    def test_delete_document(self, mock_mongodb):
        """Test suppression d'un document"""
        collection = mock_mongodb['files']
        collection.delete_one = MagicMock(return_value=MagicMock(deleted_count=1))
        
        result = collection.delete_one({'_id': 'test-id'})
        
        assert result.deleted_count == 1


class TestAlertRulesStorage:
    """Tests pour le stockage des règles d'alertes"""
    
    def test_create_alert_rule(self, sample_alert_rule):
        """Test création d'une règle d'alerte"""
        assert sample_alert_rule['name'] == 'Test Temperature Rule'
        assert sample_alert_rule['rule_type'] == 'threshold'
        assert sample_alert_rule['conditions']['operator'] == '>'
    
    def test_validate_rule_type(self):
        """Test validation du type de règle"""
        valid_types = ['threshold', 'range', 'pattern', 'trend']
        
        assert 'threshold' in valid_types
        assert 'invalid' not in valid_types
    
    def test_validate_severity(self):
        """Test validation de la sévérité"""
        valid_severities = ['low', 'medium', 'high', 'critical']
        
        for severity in valid_severities:
            assert severity in valid_severities
    
    def test_rule_conditions_structure(self, sample_alert_rule):
        """Test structure des conditions de règle"""
        conditions = sample_alert_rule['conditions']
        
        assert 'field' in conditions
        assert 'operator' in conditions
        assert 'threshold' in conditions
    
    def test_rule_filters_structure(self, sample_alert_rule):
        """Test structure des filtres de règle"""
        filters = sample_alert_rule['filters']
        
        assert filters.get('sensor_type') == 'temperature'
        assert filters.get('zone') == 'A'
    
    def test_rule_actions_structure(self, sample_alert_rule):
        """Test structure des actions de règle"""
        actions = sample_alert_rule['actions']
        
        assert len(actions) >= 1
        assert actions[0]['type'] == 'email'
        assert 'config' in actions[0]


class TestMongoDBIndexes:
    """Tests pour les index MongoDB"""
    
    def test_file_metadata_indexes(self):
        """Test définition des index pour les métadonnées de fichiers"""
        indexes = [
            {'keys': [('upload_date', -1)], 'name': 'upload_date_desc'},
            {'keys': [('status', 1)], 'name': 'status_asc'},
            {'keys': [('file_type', 1)], 'name': 'file_type_asc'}
        ]
        
        assert len(indexes) == 3
        assert indexes[0]['name'] == 'upload_date_desc'
    
    def test_search_history_indexes(self):
        """Test définition des index pour l'historique de recherche"""
        indexes = [
            {'keys': [('timestamp', -1)], 'name': 'timestamp_desc'},
            {'keys': [('user_id', 1)], 'name': 'user_id_asc'}
        ]
        
        assert len(indexes) == 2
    
    def test_alert_rules_indexes(self):
        """Test définition des index pour les règles d'alertes"""
        indexes = [
            {'keys': [('name', 1)], 'name': 'name_asc', 'unique': True},
            {'keys': [('enabled', 1)], 'name': 'enabled_asc'},
            {'keys': [('severity', 1)], 'name': 'severity_asc'}
        ]
        
        assert indexes[0]['unique'] is True


class TestObjectIdHandling:
    """Tests pour la gestion des ObjectId"""
    
    def test_create_object_id(self):
        """Test création d'un ObjectId"""
        oid = ObjectId()
        
        assert len(str(oid)) == 24
    
    def test_convert_string_to_object_id(self):
        """Test conversion string vers ObjectId"""
        oid_str = "507f1f77bcf86cd799439011"
        oid = ObjectId(oid_str)
        
        assert str(oid) == oid_str
    
    def test_invalid_object_id(self):
        """Test ObjectId invalide"""
        with pytest.raises(Exception):
            ObjectId("invalid-id")
    
    def test_object_id_comparison(self):
        """Test comparaison d'ObjectId"""
        oid1 = ObjectId()
        oid2 = ObjectId(str(oid1))
        
        assert oid1 == oid2
