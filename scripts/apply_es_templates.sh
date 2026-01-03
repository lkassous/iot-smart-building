#!/bin/bash
# Script pour appliquer les templates Elasticsearch

echo "📊 Application des templates Elasticsearch..."

# Template sensors
echo "  - Sensors template..."
curl -X PUT "http://localhost:9200/_index_template/logs-iot-sensors-template" \
  -H 'Content-Type: application/json' \
  -d @elasticsearch/mappings/sensors-template.json \
  -s -o /dev/null && echo "    ✅ Template sensors appliqué"

# Template alerts
echo "  - Alerts template..."
curl -X PUT "http://localhost:9200/_index_template/logs-iot-alerts-template" \
  -H 'Content-Type: application/json' \
  -d @elasticsearch/mappings/alerts-template.json \
  -s -o /dev/null && echo "    ✅ Template alerts appliqué"

echo ""
echo "✅ Templates appliqués avec succès !"
