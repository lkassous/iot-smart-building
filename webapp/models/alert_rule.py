"""
Modèle MongoDB pour les règles d'alertes intelligentes
"""
from datetime import datetime
from bson import ObjectId


class AlertRule:
    """
    Représente une règle d'alerte configurable
    
    Types de règles supportés:
    - threshold: Comparaison simple (value > seuil)
    - range: Valeur hors plage (value < min OR value > max)
    - trend: Variation anormale (delta > seuil sur période)
    - pattern: Détection de motifs (N events dans X minutes)
    """
    
    RULE_TYPES = ['threshold', 'range', 'trend', 'pattern']
    OPERATORS = ['>', '<', '>=', '<=', '==', '!=']
    SEVERITIES = ['low', 'medium', 'high', 'critical']
    ACTION_TYPES = ['email', 'webhook', 'slack', 'discord', 'sms']
    
    @staticmethod
    def create_schema():
        """Retourne le schéma MongoDB pour une règle d'alerte"""
        return {
            '_id': ObjectId,
            'name': str,                    # Nom de la règle
            'description': str,             # Description détaillée
            'enabled': bool,                # Active/Inactive
            'rule_type': str,               # threshold, range, trend, pattern
            
            # Conditions de déclenchement
            'conditions': {
                'field': str,               # Champ à surveiller (value, temperature, etc.)
                'operator': str,            # >, <, >=, <=, ==, !=
                'threshold': float,         # Seuil pour threshold
                'min_value': float,         # Min pour range (optionnel)
                'max_value': float,         # Max pour range (optionnel)
                'time_window': int,         # Fenêtre temporelle en secondes (pattern/trend)
                'event_count': int,         # Nombre d'events pour pattern (optionnel)
                
                # Filtres supplémentaires
                'filters': {
                    'zone': [str],          # Zones concernées (ex: ['A', 'B', 'C'])
                    'sensor_type': [str],   # Types de capteurs (ex: ['temperature', 'co2'])
                    'status': [str],        # Statuts (ex: ['critical', 'high'])
                    'building': str,        # Bâtiment (ex: 'Smart Building A')
                }
            },
            
            # Actions à déclencher
            'actions': [
                {
                    'type': str,            # email, webhook, slack, discord, sms
                    'config': {
                        # Pour email
                        'recipients': [str],
                        'subject': str,
                        'template': str,
                        
                        # Pour webhook/slack/discord
                        'url': str,
                        'method': str,      # POST, PUT
                        'headers': dict,
                        'payload_template': str,
                        
                        # Pour SMS (Twilio)
                        'phone_numbers': [str],
                    },
                    'enabled': bool
                }
            ],
            
            # Configuration de notification
            'severity': str,                # low, medium, high, critical
            'priority': int,                # 1-10 (1=highest)
            'cooldown': int,                # Temps en secondes avant nouvelle alerte
            'escalation': {
                'enabled': bool,
                'after': int,               # Temps en secondes avant escalade
                'to_severity': str,         # Nouvelle sévérité après escalade
                'additional_actions': [str] # Actions supplémentaires
            },
            
            # Métadonnées
            'created_by': str,              # Username du créateur
            'created_at': datetime,
            'updated_at': datetime,
            'last_triggered': datetime,     # Dernière fois déclenchée
            'trigger_count': int,           # Nombre de déclenchements
            
            # Statistiques
            'stats': {
                'total_triggers': int,
                'last_7_days_triggers': int,
                'avg_value_on_trigger': float,
                'zones_affected': [str]
            }
        }
    
    @staticmethod
    def default_rule():
        """Retourne une règle par défaut pour template"""
        return {
            'name': 'Nouvelle Règle',
            'description': '',
            'enabled': True,
            'rule_type': 'threshold',
            'conditions': {
                'field': 'value',
                'operator': '>',
                'threshold': 0,
                'filters': {
                    'zone': [],
                    'sensor_type': [],
                    'status': [],
                    'building': 'Smart Building A'
                }
            },
            'actions': [
                {
                    'type': 'email',
                    'config': {
                        'recipients': ['admin@smartbuilding.com'],
                        'subject': 'Alerte: {rule_name}',
                        'template': 'alert_notification'
                    },
                    'enabled': True
                }
            ],
            'severity': 'medium',
            'priority': 5,
            'cooldown': 300,  # 5 minutes
            'escalation': {
                'enabled': False,
                'after': 1800,  # 30 minutes
                'to_severity': 'high',
                'additional_actions': []
            },
            'created_by': 'system',
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'last_triggered': None,
            'trigger_count': 0,
            'stats': {
                'total_triggers': 0,
                'last_7_days_triggers': 0,
                'avg_value_on_trigger': 0,
                'zones_affected': []
            }
        }
    
    @staticmethod
    def validate_rule(rule):
        """
        Valide une règle d'alerte
        
        Args:
            rule: Dictionnaire représentant la règle
            
        Returns:
            tuple: (is_valid, error_message)
        """
        # Vérifications obligatoires
        if not rule.get('name'):
            return False, "Le nom de la règle est obligatoire"
        
        if rule.get('rule_type') not in AlertRule.RULE_TYPES:
            return False, f"Type de règle invalide. Doit être: {', '.join(AlertRule.RULE_TYPES)}"
        
        conditions = rule.get('conditions', {})
        if not conditions.get('field'):
            return False, "Le champ à surveiller est obligatoire"
        
        # Validation selon le type de règle
        if rule['rule_type'] == 'threshold':
            if not conditions.get('operator') or conditions['operator'] not in AlertRule.OPERATORS:
                return False, f"Opérateur invalide. Doit être: {', '.join(AlertRule.OPERATORS)}"
            if conditions.get('threshold') is None:
                return False, "Le seuil est obligatoire pour une règle threshold"
        
        elif rule['rule_type'] == 'range':
            if conditions.get('min_value') is None or conditions.get('max_value') is None:
                return False, "min_value et max_value sont obligatoires pour une règle range"
        
        elif rule['rule_type'] in ['trend', 'pattern']:
            if not conditions.get('time_window'):
                return False, "time_window est obligatoire pour les règles trend/pattern"
        
        # Validation des actions (optionnelles, mais si présentes, doivent être valides)
        actions = rule.get('actions', [])
        for action in actions:
            if action.get('type') not in AlertRule.ACTION_TYPES:
                return False, f"Type d'action invalide: {action.get('type')}"
            
            if action['type'] == 'email':
                if not action.get('config', {}).get('recipients'):
                    return False, "Les destinataires email sont obligatoires"
            
            elif action['type'] in ['webhook', 'slack', 'discord']:
                config = action.get('config', {})
                if not config.get('url') and not config.get('webhook_url'):
                    return False, f"L'URL est obligatoire pour {action['type']}"
        
        # Validation de la sévérité
        if rule.get('severity') and rule['severity'] not in AlertRule.SEVERITIES:
            return False, f"Sévérité invalide. Doit être: {', '.join(AlertRule.SEVERITIES)}"
        
        return True, ""
    
    @staticmethod
    def example_rules():
        """Retourne des exemples de règles pour démonstration"""
        return [
            # Règle 1: Température critique
            {
                'name': 'Température Critique - Zone A',
                'description': 'Alerte si température > 35°C dans la zone A',
                'enabled': True,
                'rule_type': 'threshold',
                'conditions': {
                    'field': 'value',
                    'operator': '>',
                    'threshold': 35.0,
                    'filters': {
                        'zone': ['A'],
                        'sensor_type': ['temperature'],
                        'status': [],
                        'building': 'Smart Building A'
                    }
                },
                'actions': [
                    {
                        'type': 'email',
                        'config': {
                            'recipients': ['admin@smartbuilding.com', 'tech@smartbuilding.com'],
                            'subject': '🔥 Température Critique - Zone A',
                            'template': 'critical_temperature'
                        },
                        'enabled': True
                    },
                    {
                        'type': 'webhook',
                        'config': {
                            'url': 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL',
                            'method': 'POST',
                            'headers': {'Content-Type': 'application/json'},
                            'payload_template': '{"text": "🔥 Alerte: Température {value}°C en Zone {zone}"}'
                        },
                        'enabled': False
                    }
                ],
                'severity': 'critical',
                'priority': 1,
                'cooldown': 600,  # 10 minutes
                'escalation': {
                    'enabled': True,
                    'after': 1800,  # 30 minutes
                    'to_severity': 'critical',
                    'additional_actions': ['sms']
                },
                'created_by': 'admin',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'last_triggered': None,
                'trigger_count': 0,
                'stats': {
                    'total_triggers': 0,
                    'last_7_days_triggers': 0,
                    'avg_value_on_trigger': 0,
                    'zones_affected': []
                }
            },
            
            # Règle 2: CO2 élevé - Plage invalide
            {
                'name': 'CO2 Dangereux - Toutes Zones',
                'description': 'Alerte si CO2 hors plage normale (400-1000 ppm)',
                'enabled': True,
                'rule_type': 'range',
                'conditions': {
                    'field': 'value',
                    'operator': 'out_of_range',
                    'min_value': 400.0,
                    'max_value': 1000.0,
                    'filters': {
                        'zone': [],  # Toutes zones
                        'sensor_type': ['co2', 'co2_high'],
                        'status': [],
                        'building': 'Smart Building A'
                    }
                },
                'actions': [
                    {
                        'type': 'email',
                        'config': {
                            'recipients': ['maintenance@smartbuilding.com'],
                            'subject': '⚠️ Niveau CO2 Anormal',
                            'template': 'co2_alert'
                        },
                        'enabled': True
                    }
                ],
                'severity': 'high',
                'priority': 2,
                'cooldown': 900,  # 15 minutes
                'escalation': {
                    'enabled': False,
                    'after': 3600,
                    'to_severity': 'critical',
                    'additional_actions': []
                },
                'created_by': 'admin',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'last_triggered': None,
                'trigger_count': 0,
                'stats': {
                    'total_triggers': 0,
                    'last_7_days_triggers': 0,
                    'avg_value_on_trigger': 0,
                    'zones_affected': []
                }
            },
            
            # Règle 3: Pattern - Alarmes incendie multiples
            {
                'name': 'Alarmes Incendie Multiples',
                'description': 'Alerte si 3+ alarmes incendie en 5 minutes',
                'enabled': True,
                'rule_type': 'pattern',
                'conditions': {
                    'field': 'sensor_type',
                    'operator': '==',
                    'threshold': 'fire_alarm',
                    'time_window': 300,  # 5 minutes
                    'event_count': 3,
                    'filters': {
                        'zone': [],
                        'sensor_type': ['fire_alarm'],
                        'status': ['critical'],
                        'building': 'Smart Building A'
                    }
                },
                'actions': [
                    {
                        'type': 'email',
                        'config': {
                            'recipients': ['emergency@smartbuilding.com', 'security@smartbuilding.com'],
                            'subject': '🚨 URGENCE - Alarmes Incendie Multiples',
                            'template': 'fire_emergency'
                        },
                        'enabled': True
                    }
                ],
                'severity': 'critical',
                'priority': 1,
                'cooldown': 60,  # 1 minute seulement
                'escalation': {
                    'enabled': True,
                    'after': 120,  # 2 minutes
                    'to_severity': 'critical',
                    'additional_actions': ['sms']
                },
                'created_by': 'security',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'last_triggered': None,
                'trigger_count': 0,
                'stats': {
                    'total_triggers': 0,
                    'last_7_days_triggers': 0,
                    'avg_value_on_trigger': 0,
                    'zones_affected': []
                }
            }
        ]
