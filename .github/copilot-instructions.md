# IoT Smart Building - AI Coding Agent Instructions

## 🎯 Project Context & Objectives

This is an **educational IoT Smart Building monitoring and log analysis platform** designed to centralize, index, search, and visualize sensor data in real-time using the ELK Stack.

### Business Context
Managing a **smart building with hundreds of sensors** generating logs for:
- **Sensors**: Temperature, humidity, luminosity, CO2 (CSV format)
- **Alerts**: Anomalies, threshold violations (JSON format)
- **Maintenance**: Equipment wear, predictive failures
- **Energy**: Electricity, water, heating consumption
- **Occupancy**: Room presence, space utilization rates

### Key Performance Indicators (KPIs)
1. Average temperature per zone per hour
2. Critical alerts count per day
3. Real-time energy consumption
4. Space occupancy rate
5. Maintenance predictions (ML optional)

### Critical Use Cases
- 🚨 Trigger alert if temperature >30°C or <15°C (implemented in csv-pipeline)
- ⚡ Optimize energy consumption via pattern analysis
- 🔧 Predict equipment failures through historical analysis

## Architecture Overview

**Full-stack monitoring platform** using the ELK Stack (Elasticsearch, Logstash, Kibana) with Flask web application, MongoDB for metadata, and Redis for caching.

### System Components (docker-compose.yml)
- **Elasticsearch (9200)**: Time-series sensor data storage and search
- **Logstash (5000, 9600)**: Data ingestion pipelines for CSV and JSON sensor files
- **Kibana (5601)**: Visualization dashboards
- **MongoDB (27017)**: Metadata storage (credentials: admin/admin123)
- **Redis (6379)**: Session cache
- **Flask webapp (8000)**: Web interface for data upload and management

**Critical**: All services run in Docker with `iot-network` bridge. Services use container names for DNS (`elasticsearch:9200` not `localhost:9200` internally).

## Data Flow Architecture

1. **Upload**: Files dropped in `data/uploads/` (mounted to both webapp and logstash)
2. **Processing**: Logstash monitors `uploads/*.{csv,json}` with separate pipelines
3. **Storage**: Data indexed to Elasticsearch with date-partitioned indices
4. **Access**: Kibana visualizes, webapp queries via Elasticsearch API

### Index Naming Convention
- Sensors: `logs-iot-sensors-YYYY.MM.dd` (from CSV pipeline)
- Alerts: `logs-iot-alerts-YYYY.MM.dd` (from JSON pipeline)

## Logstash Pipeline Patterns

### CSV Pipeline (`logstash/pipeline/csv-pipeline.conf`)
**Schema**: `timestamp,zone,sensor_type,sensor_id,value,unit,status`

**Built-in anomaly detection**:
- Temperature: alerts if <15°C or >30°C → adds `["anomaly", "temperature_alert"]` tags
- Humidity: alerts if <30% or >80% → adds `["anomaly", "humidity_alert"]` tags

**Document ID**: SHA256 fingerprint of `timestamp+zone+sensor_id` (prevents duplicates)

### JSON Pipeline (`logstash/pipeline/json-pipeline.conf`)
**Field normalization**:
- `sensor` → `sensor_id`
- `location` → `zone`
- `alert_type` → `event_type`

**Zone-to-floor mapping** (geographic enrichment):
- Zones A/B/C → Floor 1
- Zones D/E/F → Floor 2
- Zones G/H/I → Floor 3

**Critical**: Both pipelines add `"building": "Smart Building A"` and `source_type` fields.

## Critical Developer Workflows

### Starting the Stack
```bash
docker-compose up -d                    # Start all services
docker-compose logs -f webapp           # Follow webapp logs
docker-compose logs -f logstash         # Watch data ingestion
```

**Health checks**: Elasticsearch, Kibana, MongoDB, Redis have built-in healthchecks. Webapp waits for all dependencies.

### Testing Data Ingestion
1. Copy CSV/JSON files to `data/uploads/`
2. Logstash auto-processes (sincedb disabled: `sincedb_path => "/dev/null"`)
3. Check stdout: `docker-compose logs logstash | grep rubydebug`
4. Query Elasticsearch: `curl http://localhost:9200/logs-iot-*/_search?pretty`

