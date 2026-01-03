"""
Générateur de données de test pour IoT Smart Building
Génère des fichiers CSV (capteurs) et JSON (alertes) avec données réalistes
"""
import csv
import json
import random
import os
from datetime import datetime, timedelta
from faker import Faker

# Initialisation
fake = Faker('fr_FR')
random.seed(42)  # Pour reproductibilité

# Configuration
OUTPUT_DIR = '../data/uploads'
TEST_DATA_DIR = '../data/test-data'

# Zones du bâtiment (3 étages x 3 zones)
ZONES = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']

# Types de capteurs
SENSOR_TYPES = {
    'temperature': {
        'min': 10,
        'max': 35,
        'normal_min': 18,
        'normal_max': 25,
        'unit': '°C',
        'anomaly_threshold_low': 15,
        'anomaly_threshold_high': 30
    },
    'humidity': {
        'min': 20,
        'max': 90,
        'normal_min': 40,
        'normal_max': 70,
        'unit': '%',
        'anomaly_threshold_low': 30,
        'anomaly_threshold_high': 80
    },
    'luminosity': {
        'min': 0,
        'max': 1000,
        'normal_min': 200,
        'normal_max': 800,
        'unit': 'lux',
        'anomaly_threshold_low': 50,
        'anomaly_threshold_high': 950
    },
    'co2': {
        'min': 300,
        'max': 2000,
        'normal_min': 400,
        'normal_max': 1000,
        'unit': 'ppm',
        'anomaly_threshold_low': 350,
        'anomaly_threshold_high': 1200
    }
}

# Niveaux de sévérité pour alertes
SEVERITY_LEVELS = ['low', 'medium', 'high', 'critical']

# Types d'alertes
ALERT_TYPES = [
    'temperature_high',
    'temperature_low',
    'humidity_high',
    'humidity_low',
    'co2_high',
    'equipment_failure',
    'power_outage',
    'sensor_malfunction'
]


def generate_sensor_value(sensor_type, force_anomaly=False):
    """Génère une valeur de capteur réaliste"""
    config = SENSOR_TYPES[sensor_type]
    
    if force_anomaly or random.random() < 0.1:  # 10% de chance d'anomalie
        # Valeur anormale (en dehors des seuils normaux)
        if random.random() < 0.5:
            value = random.uniform(config['min'], config['normal_min'])
        else:
            value = random.uniform(config['normal_max'], config['max'])
    else:
        # Valeur normale
        value = random.uniform(config['normal_min'], config['normal_max'])
    
    return round(value, 1)


def generate_sensor_logs(num_logs=10000, filename='sensors_test.csv'):
    """
    Génère des logs de capteurs au format CSV
    Format: timestamp,zone,sensor_type,sensor_id,value,unit,status
    """
    print(f"📊 Génération de {num_logs} logs de capteurs...")
    
    # Créer les répertoires si nécessaire
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    
    filepath = os.path.join(OUTPUT_DIR, filename)
    test_filepath = os.path.join(TEST_DATA_DIR, filename)
    
    logs = []
    sensor_id_base = 1000
    
    # Générer les logs sur les 7 derniers jours
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    for i in range(num_logs):
        # Timestamp aléatoire dans les 7 derniers jours
        random_seconds = random.randint(0, int((end_time - start_time).total_seconds()))
        timestamp = start_time + timedelta(seconds=random_seconds)
        
        # Zone aléatoire
        zone = random.choice(ZONES)
        
        # Type de capteur aléatoire
        sensor_type = random.choice(list(SENSOR_TYPES.keys()))
        
        # ID capteur (chaque zone a 10 capteurs par type)
        sensor_id = sensor_id_base + ZONES.index(zone) * 40 + \
                   list(SENSOR_TYPES.keys()).index(sensor_type) * 10 + \
                   random.randint(0, 9)
        
        # Valeur du capteur
        value = generate_sensor_value(sensor_type)
        
        # Unité
        unit = SENSOR_TYPES[sensor_type]['unit']
        
        # Statut (basé sur la valeur)
        config = SENSOR_TYPES[sensor_type]
        if value < config['anomaly_threshold_low'] or value > config['anomaly_threshold_high']:
            status = 'warning'
        else:
            status = 'ok'
        
        logs.append({
            'timestamp': timestamp.isoformat(),
            'zone': zone,
            'sensor_type': sensor_type,
            'sensor_id': sensor_id,
            'value': value,
            'unit': unit,
            'status': status
        })
    
    # Trier par timestamp
    logs.sort(key=lambda x: x['timestamp'])
    
    # Écrire dans le fichier CSV
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'zone', 'sensor_type', 'sensor_id', 'value', 'unit', 'status'])
        writer.writeheader()
        writer.writerows(logs)
    
    # Copier dans test-data
    with open(test_filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'zone', 'sensor_type', 'sensor_id', 'value', 'unit', 'status'])
        writer.writeheader()
        writer.writerows(logs)
    
    print(f"✅ {len(logs)} logs générés")
    print(f"   - Fichier principal: {filepath}")
    print(f"   - Copie test: {test_filepath}")
    
    # Statistiques
    warnings = sum(1 for log in logs if log['status'] == 'warning')
    print(f"   - Logs normaux: {len(logs) - warnings}")
    print(f"   - Logs avec warning: {warnings}")
    
    return logs


