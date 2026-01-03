#!/usr/bin/env python3
"""
Script de configuration automatique de Kibana
Crée les index patterns, visualisations et dashboard
"""
import requests
import json
import time

KIBANA_URL = "http://localhost:5601"
HEADERS = {
    "kbn-xsrf": "true",
    "Content-Type": "application/json"
}

def wait_for_kibana():
    """Attend que Kibana soit prêt"""
    print("⏳ Attente de Kibana...")
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{KIBANA_URL}/api/status")
            if response.status_code == 200:
                print("✅ Kibana est prêt")
                return True
        except:
            pass
        time.sleep(2)
    print("❌ Kibana non disponible")
    return False

def create_index_pattern(pattern_id, title, time_field="@timestamp"):
    """Crée un index pattern dans Kibana"""
    print(f"📊 Création de l'index pattern: {title}")
    
    url = f"{KIBANA_URL}/api/saved_objects/index-pattern/{pattern_id}"
    
    payload = {
        "attributes": {
            "title": title,
            "timeFieldName": time_field
        }
    }
    
    response = requests.post(url, headers=HEADERS, json=payload)
    
    if response.status_code in [200, 409]:  # 409 = déjà existant
        print(f"  ✅ Index pattern créé: {title}")
        return True
    else:
        print(f"  ❌ Erreur: {response.status_code} - {response.text}")
        return False

def create_visualization_temperature():
    """Crée la visualisation de température par zone"""
    print("📈 Création de la visualisation: Température par zone")
    
    viz_id = "temperature-by-zone"
    url = f"{KIBANA_URL}/api/saved_objects/visualization/{viz_id}"
    
    payload = {
        "attributes": {
            "title": "Température par zone (dernières 24h)",
            "visState": json.dumps({
                "title": "Température par zone (dernières 24h)",
                "type": "line",
                "aggs": [
                    {
                        "id": "1",
                        "enabled": True,
                        "type": "avg",
                        "params": {
                            "field": "value",
                            "customLabel": "Température moyenne"
                        },
                        "schema": "metric"
                    },
                    {
                        "id": "2",
                        "enabled": True,
                        "type": "date_histogram",
                        "params": {
                            "field": "@timestamp",
                            "interval": "1h",
                            "customLabel": "Heure"
                        },
                        "schema": "segment"
                    },
                    {
                        "id": "3",
                        "enabled": True,
                        "type": "terms",
                        "params": {
                            "field": "zone",
                            "size": 9,
                            "order": "desc",
                            "orderBy": "1"
                        },
                        "schema": "group"
                    }
                ],
                "params": {
                    "type": "line",
                    "grid": {
                        "categoryLines": False
                    },
                    "categoryAxes": [
                        {
                            "id": "CategoryAxis-1",
                            "type": "category",
                            "position": "bottom",
                            "show": True,
                            "title": {}
                        }
                    ],
                    "valueAxes": [
                        {
                            "id": "ValueAxis-1",
                            "name": "LeftAxis-1",
                            "type": "value",
                            "position": "left",
                            "show": True,
                            "title": {
                                "text": "Température (°C)"
                            }
                        }
                    ],
                    "seriesParams": [
                        {
                            "show": True,
                            "type": "line",
                            "mode": "normal",
                            "data": {
                                "label": "Température moyenne",
                                "id": "1"
                            },
                            "valueAxis": "ValueAxis-1"
                        }
                    ],
                    "addTooltip": True,
                    "addLegend": True,
                    "legendPosition": "right",
                    "times": [],
                    "addTimeMarker": False
                }
            }),
            "uiStateJSON": "{}",
            "description": "Évolution de la température moyenne par zone sur les dernières 24 heures",
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "index": "logs-iot-sensors",
                    "query": {
                        "query": "sensor_type:temperature",
                        "language": "lucene"
                    },
                    "filter": []
                })
            }
        },
        "references": [
            {
                "name": "kibanaSavedObjectMeta.searchSourceJSON.index",
                "type": "index-pattern",
                "id": "logs-iot-sensors"
            }
        ]
    }
    
    response = requests.post(url, headers=HEADERS, json=payload)
    
    if response.status_code in [200, 409]:
        print("  ✅ Visualisation température créée")
        return viz_id
    else:
        print(f"  ❌ Erreur: {response.status_code}")
        return None

