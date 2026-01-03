"""
Validateurs pour les fichiers uploadés
Vérifie la structure et le contenu des fichiers CSV et JSON
"""
import csv
import json
import logging

logger = logging.getLogger(__name__)


def validate_csv_structure(filepath, max_preview_lines=10):
    """
    Valide la structure d'un fichier CSV
    
    Args:
        filepath: Chemin du fichier
        max_preview_lines: Nombre de lignes à prévisualiser
    
    Returns:
        dict: {
            'valid': bool,
            'errors': list,
            'num_lines': int,
            'preview': list,
            'headers': list
        }
    """
    result = {
        'valid': False,
        'errors': [],
        'num_lines': 0,
        'preview': [],
        'headers': []
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Lire l'en-tête
            reader = csv.reader(f)
            
            try:
                headers = next(reader)
                result['headers'] = headers
            except StopIteration:
                result['errors'].append('Fichier CSV vide')
                return result
            
            # Vérifier les colonnes requises pour les sensors
            required_columns = ['timestamp', 'zone', 'sensor_type', 'sensor_id', 'value', 'unit', 'status']
            missing_columns = [col for col in required_columns if col not in headers]
            
            if missing_columns:
                result['errors'].append(f'Colonnes manquantes : {", ".join(missing_columns)}')
            
            # Lire les premières lignes pour prévisualisation
            preview_lines = []
            line_count = 0
            
            for i, row in enumerate(reader):
                line_count += 1
                
                if i < max_preview_lines:
                    preview_lines.append(row)
                
                # Validation basique des données
                if len(row) != len(headers):
                    result['errors'].append(f'Ligne {i+2}: nombre de colonnes incorrect ({len(row)} au lieu de {len(headers)})')
                    if len(result['errors']) > 10:  # Limiter les erreurs
                        result['errors'].append('... (trop d\'erreurs)')
                        break
            
            result['num_lines'] = line_count
            result['preview'] = preview_lines
            
            # Si pas d'erreurs critiques, le fichier est valide
            if not missing_columns:
                result['valid'] = True
            
    except UnicodeDecodeError:
        result['errors'].append('Encodage du fichier invalide (utilisez UTF-8)')
    except Exception as e:
        result['errors'].append(f'Erreur de lecture : {str(e)}')
    
    return result


def validate_json_structure(filepath, max_preview_items=10):
    """
    Valide la structure d'un fichier JSON
    
    Args:
        filepath: Chemin du fichier
        max_preview_items: Nombre d'items à prévisualiser
    
    Returns:
        dict: {
            'valid': bool,
            'errors': list,
            'num_items': int,
            'preview': list
        }
    """
    result = {
        'valid': False,
        'errors': [],
        'num_items': 0,
        'preview': []
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Le JSON doit être une liste d'objets
        if not isinstance(data, list):
            result['errors'].append('Le fichier JSON doit contenir une liste d\'objets')
            return result
        
        result['num_items'] = len(data)
        
        # Vérifier les champs requis pour les alerts
        required_fields = ['timestamp', 'zone', 'sensor', 'message', 'severity']
        
        for i, item in enumerate(data):
            if i < max_preview_items:
                result['preview'].append(item)
            
            if not isinstance(item, dict):
                result['errors'].append(f'Item {i+1}: doit être un objet JSON')
                continue
            
            missing_fields = [field for field in required_fields if field not in item]
            if missing_fields and i == 0:  # Vérifier seulement le premier item
                result['errors'].append(f'Champs manquants : {", ".join(missing_fields)}')
        
        # Si pas d'erreurs critiques, le fichier est valide
        if len(result['errors']) == 0:
            result['valid'] = True
        
    except json.JSONDecodeError as e:
        result['errors'].append(f'JSON invalide : {str(e)}')
    except UnicodeDecodeError:
        result['errors'].append('Encodage du fichier invalide (utilisez UTF-8)')
    except Exception as e:
        result['errors'].append(f'Erreur de lecture : {str(e)}')
    
    return result


def validate_file(filepath, file_type):
    """
    Valide un fichier selon son type
    
    Args:
        filepath: Chemin du fichier
        file_type: Type de fichier (csv, json, txt)
    
    Returns:
        dict: Résultat de la validation
    """
    if file_type == 'csv':
        return validate_csv_structure(filepath)
    elif file_type == 'json':
        return validate_json_structure(filepath)
    elif file_type == 'txt':
        # Les fichiers TXT sont acceptés tels quels
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            return {
                'valid': True,
                'errors': [],
                'num_lines': len(lines),
                'preview': lines[:10]
            }
        except Exception as e:
            return {
                'valid': False,
                'errors': [f'Erreur de lecture : {str(e)}'],
                'num_lines': 0,
                'preview': []
            }
    else:
        return {
            'valid': False,
            'errors': [f'Type de fichier non supporté : {file_type}'],
            'num_lines': 0,
            'preview': []
        }