### Generating Test Data (URGENT - Required)
```python
# scripts/generate_test_data.py
from faker import Faker
import csv, json, random
from datetime import datetime, timedelta

fake = Faker()
zones = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
sensor_types = ['temperature', 'humidity', 'luminosity', 'co2']

# Generate 10,000 CSV sensor logs
with open('data/uploads/sensors_test.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['timestamp', 'zone', 'sensor_type', 'sensor_id', 'value', 'unit', 'status'])
    
    for i in range(10000):
        timestamp = (datetime.now() - timedelta(hours=random.randint(0, 168))).isoformat()
        zone = random.choice(zones)
        sensor_type = random.choice(sensor_types)
        sensor_id = random.randint(1000, 9999)
        
        if sensor_type == 'temperature':
            value = round(random.uniform(10, 35), 1)  # Some will trigger alerts
            unit = '°C'
        elif sensor_type == 'humidity':
            value = round(random.uniform(20, 90), 1)  # Some will trigger alerts
            unit = '%'
        # ... etc
        
        status = 'ok' if random.random() > 0.1 else 'warning'
        writer.writerow([timestamp, zone, sensor_type, sensor_id, value, unit, status])
```

### Environment Setup
Copy `.env.example` to `.env` before running locally (outside Docker). Docker uses environment vars from `docker-compose.yml`.

### Debugging Tips

### Directory Structure
```
webapp/               # Flask app (CURRENTLY EMPTY - TOP PRIORITY)
  app.py             # ❌ TO CREATE: Main entry point with Flask init
  config.py          # ❌ TO CREATE: Environment config loading
  requirements.txt   # ❌ TO CREATE: Python dependencies
  Dockerfile         # ❌ TO CREATE: Container build instructions
  models/            # ❌ TO CREATE: MongoDB schemas
    file_metadata.py # Track uploaded files
    search_history.py # Store user queries
  routes/            # ❌ TO CREATE: Flask blueprints
    main.py          # Dashboard routes (GET /)
    upload.py        # File upload (POST /upload)
    search.py        # Search & results
    api.py           # REST API endpoints
  utils/             # ❌ TO CREATE: Helper modules
    elasticsearch.py # ES client wrapper
    mongodb.py       # MongoDB connection
    redis_client.py  # Redis cache
    validators.py    # File validation
  static/            # Frontend assets
    css/style.css    # Custom styles
    js/main.js       # AJAX calls, Chart.js
  templates/         # Jinja2 HTML templates
    base.html        # Bootstrap 5 layout
    index.html       # Dashboard
    upload.html      # File upload page
    search.html      # Search form
    results.html     # Results table
logstash/pipeline/   # ✅ DONE: Data ingestion configs (CSV + JSON)
data/uploads/        # Shared volume for file uploads
data/test-data/      # ❌ TO CREATE: Generated test files
elasticsearch/mappings/  # ❌ TO CREATE: Index templates
kibana/exports/      # ❌ TO CREATE: Dashboard JSON exports
tests/               # ❌ TO CREATE: Pytest unit & integration tests
scripts/             # ❌ TO CREATE: Utility scripts (data generation)
```

### Required Flask App Structure

**Minimal `webapp/app.py`**:
```python
from flask import Flask, render_template, request, jsonify
from elasticsearch import Elasticsearch
from pymongo import MongoClient
import redis
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Initialize connections
es = Elasticsearch([os.getenv('ELASTICSEARCH_HOST', 'http://localhost:9200')])
mongo_client = MongoClient(os.getenv('MONGODB_URI'))
mongo_db = mongo_client.iot_smart_building
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    # Health check for Docker
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
```

**Required `webapp/requirements.txt`**:
```txt
Flask==3.0.0
flask-restful==0.3.10
gunicorn==21.2.0
python-dotenv==1.0.0
elasticsearch==8.11.0
pymongo==4.6.1
redis==5.0.1
python-multipart==0.0.6
Faker==20.1.0
pytest==7.4.3
pytest-cov==4.1.0
```

