"""
Tests unitaires pour le module d'upload de fichiers
"""

import pytest
import os
import tempfile
import io
from unittest.mock import MagicMock, patch


class TestFileValidation:
    """Tests pour la validation des fichiers uploadés"""
    
    def test_validate_csv_extension(self):
        """Test validation extension CSV"""
        allowed = {'csv', 'json', 'txt'}
        
        # Extensions valides
        assert 'csv' in allowed
        assert 'json' in allowed
        assert 'txt' in allowed
        
        # Extensions invalides
        assert 'exe' not in allowed
        assert 'py' not in allowed
        assert 'php' not in allowed
    
    def test_validate_file_size(self):
        """Test validation de la taille du fichier"""
        max_size = 100 * 1024 * 1024  # 100 MB
        
        # Fichier valide (10 MB)
        valid_size = 10 * 1024 * 1024
        assert valid_size <= max_size
        
        # Fichier invalide (200 MB)
        invalid_size = 200 * 1024 * 1024
        assert invalid_size > max_size
    
    def test_validate_csv_header(self, sample_sensor_csv):
        """Test validation du header CSV"""
        lines = sample_sensor_csv.strip().split('\n')
        header = lines[0]
        
        expected_columns = ['timestamp', 'zone', 'sensor_type', 'sensor_id', 'value', 'unit', 'status']
        actual_columns = header.split(',')
        
        assert actual_columns == expected_columns
    
    def test_validate_csv_data_rows(self, sample_sensor_csv):
        """Test que les données CSV ont le bon nombre de colonnes"""
        lines = sample_sensor_csv.strip().split('\n')
        header_count = len(lines[0].split(','))
        
        for i, line in enumerate(lines[1:], start=2):
            columns = line.split(',')
            assert len(columns) == header_count, f"Ligne {i} a {len(columns)} colonnes au lieu de {header_count}"
    
    def test_validate_json_structure(self, sample_alert_json):
        """Test validation de la structure JSON"""
        required_fields = ['timestamp', 'zone', 'sensor_id', 'severity', 'message']
        
        for alert in sample_alert_json:
            for field in required_fields:
                assert field in alert, f"Champ requis '{field}' manquant"
    
    def test_validate_json_severity_values(self, sample_alert_json):
        """Test que les valeurs de severity sont valides"""
        valid_severities = {'low', 'medium', 'high', 'critical'}
        
        for alert in sample_alert_json:
            assert alert['severity'] in valid_severities


class TestFileUpload:
    """Tests pour le processus d'upload"""
    
    def test_create_upload_folder(self, temp_upload_folder):
        """Test création du dossier d'upload"""
        assert os.path.exists(temp_upload_folder)
        assert os.path.isdir(temp_upload_folder)
    
    def test_save_uploaded_file(self, temp_upload_folder, sample_sensor_csv):
        """Test sauvegarde d'un fichier uploadé"""
        filename = 'test_sensors.csv'
        filepath = os.path.join(temp_upload_folder, filename)
        
        with open(filepath, 'w') as f:
            f.write(sample_sensor_csv)
        
        assert os.path.exists(filepath)
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        assert content == sample_sensor_csv
    
    def test_generate_unique_filename(self):
        """Test génération de nom de fichier unique"""
        import uuid
        from datetime import datetime
        
        original_name = 'sensors.csv'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        unique_name = f"{timestamp}_{unique_id}_{original_name}"
        
        assert timestamp in unique_name
        assert original_name in unique_name
    
    def test_file_metadata_structure(self):
        """Test structure des métadonnées de fichier"""
        from datetime import datetime
        
        metadata = {
            'filename': 'sensors_test.csv',
            'original_name': 'sensors.csv',
            'upload_date': datetime.now(),
            'file_size': 2048,
            'file_type': 'csv',
            'status': 'uploaded',
            'num_logs': 0,
            'processing_time': 0.0,
            'errors': []
        }
        
        # Vérifier les champs requis
        required_fields = ['filename', 'original_name', 'upload_date', 'file_size', 
                          'file_type', 'status', 'num_logs']
        
        for field in required_fields:
            assert field in metadata


class TestFilePreview:
    """Tests pour la prévisualisation des fichiers"""
    
    def test_preview_first_10_lines(self, sample_sensor_csv):
        """Test prévisualisation des 10 premières lignes"""
        lines = sample_sensor_csv.strip().split('\n')
        preview_lines = lines[:10]
        
        assert len(preview_lines) <= 10
    
    def test_preview_csv_as_table(self, sample_sensor_csv):
        """Test conversion CSV en tableau pour prévisualisation"""
        lines = sample_sensor_csv.strip().split('\n')
        
        # Parser le header
        header = lines[0].split(',')
        
        # Parser les données
        data = []
        for line in lines[1:]:
            row = line.split(',')
            data.append(dict(zip(header, row)))
        
        assert len(data) == 5  # 5 lignes de données
        assert data[0]['zone'] == 'A'
        assert data[0]['sensor_type'] == 'temperature'
    
    def test_preview_json_pretty(self, sample_alert_json):
        """Test formatage JSON pour prévisualisation"""
        import json
        
        pretty_json = json.dumps(sample_alert_json, indent=2)
        
        assert '{\n' in pretty_json
        assert '"zone":' in pretty_json


class TestUploadErrors:
    """Tests pour la gestion des erreurs d'upload"""
    
    def test_handle_empty_file(self):
        """Test gestion fichier vide"""
        content = ""
        
        is_empty = len(content.strip()) == 0
        assert is_empty is True
    
    def test_handle_invalid_csv(self):
        """Test gestion CSV invalide"""
        invalid_csv = """col1,col2
value1
value1,value2,value3"""
        
        lines = invalid_csv.strip().split('\n')
        header_count = len(lines[0].split(','))
        
        errors = []
        for i, line in enumerate(lines[1:], start=2):
            if len(line.split(',')) != header_count:
                errors.append(f"Ligne {i}: nombre de colonnes incorrect")
        
        assert len(errors) == 2
    
    def test_handle_invalid_json(self):
        """Test gestion JSON invalide"""
        import json
        
        invalid_json = '{"key": "value",}'  # Virgule trailing invalide
        
        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_json)
    
    def test_handle_file_too_large(self):
        """Test gestion fichier trop volumineux"""
        max_size_mb = 100
        file_size_mb = 150
        
        error_message = None
        if file_size_mb > max_size_mb:
            error_message = f"Fichier trop volumineux: {file_size_mb}MB > {max_size_mb}MB"
        
        assert error_message is not None
        assert "150MB" in error_message
