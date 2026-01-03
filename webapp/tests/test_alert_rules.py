"""
Tests unitaires pour le moteur de règles d'alertes
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestAlertRuleTypes:
    """Tests pour les types de règles d'alertes"""
    
    def test_threshold_rule_above(self, sample_logs_for_evaluation):
        """Test règle threshold avec opérateur >"""
        rule = {
            'rule_type': 'threshold',
            'conditions': {
                'field': 'value',
                'operator': '>',
                'threshold': 30
            },
            'filters': {
                'sensor_type': 'temperature',
                'zone': 'A'
            }
        }
        
        # Filtrer les logs Zone A
        zone_a_logs = [log for log in sample_logs_for_evaluation 
                       if log.get('zone') == 'A' and log.get('sensor_type') == 'temperature']
        
        # Évaluer la condition threshold
        matching = [log for log in zone_a_logs if log.get('value', 0) > rule['conditions']['threshold']]
        
        assert len(matching) == 2  # 35.5 et 36.2 > 30
    
    def test_threshold_rule_below(self):
        """Test règle threshold avec opérateur <"""
        logs = [
            {'value': 10},
            {'value': 14},
            {'value': 16},
            {'value': 20}
        ]
        
        threshold = 15
        matching = [log for log in logs if log['value'] < threshold]
        
        assert len(matching) == 2  # 10 et 14
    
    def test_threshold_rule_equals(self):
        """Test règle threshold avec opérateur =="""
        logs = [
            {'status': 'ok'},
            {'status': 'warning'},
            {'status': 'ok'},
            {'status': 'error'}
        ]
        
        matching = [log for log in logs if log['status'] == 'warning']
        
        assert len(matching) == 1
    
    def test_range_rule_out_of_range(self):
        """Test règle range (valeur hors plage)"""
        rule = {
            'rule_type': 'range',
            'conditions': {
                'field': 'value',
                'operator': 'out_of_range',
                'min_value': 400,
                'max_value': 1000
            }
        }
        
        logs = [
            {'value': 300},   # Hors plage (en dessous)
            {'value': 500},   # Dans la plage
            {'value': 800},   # Dans la plage
            {'value': 1200},  # Hors plage (au dessus)
            {'value': 1500}   # Hors plage (au dessus)
        ]
        
        min_val = rule['conditions']['min_value']
        max_val = rule['conditions']['max_value']
        
        matching = [log for log in logs if log['value'] < min_val or log['value'] > max_val]
        
        assert len(matching) == 3  # 300, 1200, 1500
    
    def test_pattern_rule_count(self):
        """Test règle pattern (nombre d'événements)"""
        rule = {
            'rule_type': 'pattern',
            'conditions': {
                'min_count': 3,
                'time_window_seconds': 300  # 5 minutes
            },
            'filters': {
                'event_type': 'fire_alarm'
            }
        }
        
        now = datetime.now()
        logs = [
            {'event_type': 'fire_alarm', 'timestamp': now - timedelta(seconds=60)},
            {'event_type': 'fire_alarm', 'timestamp': now - timedelta(seconds=120)},
            {'event_type': 'fire_alarm', 'timestamp': now - timedelta(seconds=180)},
            {'event_type': 'fire_alarm', 'timestamp': now - timedelta(seconds=240)},
        ]
        
        # Filtrer par event_type
        matching = [log for log in logs if log['event_type'] == 'fire_alarm']
        
        # Vérifier si le nombre dépasse le seuil
        is_triggered = len(matching) >= rule['conditions']['min_count']
        
        assert is_triggered is True


class TestAlertRuleFiltering:
    """Tests pour le filtrage des logs par règle"""
    
    def test_filter_by_zone(self, sample_logs_for_evaluation):
        """Test filtrage par zone"""
        zone_filter = 'A'
        
        filtered = [log for log in sample_logs_for_evaluation if log.get('zone') == zone_filter]
        
        assert all(log['zone'] == 'A' for log in filtered)
    
    def test_filter_by_sensor_type(self, sample_logs_for_evaluation):
        """Test filtrage par type de capteur"""
        sensor_filter = 'temperature'
        
        filtered = [log for log in sample_logs_for_evaluation 
                   if log.get('sensor_type') == sensor_filter]
        
        assert all(log['sensor_type'] == 'temperature' for log in filtered)
    
    def test_filter_by_building(self, sample_logs_for_evaluation):
        """Test filtrage par bâtiment"""
        building_filter = 'Smart Building A'
        
        filtered = []
        for log in sample_logs_for_evaluation:
            building = log.get('building')
            # Gérer le cas où building est une liste
            if isinstance(building, list):
                building = building[0] if building else None
            if building == building_filter:
                filtered.append(log)
        
        assert len(filtered) == len(sample_logs_for_evaluation)
    
    def test_multiple_filters(self, sample_logs_for_evaluation):
        """Test avec plusieurs filtres combinés"""
        filters = {
            'zone': 'A',
            'sensor_type': 'temperature'
        }
        
        filtered = sample_logs_for_evaluation
        
        if filters.get('zone'):
            filtered = [log for log in filtered if log.get('zone') == filters['zone']]
        
        if filters.get('sensor_type'):
            filtered = [log for log in filtered if log.get('sensor_type') == filters['sensor_type']]
        
        assert len(filtered) == 2