### Data Storage Conventions
- **Uploads volume**: `./data/uploads` mounted to both webapp (`/app/uploads`) and logstash (`/usr/share/logstash/uploads`)
- **Test data**: `data/test-data/` excluded from git
- **Persistent volumes**: Named volumes for elasticsearch-data, mongodb-data, redis-data

## Integration Points

### Elasticsearch Connection
**From webapp**: `ELASTICSEARCH_HOST=http://elasticsearch:9200` (inside Docker) or `http://localhost:9200` (local dev)

Query pattern example:
```python
# Date-partitioned index queries
GET /logs-iot-sensors-2025.10.*/_search
GET /logs-iot-alerts-*/_search
```

### MongoDB Connection
**URI format**: `mongodb://admin:admin123@mongodb:27017/iot_smart_building?authSource=admin`

Database: `iot_smart_building` (initialized automatically)

### Redis Usage
Simple key-value cache on port 6379. No authentication configured.

## Critical Constraints

1. **Logstash reprocesses files**: `sincedb_path => "/dev/null"` means files are reprocessed on restart. For production, use persistent sincedb.

2. **Security disabled**: `xpack.security.enabled=false` on Elasticsearch/Kibana for dev. **Enable for production**.

3. **File size limits**: `.env.example` sets `MAX_FILE_SIZE_MB=100` for uploads.

4. **Allowed extensions**: Only `csv,json,txt` per `.env.example`.

5. **Language**: Comments in French (pipeline configs, docker-compose). Maintain this convention.

## Grading Criteria & Project Scope

### Evaluation Levels

**OBLIGATOIRE - 12/20 (Minimum viable product)**:
- ✅ All 5 core modules functional
- ✅ Docker deployment working
- ✅ Basic web interface
- ✅ ELK stack configured
- ✅ MongoDB integration
- ⏱️ Estimated: 10-12 days

**INTERMÉDIAIRE - 16/20 (Complete project)**:
- ✅ All obligatory modules (12/20)
- ✅ **+ 3 intermediate modules** from:
  - Authentication & roles (Flask-Login)
  - Advanced Redis caching (5min TTL for ES queries)
  - RESTful API + Swagger documentation
  - Custom dashboards (save configs in MongoDB)
  - Advanced export (CSV, JSON, PDF reports)
- ⏱️ Estimated: 18-22 days

**AVANCÉ - 20/20 (Excellent project)**:
- ✅ All obligatory + 3 intermediate modules (16/20)
- ✅ **+ 2 advanced modules** from:
  - **Intelligent alerting** (rule engine, email/Slack notifications, escalation) - RECOMMENDED for IoT
  - **Real-time WebSocket** (Flask-SocketIO, live logs, animated charts) - RECOMMENDED for IoT
  - **Machine Learning** (ES ML jobs, anomaly detection, predictive maintenance)
  - **CI/CD pipeline** (GitHub Actions, pytest coverage >70%, Docker build)
  - **Multi-tenancy** (data isolation, quotas, billing simulation)
  - **Observability** (Prometheus/Grafana metrics, distributed tracing)
- ⏱️ Estimated: 28-35 days

### Core Modules Status (Required for 12/20)

**Module 1: File Management** ❌ NOT STARTED
- Upload interface with drag & drop
- File validation (CSV/JSON, max 100MB)
- Preview first 10 lines
- Logstash injection trigger
- Files list with pagination
- Metadata storage in MongoDB

**Module 2: ELK Configuration** ⚠️ PARTIAL
- ✅ Elasticsearch running (8.11.0)
- ✅ 2 Logstash pipelines (CSV + JSON)
- ✅ Anomaly detection (temp/humidity)
- ❌ Index templates in `elasticsearch/mappings/`
- ❌ 3 Kibana visualizations (temp chart, alert heatmap, energy gauge)
- ❌ Dashboard exported to `kibana/exports/`

**Module 3: Web Interface** ❌ NOT STARTED
- Dashboard page (4 KPI cards, Chart.js graphs)
- Upload page (drag & drop, progress bar)
- Search page (filters: level, zone, sensor_type, date range)
- Results page (DataTables.js, pagination, CSV export)
- Responsive design (Bootstrap 5)

