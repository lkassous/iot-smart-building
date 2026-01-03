#!/usr/bin/env python3
"""
Script pour initialiser des règles d'alertes par défaut dans MongoDB
"""
import sys
import os

# Ajouter le chemin parent pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import mongo_client
from utils.alert_rules_manager import AlertRulesManager
from models.alert_rule import AlertRule


def init_default_rules():
    """Initialise les règles d'alertes par défaut"""
    
    # Initialiser le gestionnaire de règles
    rules_manager = AlertRulesManager(mongo_client.iot_smart_building)
    
    print("🔧 Initialisation des règles d'alertes par défaut...\n")
    
    # Récupérer les exemples de règles
    example_rules = AlertRule.example_rules()
    
    success_count = 0
    error_count = 0
    
    for rule in example_rules:
        success, message, rule_id = rules_manager.create_rule(rule)
        
        if success:
            print(f"✅ Règle créée: {rule['name']}")
            print(f"   ID: {rule_id}")
            print(f"   Type: {rule['rule_type']}")
            print(f"   Sévérité: {rule['severity']}")
            print(f"   Actions: {', '.join([a['type'] for a in rule['actions']])}")
            print()
            success_count += 1
        else:
            print(f"❌ Erreur: {message}")
            print(f"   Règle: {rule['name']}")
            print()
            error_count += 1
    
    print("=" * 60)
    print(f"✅ {success_count} règle(s) créée(s)")
    print(f"❌ {error_count} erreur(s)")
    print("=" * 60)
    
    # Afficher les statistiques
    stats = rules_manager.get_rules_stats()
    print("\n📊 Statistiques des règles:")
    print(f"   Total: {stats.get('total_rules', 0)}")
    print(f"   Actives: {stats.get('enabled_rules', 0)}")
    print(f"   Désactivées: {stats.get('disabled_rules', 0)}")
    
    print("\n   Par sévérité:")
    for severity, count in stats.get('by_severity', {}).items():
        print(f"   - {severity}: {count}")


if __name__ == '__main__':
    try:
        init_default_rules()
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
