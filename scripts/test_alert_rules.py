#!/usr/bin/env python3
"""
Script de test pour déclencher les règles d'alertes
Génère des données ciblées qui correspondent aux critères des règles
"""
import json
from datetime import datetime
import os


def generate_rule_trigger_data():
    """Génère des données pour déclencher chaque règle"""
    
    alerts = []
    timestamp = datetime.now().isoformat()
    
    print("🎯 Génération de données pour tester les règles d'alertes...\n")
    
    # =====================================================
    # RÈGLE 1: Température Critique - Zone A (value > 35°C)
    # =====================================================
    print("1️⃣  Règle: Température Critique - Zone A")
    print("   Condition: temperature > 35°C dans Zone A")
    print("   Génération: 5 logs de température entre 36-45°C en Zone A\n")
    
    for i in range(5):
        temp_value = 36.0 + (i * 2)  # 36, 38, 40, 42, 44°C
        alert = {
            "@timestamp": timestamp,
            "timestamp": timestamp,
            "zone": "A",
            "sensor_type": "temperature",
            "sensor_id": f"TEMP-A-{100+i}",
            "value": temp_value,
            "unit": "°C",
            "severity": "critical",
            "status": "critical",
            "message": f"Température critique {temp_value}°C détectée dans la zone A",
            "building": "Smart Building A",
            "source_type": "sensor"
        }
        alerts.append(alert)
        print(f"   ✅ {temp_value}°C en Zone A")
    
    print()
    
    # =====================================================
    # RÈGLE 2: Alarmes Incendie Multiples (3+ en 5min)
    # =====================================================
    print("2️⃣  Règle: Alarmes Incendie Multiples")
    print("   Condition: 3+ alarmes incendie en 5 minutes")
    print("   Génération: 4 alarmes incendie dans différentes zones\n")
    
    fire_zones = ['B', 'C', 'D', 'E']
    for i, zone in enumerate(fire_zones):
        alert = {
            "@timestamp": timestamp,
            "timestamp": timestamp,
            "zone": zone,
            "sensor_type": "fire_alarm",
            "sensor_id": f"FIRE-{zone}-{200+i}",
            "value": 1.0,
            "unit": None,
            "severity": "critical",
            "status": "critical",
            "message": f"🔥 ALARME INCENDIE - Zone {zone}",
            "building": "Smart Building A",
            "source_type": "alert"
        }
        alerts.append(alert)
        print(f"   🔥 Alarme incendie Zone {zone}")
    
    print()
    
    # =====================================================
    # RÈGLE 3: CO2 Dangereux (hors plage 400-1000ppm)
    # =====================================================
    print("3️⃣  Règle: CO2 Dangereux - Toutes Zones")
    print("   Condition: CO2 < 400ppm OU > 1000ppm")
    print("   Génération: CO2 élevé (1500-3000ppm) dans plusieurs zones\n")
    
    co2_zones = ['F', 'G', 'H', 'I']
    for i, zone in enumerate(co2_zones):
        co2_value = 1500.0 + (i * 400)  # 1500, 1900, 2300, 2700 ppm
        alert = {
            "@timestamp": timestamp,
            "timestamp": timestamp,
            "zone": zone,
            "sensor_type": "co2_high",
            "sensor_id": f"CO2-{zone}-{300+i}",
            "value": co2_value,
            "unit": "ppm",
            "severity": "high",
            "status": "high",
            "message": f"Niveau de CO2 dangereux: {co2_value}ppm dans la zone {zone}",
            "building": "Smart Building A",
            "source_type": "sensor"
        }
        alerts.append(alert)
        print(f"   ⚠️  {co2_value}ppm en Zone {zone}")
    
    print()
    
    return alerts


def save_alerts_to_file(alerts, output_dir='./data/uploads'):
    """Sauvegarde les alertes au format JSON pour Logstash"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"test_alert_rules_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        for alert in alerts:
            json.dump(alert, f)
            f.write('\n')  # NDJSON format
    
    print(f"💾 {len(alerts)} alertes sauvegardées dans: {filepath}")
    print(f"\n📊 Résumé:")
    print(f"   - Température Zone A: 5 logs (36-44°C)")
    print(f"   - Alarmes incendie: 4 logs (Zones B, C, D, E)")
    print(f"   - CO2 élevé: 4 logs (1500-2700ppm, Zones F, G, H, I)")
    print(f"\n⏱️  Logstash va ingérer ces données dans ~10 secondes")
    print(f"🔔 Les règles devraient se déclencher dans ~15-20 secondes")
    print(f"\n👀 Surveillez les logs webapp:")
    print(f"   docker logs iot-webapp --tail=50 -f | grep -E 'Règle déclenchée|rule_triggered|critical_alert'")
    
    return filepath


if __name__ == '__main__':
    alerts = generate_rule_trigger_data()
    save_alerts_to_file(alerts)