def generate_alerts(num_alerts=1000, filename='alerts_test.json'):
    """
    Génère des alertes au format JSON
    Format: {timestamp, sensor, location, alert_type, severity, value, message}
    """
    print(f"\n🚨 Génération de {num_alerts} alertes...")
    
    filepath = os.path.join(OUTPUT_DIR, filename)
    test_filepath = os.path.join(TEST_DATA_DIR, filename)
    
    alerts = []
    
    # Générer les alertes sur les 7 derniers jours
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    for i in range(num_alerts):
        # Timestamp aléatoire
        random_seconds = random.randint(0, int((end_time - start_time).total_seconds()))
        timestamp = start_time + timedelta(seconds=random_seconds)
        
        # Zone
        zone = random.choice(ZONES)
        
        # Type d'alerte
        alert_type = random.choice(ALERT_TYPES)
        
        # Sévérité (plus probable d'avoir low/medium que high/critical)
        severity_weights = [0.4, 0.35, 0.2, 0.05]
        severity = random.choices(SEVERITY_LEVELS, weights=severity_weights)[0]
        
        # Sensor ID
        sensor_id = 1000 + random.randint(0, 360)
        
        # Valeur (selon le type d'alerte)
        if 'temperature' in alert_type:
            if 'high' in alert_type:
                value = random.uniform(30, 40)
            else:
                value = random.uniform(5, 15)
        elif 'humidity' in alert_type:
            if 'high' in alert_type:
                value = random.uniform(80, 95)
            else:
                value = random.uniform(15, 30)
        elif 'co2' in alert_type:
            value = random.uniform(1200, 2000)
        else:
            value = random.uniform(0, 100)
        
        # Message
        messages = {
            'temperature_high': f"Température élevée détectée dans la zone {zone}",
            'temperature_low': f"Température basse détectée dans la zone {zone}",
            'humidity_high': f"Humidité élevée dans la zone {zone}",
            'humidity_low': f"Humidité basse dans la zone {zone}",
            'co2_high': f"Niveau de CO2 critique dans la zone {zone}",
            'equipment_failure': f"Panne d'équipement détectée dans la zone {zone}",
            'power_outage': f"Coupure de courant dans la zone {zone}",
            'sensor_malfunction': f"Dysfonctionnement capteur dans la zone {zone}"
        }
        
        alert = {
            'timestamp': timestamp.isoformat() + 'Z',
            'sensor': str(sensor_id),
            'location': zone,
            'alert_type': alert_type,
            'severity': severity,
            'value': round(value, 2),
            'message': messages.get(alert_type, f"Alerte dans la zone {zone}"),
            'acknowledged': random.random() > 0.7,  # 30% déjà acquittées
            'building': 'Smart Building A'
        }
        
        alerts.append(alert)
    
    # Trier par timestamp
    alerts.sort(key=lambda x: x['timestamp'])
    
    # Écrire dans le fichier JSON (une alerte par ligne pour Logstash)
    with open(filepath, 'w', encoding='utf-8') as f:
        for alert in alerts:
            f.write(json.dumps(alert) + '\n')
    
    # Copier dans test-data
    with open(test_filepath, 'w', encoding='utf-8') as f:
        for alert in alerts:
            f.write(json.dumps(alert) + '\n')
    
    print(f"✅ {len(alerts)} alertes générées")
    print(f"   - Fichier principal: {filepath}")
    print(f"   - Copie test: {test_filepath}")
    
    # Statistiques par sévérité
    for severity in SEVERITY_LEVELS:
        count = sum(1 for a in alerts if a['severity'] == severity)
        print(f"   - {severity.capitalize()}: {count}")
    
    return alerts


def generate_sample_data():
    """Génère un petit échantillon de données pour tests rapides"""
    print("\n📦 Génération d'échantillons de données...")
    
    # Petit fichier CSV (100 logs)
    generate_sensor_logs(100, 'sensors_sample.csv')
    
    # Petit fichier JSON (20 alertes)
    generate_alerts(20, 'alerts_sample.json')


def main():
    """Fonction principale"""
    print("=" * 60)
    print("🏢 IoT Smart Building - Générateur de données de test")
    print("=" * 60)
    
    # Générer les données complètes
    print("\n📋 Génération des données complètes...")
    sensor_logs = generate_sensor_logs(10000, 'sensors_test.csv')
    alerts = generate_alerts(1000, 'alerts_test.json')
    
    # Générer des échantillons
    generate_sample_data()
    
    print("\n" + "=" * 60)
    print("✅ Génération terminée avec succès!")
    print("=" * 60)
    print(f"\n📂 Fichiers créés dans:")
    print(f"   - {OUTPUT_DIR}/ (surveillé par Logstash)")
    print(f"   - {TEST_DATA_DIR}/ (sauvegarde)")
    
    print("\n💡 Prochaines étapes:")
    print("   1. Logstash va traiter automatiquement les fichiers")
    print("   2. Vérifier dans Kibana: http://localhost:5601")
    print("   3. Interroger l'API: http://localhost:8000/api/v1/stats")
    print("   4. Créer des visualisations dans Kibana")
    
    print("\n🔍 Commandes utiles:")
    print("   - Logs Logstash: docker compose logs -f logstash")
    print("   - Query ES: curl 'localhost:9200/logs-iot-*/_search?pretty&size=5'")
    print("   - Stats ES: curl 'localhost:9200/_cat/indices?v'")


if __name__ == '__main__':
    # Créer les répertoires si nécessaire
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    
    main()
