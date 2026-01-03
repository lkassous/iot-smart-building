#!/usr/bin/env python3
"""
Script d'installation des index templates Elasticsearch
pour le projet IoT Smart Building
"""

import json
import requests
import os
from pathlib import Path

ES_HOST = os.getenv('ELASTICSEARCH_HOST', 'http://localhost:9200')
MAPPINGS_DIR = Path(__file__).parent.parent / 'elasticsearch' / 'mappings'

def install_template(template_name: str, template_file: Path):
    """Installe un template dans Elasticsearch"""
    print(f"\n📦 Installation du template: {template_name}")
    
    # Lire le fichier template
    with open(template_file, 'r') as f:
        template_data = json.load(f)
    
    # Supprimer data_stream si présent (incompatible avec index réguliers)
    if 'data_stream' in template_data:
        del template_data['data_stream']
        print("   ⚠️  Suppression de 'data_stream' (non compatible)")
    
    # Envoyer à Elasticsearch
    url = f"{ES_HOST}/_index_template/{template_name}"
    response = requests.put(
        url,
        headers={'Content-Type': 'application/json'},
        json=template_data
    )
    
    if response.status_code == 200:
        print(f"   ✅ Template installé avec succès!")
        return True
    else:
        print(f"   ❌ Erreur: {response.status_code}")
        print(f"   {response.text}")
        return False

def install_ilm_policy():
    """Installe la politique ILM pour la gestion du cycle de vie des index"""
    print("\n📅 Installation de la politique ILM: logs-iot-policy")
    
    ilm_policy = {
        "policy": {
            "phases": {
                "hot": {
                    "min_age": "0ms",
                    "actions": {
                        "rollover": {
                            "max_age": "7d",
                            "max_size": "50gb"
                        }
                    }
                },
                "warm": {
                    "min_age": "7d",
                    "actions": {
                        "shrink": {
                            "number_of_shards": 1
                        },
                        "forcemerge": {
                            "max_num_segments": 1
                        }
                    }
                },
                "delete": {
                    "min_age": "30d",
                    "actions": {
                        "delete": {}
                    }
                }
            }
        }
    }
    
    url = f"{ES_HOST}/_ilm/policy/logs-iot-policy"
    response = requests.put(
        url,
        headers={'Content-Type': 'application/json'},
        json=ilm_policy
    )
    
    if response.status_code == 200:
        print("   ✅ Politique ILM installée!")
        return True
    else:
        print(f"   ❌ Erreur: {response.status_code}")
        print(f"   {response.text}")
        return False

def check_elasticsearch():
    """Vérifie que Elasticsearch est accessible"""
    print(f"🔍 Vérification d'Elasticsearch sur {ES_HOST}...")
    try:
        response = requests.get(f"{ES_HOST}/_cluster/health")
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Cluster: {health['cluster_name']} - Status: {health['status']}")
            return True
    except requests.exceptions.ConnectionError:
        pass
    
    print("   ❌ Elasticsearch non accessible!")
    return False

def list_templates():
    """Liste les templates installés"""
    print("\n📋 Templates actuellement installés:")
    
    response = requests.get(f"{ES_HOST}/_index_template")
    if response.status_code == 200:
        templates = response.json().get('index_templates', [])
        if templates:
            for t in templates:
                name = t.get('name', 'unknown')
                patterns = t.get('index_template', {}).get('index_patterns', [])
                print(f"   - {name}: {patterns}")
        else:
            print("   (aucun template personnalisé)")
    return True

def main():
    print("=" * 60)
    print("🚀 INSTALLATION DES INDEX TEMPLATES ELASTICSEARCH")
    print("   IoT Smart Building - Monitoring Platform")
    print("=" * 60)
    
    # Vérifier ES
    if not check_elasticsearch():
        print("\n❌ Impossible de continuer sans Elasticsearch")
        return False
    
    # Installer la politique ILM (optionnel, ignore les erreurs)
    try:
        install_ilm_policy()
    except Exception as e:
        print(f"   ⚠️ ILM non disponible: {e}")
    
    # Installer les templates
    templates = [
        ('logs-iot-sensors-template', MAPPINGS_DIR / 'sensors-template.json'),
        ('logs-iot-alerts-template', MAPPINGS_DIR / 'alerts-template.json')
    ]
    
    success_count = 0
    for name, path in templates:
        if path.exists():
            if install_template(name, path):
                success_count += 1
        else:
            print(f"\n⚠️ Fichier non trouvé: {path}")
    
    # Lister les templates
    list_templates()
    
    # Résumé
    print("\n" + "=" * 60)
    print(f"📊 RÉSUMÉ: {success_count}/{len(templates)} templates installés")
    print("=" * 60)
    
    return success_count == len(templates)

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