def create_visualization_alerts_heatmap():
    """Crée la heatmap des alertes par zone et heure"""
    print("🔥 Création de la visualisation: Heatmap des alertes")
    
    viz_id = "alerts-heatmap"
    url = f"{KIBANA_URL}/api/saved_objects/visualization/{viz_id}"
    
    payload = {
        "attributes": {
            "title": "Heatmap des alertes par zone et heure",
            "visState": json.dumps({
                "title": "Heatmap des alertes par zone et heure",
                "type": "heatmap",
                "aggs": [
                    {
                        "id": "1",
                        "enabled": True,
                        "type": "count",
                        "params": {},
                        "schema": "metric"
                    },
                    {
                        "id": "2",
                        "enabled": True,
                        "type": "terms",
                        "params": {
                            "field": "zone",
                            "size": 9,
                            "order": "desc",
                            "orderBy": "1"
                        },
                        "schema": "segment"
                    },
                    {
                        "id": "3",
                        "enabled": True,
                        "type": "date_histogram",
                        "params": {
                            "field": "@timestamp",
                            "interval": "1h"
                        },
                        "schema": "group"
                    }
                ],
                "params": {
                    "type": "heatmap",
                    "addTooltip": True,
                    "addLegend": True,
                    "enableHover": True,
                    "legendPosition": "right",
                    "times": [],
                    "colorsNumber": 4,
                    "colorSchema": "Reds",
                    "setColorRange": False,
                    "percentageMode": False,
                    "invertColors": False,
                    "colorsRange": []
                }
            }),
            "uiStateJSON": "{}",
            "description": "Heatmap montrant la distribution des alertes par zone et par heure",
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "index": "logs-iot-alerts",
                    "query": {
                        "query": "*",
                        "language": "lucene"
                    },
                    "filter": []
                })
            }
        },
        "references": [
            {
                "name": "kibanaSavedObjectMeta.searchSourceJSON.index",
                "type": "index-pattern",
                "id": "logs-iot-alerts"
            }
        ]
    }
    
    response = requests.post(url, headers=HEADERS, json=payload)
    
    if response.status_code in [200, 409]:
        print("  ✅ Visualisation heatmap créée")
        return viz_id
    else:
        print(f"  ❌ Erreur: {response.status_code}")
        return None

def create_visualization_metrics():
    """Crée la visualisation des métriques (gauge)"""
    print("📊 Création de la visualisation: Métriques KPI")
    
    viz_id = "kpi-metrics"
    url = f"{KIBANA_URL}/api/saved_objects/visualization/{viz_id}"
    
    payload = {
        "attributes": {
            "title": "KPI - Capteurs actifs et logs",
            "visState": json.dumps({
                "title": "KPI - Capteurs actifs et logs",
                "type": "metric",
                "aggs": [
                    {
                        "id": "1",
                        "enabled": True,
                        "type": "count",
                        "params": {
                            "customLabel": "Total Logs"
                        },
                        "schema": "metric"
                    },
                    {
                        "id": "2",
                        "enabled": True,
                        "type": "cardinality",
                        "params": {
                            "field": "sensor_id",
                            "customLabel": "Capteurs actifs"
                        },
                        "schema": "metric"
                    }
                ],
                "params": {
                    "addTooltip": True,
                    "addLegend": False,
                    "type": "metric",
                    "metric": {
                        "percentageMode": False,
                        "useRanges": False,
                        "colorSchema": "Green to Red",
                        "metricColorMode": "None",
                        "colorsRange": [
                            {
                                "from": 0,
                                "to": 10000
                            }
                        ],
                        "labels": {
                            "show": True
                        },
                        "invertColors": False,
                        "style": {
                            "bgFill": "#000",
                            "bgColor": False,
                            "labelColor": False,
                            "subText": "",
                            "fontSize": 60
                        }
                    }
                }
            }),
            "uiStateJSON": "{}",
            "description": "Métriques clés : nombre total de logs et capteurs actifs",
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "index": "logs-iot-sensors",
                    "query": {
                        "query": "*",
                        "language": "lucene"
                    },
                    "filter": []
                })
            }
        },
        "references": [
            {
                "name": "kibanaSavedObjectMeta.searchSourceJSON.index",
                "type": "index-pattern",
                "id": "logs-iot-sensors"
            }
        ]
    }
    
    response = requests.post(url, headers=HEADERS, json=payload)
    
    if response.status_code in [200, 409]:
        print("  ✅ Visualisation métriques créée")
        return viz_id
    else:
        print(f"  ❌ Erreur: {response.status_code}")
        return None

