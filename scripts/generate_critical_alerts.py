#!/usr/bin/env python3
"""
Génère des alertes critiques en temps réel pour tester le système
"""
import json
import random
from datetime import datetime
import os

def generate_critical_alerts(count=10):
    """Génère des alertes critiques avec timestamp actuel"""
    
    zones = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
    alert_types = [
        {
            'sensor_type': 'temperature_high',
            'severity': 'critical',
            'status': 'critical',
            'value_range': (40, 50),
            'unit': '°C',
            'message': 'Température critique détectée dans la zone {}'
        },
        {
            'sensor_type': 'co2_high',
            'severity': 'critical',
            'status': 'critical',
            'value_range': (2000, 3000),
            'unit': 'ppm',
            'message': 'Niveau de CO2 dangereux dans la zone {}'
        },
        {
            'sensor_type': 'fire_alarm',
            'severity': 'critical',
            'status': 'critical',
            'value_range': (1, 1),
            'unit': None,
            'message': '🔥 ALARME INCENDIE - Zone {}'
        },
        {
            'sensor_type': 'humidity_high',
            'severity': 'high',
            'status': 'high',
            'value_range': (85, 95),
            'unit': '%',
            'message': 'Humidité élevée dans la zone {}'
        }
    ]
    
    alerts = []
    timestamp = datetime.now().isoformat()
    
    for i in range(count):
        zone = random.choice(zones)
        alert_type = random.choice(alert_types)
        sensor_id = random.randint(5000, 5999)
        
        value = round(random.uniform(*alert_type['value_range']), 2)
        
        alert = {
            "@timestamp": timestamp,
            "timestamp": timestamp,
            "zone": zone,
            "sensor_type": alert_type['sensor_type'],
            "sensor_id": f"SENSOR-{sensor_id}",
            "value": value,
            "unit": alert_type['unit'],
            "severity": alert_type['severity'],
            "status": alert_type['status'],
            "message": alert_type['message'].format(zone),
            "building": "Smart Building A",
            "source_type": "alert"
        }
        
        alerts.append(alert)
    
    return alerts


def save_to_json(alerts, output_dir='./data/uploads'):
    """Sauvegarde les alertes au format JSON pour ingestion Logstash"""
    
    # Créer le répertoire s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"critical_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        for alert in alerts:
            json.dump(alert, f)
            f.write('\n')  # NDJSON format pour Logstash
    
    print(f"✅ {len(alerts)} alertes critiques générées dans {filepath}")
    print(f"\n📋 Échantillons:")
    for alert in alerts[:3]:
        print(f"  - {alert['zone']} | {alert['severity']} | {alert['message']}")
    
    return filepath


if __name__ == '__main__':
    alerts = generate_critical_alerts(count=15)
    save_to_json(alerts)