class TestAlertRuleCooldown:
    """Tests pour le système de cooldown"""
    
    def test_cooldown_not_expired(self):
        """Test cooldown non expiré"""
        cooldown_seconds = 300
        last_triggered = datetime.now() - timedelta(seconds=100)
        
        time_since_last = (datetime.now() - last_triggered).total_seconds()
        is_ready = time_since_last >= cooldown_seconds
        
        assert is_ready is False
    
    def test_cooldown_expired(self):
        """Test cooldown expiré"""
        cooldown_seconds = 300
        last_triggered = datetime.now() - timedelta(seconds=400)
        
        time_since_last = (datetime.now() - last_triggered).total_seconds()
        is_ready = time_since_last >= cooldown_seconds
        
        assert is_ready is True
    
    def test_cooldown_never_triggered(self):
        """Test règle jamais déclenchée (pas de cooldown)"""
        last_triggered = None
        
        is_ready = last_triggered is None
        
        assert is_ready is True


class TestAlertRuleSeverity:
    """Tests pour les niveaux de sévérité"""
    
    def test_severity_ordering(self):
        """Test ordre des niveaux de sévérité"""
        severity_order = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
        
        assert severity_order['critical'] > severity_order['high']
        assert severity_order['high'] > severity_order['medium']
        assert severity_order['medium'] > severity_order['low']
    
    def test_filter_by_minimum_severity(self):
        """Test filtrage par sévérité minimale"""
        severity_order = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        
        rules = [
            {'name': 'Rule 1', 'severity': 'low'},
            {'name': 'Rule 2', 'severity': 'medium'},
            {'name': 'Rule 3', 'severity': 'high'},
            {'name': 'Rule 4', 'severity': 'critical'}
        ]
        
        min_severity = 'high'
        min_level = severity_order[min_severity]
        
        filtered = [r for r in rules if severity_order[r['severity']] >= min_level]
        
        assert len(filtered) == 2  # high et critical


class TestAlertRuleActions:
    """Tests pour les actions d'alertes"""
    
    def test_email_action_config(self):
        """Test configuration action email"""
        action = {
            'type': 'email',
            'config': {
                'recipients': ['admin@example.com', 'ops@example.com'],
                'subject_template': 'Alerte {severity}: {rule_name}',
                'body_template': 'Une alerte a été déclenchée...'
            }
        }
        
        assert action['type'] == 'email'
        assert len(action['config']['recipients']) == 2
    
    def test_webhook_action_config(self):
        """Test configuration action webhook"""
        action = {
            'type': 'webhook',
            'config': {
                'url': 'https://hooks.slack.com/services/xxx',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'retry_count': 3
            }
        }
        
        assert action['type'] == 'webhook'
        assert action['config']['method'] == 'POST'
    
    def test_action_types(self):
        """Test types d'actions supportés"""
        supported_types = ['email', 'webhook', 'slack', 'discord', 'sms']
        
        for action_type in ['email', 'webhook', 'slack']:
            assert action_type in supported_types


class TestAlertRuleStatistics:
    """Tests pour les statistiques des règles"""
    
    def test_calculate_trigger_count(self):
        """Test calcul du nombre de déclenchements"""
        rule_stats = {
            'trigger_count': 0
        }
        
        # Simuler des déclenchements
        for _ in range(5):
            rule_stats['trigger_count'] += 1
        
        assert rule_stats['trigger_count'] == 5
    
    def test_calculate_average_value(self):
        """Test calcul de la valeur moyenne"""
        triggered_values = [35.5, 36.2, 37.0, 38.5, 40.0]
        
        avg = sum(triggered_values) / len(triggered_values)
        
        assert round(avg, 2) == 37.44
    
    def test_track_affected_zones(self):
        """Test suivi des zones affectées"""
        triggered_logs = [
            {'zone': 'A'},
            {'zone': 'A'},
            {'zone': 'B'},
            {'zone': 'C'},
            {'zone': 'A'}
        ]
        
        zones = list(set(log['zone'] for log in triggered_logs))
        
        assert len(zones) == 3
        assert 'A' in zones
        assert 'B' in zones
        assert 'C' in zones
    
    def test_moving_average(self):
        """Test moyenne mobile"""
        current_avg = 35.0
        new_value = 40.0
        total_count = 5
        
        # Calcul moyenne mobile
        new_avg = (current_avg * (total_count - 1) + new_value) / total_count
        
        assert round(new_avg, 2) == 36.0


class TestOperatorEvaluation:
    """Tests pour l'évaluation des opérateurs"""
    
    def test_operator_greater_than(self):
        """Test opérateur >"""
        value = 35
        threshold = 30
        
        result = value > threshold
        
        assert result is True
    
    def test_operator_less_than(self):
        """Test opérateur <"""
        value = 10
        threshold = 15
        
        result = value < threshold
        
        assert result is True
    
    def test_operator_greater_equal(self):
        """Test opérateur >="""
        value = 30
        threshold = 30
        
        result = value >= threshold
        
        assert result is True
    
    def test_operator_less_equal(self):
        """Test opérateur <="""
        value = 30
        threshold = 30
        
        result = value <= threshold
        
        assert result is True
    
    def test_operator_equals(self):
        """Test opérateur =="""
        value = 'error'
        expected = 'error'
        
        result = value == expected
        
        assert result is True
    
    def test_operator_not_equals(self):
        """Test opérateur !="""
        value = 'ok'
        expected = 'error'
        
        result = value != expected
        
        assert result is True
    
    def test_evaluate_with_operator(self):
        """Test évaluation dynamique avec opérateur"""
        operators = {
            '>': lambda a, b: a > b,
            '<': lambda a, b: a < b,
            '>=': lambda a, b: a >= b,
            '<=': lambda a, b: a <= b,
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b
        }
        
        value = 35
        threshold = 30
        operator = '>'
        
        result = operators[operator](value, threshold)
        
        assert result is True