**Module 4: MongoDB Integration** ⚠️ CONFIGURED ONLY
- ✅ MongoDB 7.0 running (admin/admin123)
- ❌ File metadata model
- ❌ Search history model
- ❌ Connection in Flask app

**Module 5: Docker Deployment** ⚠️ PARTIAL
- ✅ docker-compose.yml complete (6 services)
- ✅ Health checks configured
- ✅ .env.example provided
- ❌ webapp/Dockerfile missing
- ❌ webapp/requirements.txt missing
- ❌ Test data generation script

## Critical Developer Workflows

- **Logstash not processing?** Check `docker-compose logs logstash` for pipeline syntax errors
- **Elasticsearch queries failing?** Verify index exists: `curl localhost:9200/_cat/indices?v`
- **Webapp can't connect?** Ensure using container hostnames (`elasticsearch:9200`) not localhost inside Docker
- **Data not appearing?** Check Logstash stdout debug output (rubydebug codec enabled)

## Next Implementation Steps

Based on empty directories and project requirements, **URGENT PRIORITIES**:

### 🔴 Critical (Blocking - Week 1)
1. **Flask app structure** (`webapp/`)
   - Create `app.py` entry point with Flask initialization
   - Create `requirements.txt`: Flask 3.x, elasticsearch 8.x, pymongo 4.x, redis 5.x, gunicorn
   - Create `Dockerfile` with multi-stage build (python:3.11-slim base)
   - File upload route (POST /upload) with drag & drop support
   - Search route (GET /search) with Elasticsearch Query DSL
   - API endpoints: `/api/v1/stats`, `/api/v1/logs`, `/api/v1/files`

2. **MongoDB models** (`webapp/models/`)
   - `file_metadata.py`: Track uploaded files (filename, size, status, num_logs, upload_date)
   - `search_history.py`: Store user queries (query, filters, num_results, execution_time)

3. **Test data generation**
   - Script `scripts/generate_test_data.py` using Faker library
   - Generate 10,000+ CSV logs (temperature/humidity with zones A-I)
   - Generate 1,000+ JSON alerts with severity levels
   - Auto-copy to `data/uploads/` for Logstash processing

4. **Kibana dashboards** (`kibana/exports/`)
   - **Visualization 1**: Line chart - Temperature evolution by zone (last 24h)
   - **Visualization 2**: Heat map - Alerts count by zone and hour
   - **Visualization 3**: Gauge - Current energy consumption vs target
   - Export dashboard as JSON for version control

### 🟡 Important (Week 2-3)
5. **Frontend templates** (`webapp/templates/`)
   - `base.html`: Bootstrap 5 layout with navbar/footer
   - `index.html`: Dashboard with 4 KPI cards + Chart.js graphs
   - `upload.html`: Drag & drop file upload with progress bar
   - `search.html`: Search form with filters (level, zone, sensor_type, date range)
   - `results.html`: DataTables.js with pagination (50 rows/page), modal details, CSV export

6. **Elasticsearch index templates** (`elasticsearch/mappings/`)
   - Template for `logs-iot-sensors-*` with proper field types (date, keyword, float)
   - Template for `logs-iot-alerts-*` with alert-specific fields
   - Index lifecycle management (ILM) for data retention

7. **Unit tests** (`tests/`)
   - `test_upload.py`: File validation (CSV/JSON structure, size limits)
   - `test_elasticsearch.py`: Query DSL construction, result parsing
   - `test_mongodb.py`: CRUD operations on metadata
   - Target: >70% code coverage with pytest

### 🟢 Advanced Features (Week 4+)
8. **Recommended for 16/20 (choose 3)**:
   - Redis caching (cache ES queries with 5min TTL, session management)
   - RESTful API + Swagger/OpenAPI documentation
   - User authentication (Flask-Login) with roles (Admin/User/Viewer)

9. **Recommended for 20/20 (choose 2)**:
   - **Intelligent alerting** (rule engine, multi-channel notifications: email/Slack, escalation)
   - **Real-time WebSocket** (Flask-SocketIO, live tail logs, animated charts)
   - **Machine Learning** (Elasticsearch ML jobs, anomaly detection, predictive maintenance)
   - **CI/CD** (GitHub Actions: linting, tests, Docker build, auto-deploy)