def create_dashboard(viz_ids):
    """Crée le dashboard avec toutes les visualisations"""
    print("📋 Création du dashboard IoT Smart Building")
    
    dashboard_id = "iot-smart-building-dashboard"
    url = f"{KIBANA_URL}/api/saved_objects/dashboard/{dashboard_id}"
    
    # Disposition des panneaux
    panels = []
    
    if "temperature-by-zone" in viz_ids:
        panels.append({
            "version": "8.11.0",
            "type": "visualization",
            "gridData": {
                "x": 0,
                "y": 0,
                "w": 24,
                "h": 15,
                "i": "1"
            },
            "panelIndex": "1",
            "embeddableConfig": {},
            "panelRefName": "panel_1"
        })
    
    if "alerts-heatmap" in viz_ids:
        panels.append({
            "version": "8.11.0",
            "type": "visualization",
            "gridData": {
                "x": 24,
                "y": 0,
                "w": 24,
                "h": 15,
                "i": "2"
            },
            "panelIndex": "2",
            "embeddableConfig": {},
            "panelRefName": "panel_2"
        })
    
    if "kpi-metrics" in viz_ids:
        panels.append({
            "version": "8.11.0",
            "type": "visualization",
            "gridData": {
                "x": 0,
                "y": 15,
                "w": 48,
                "h": 10,
                "i": "3"
            },
            "panelIndex": "3",
            "embeddableConfig": {},
            "panelRefName": "panel_3"
        })
    
    # Références aux visualisations
    references = []
    for i, viz_id in enumerate(viz_ids, 1):
        references.append({
            "name": f"panel_{i}",
            "type": "visualization",
            "id": viz_id
        })
    
    payload = {
        "attributes": {
            "title": "IoT Smart Building - Dashboard Principal",
            "hits": 0,
            "description": "Dashboard de monitoring pour le smart building avec température, alertes et métriques",
            "panelsJSON": json.dumps(panels),
            "optionsJSON": json.dumps({
                "useMargins": True,
                "hidePanelTitles": False
            }),
            "version": 1,
            "timeRestore": True,
            "timeTo": "now",
            "timeFrom": "now-24h",
            "refreshInterval": {
                "pause": False,
                "value": 60000  # 1 minute
            },
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "query": {
                        "query": "",
                        "language": "lucene"
                    },
                    "filter": []
                })
            }
        },
        "references": references
    }
    
    response = requests.post(url, headers=HEADERS, json=payload)
    
    if response.status_code in [200, 409]:
        print("  ✅ Dashboard créé")
        print(f"\n🌐 Accès au dashboard: {KIBANA_URL}/app/dashboards#/view/{dashboard_id}")
        return True
    else:
        print(f"  ❌ Erreur: {response.status_code}")
        return False

def main():
    print("=" * 60)
    print("🚀 Configuration de Kibana pour IoT Smart Building")
    print("=" * 60)
    print()
    
    if not wait_for_kibana():
        return
    
    # Créer les index patterns
    print("\n📊 Création des index patterns...")
    create_index_pattern("logs-iot-sensors", "logs-iot-sensors-*")
    create_index_pattern("logs-iot-alerts", "logs-iot-alerts-*")
    
    # Créer les visualisations
    print("\n📈 Création des visualisations...")
    viz_ids = []
    
    viz_id = create_visualization_temperature()
    if viz_id:
        viz_ids.append(viz_id)
    
    viz_id = create_visualization_alerts_heatmap()
    if viz_id:
        viz_ids.append(viz_id)
    
    viz_id = create_visualization_metrics()
    if viz_id:
        viz_ids.append(viz_id)
    
    # Créer le dashboard
    if viz_ids:
        print("\n📋 Création du dashboard...")
        create_dashboard(viz_ids)
    
    print("\n" + "=" * 60)
    print("✅ Configuration terminée !")
    print("=" * 60)
    print(f"\n📌 Accédez à Kibana: {KIBANA_URL}")
    print(f"📌 Dashboard direct: {KIBANA_URL}/app/dashboards#/view/iot-smart-building-dashboard")

if __name__ == "__main__":
    main()
