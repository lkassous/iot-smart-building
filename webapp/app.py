"""
Application Flask principale - IoT Smart Building
Point d'entrée de l'application de monitoring
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from flasgger import Swagger
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
import time

# Import de la configuration
from config import get_config
from swagger_config import swagger_config, swagger_template

# Import des connexions aux services
from utils import es_client, mongo_client, redis_client
from utils.validators import validate_file
from utils.user_manager import UserManager
from utils.permissions import permission_required, role_required
from utils.realtime_monitor import RealtimeMonitor, AlertMonitor
from utils.alert_rules_manager import AlertRulesManager
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialisation de l'application Flask
app = Flask(__name__)

# Chargement de la configuration
config = get_config()
app.config.from_object(config)

# Activation CORS pour le développement
CORS(app)

# Configuration Flask-SocketIO pour WebSocket temps réel
# Mode threading pour compatibilité maximale (long polling fallback automatique)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=True)

# Configuration Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'info'

# Initialisation du gestionnaire d'utilisateurs
user_manager = UserManager(mongo_client)

@login_manager.user_loader
def load_user(user_id):
    """Callback pour charger un utilisateur depuis son ID"""
    return user_manager.get_user_by_id(user_id)

# Configuration Swagger/OpenAPI
swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Initialisation LAZY du monitoring temps réel
# Les monitors seront initialisés à la première connexion WebSocket
realtime_monitor = None
alert_monitor = None
alert_rules_manager = None  # Gestionnaire des règles d'alertes
_monitor_client_count = 0

# Création du dossier uploads si inexistant
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ============================================================================
# ENREGISTREMENT DES BLUEPRINTS
# ============================================================================

from routes.auth import auth_bp, init_auth_routes
from routes.alerts import alerts_bp

# Injecter le user_manager dans les routes auth
init_auth_routes(user_manager)

app.register_blueprint(auth_bp)
app.register_blueprint(alerts_bp)


# ============================================================================
# ROUTES PRINCIPALES
# ============================================================================

@app.route('/')
@login_required
@permission_required('read')
def index():
    """Page d'accueil - Dashboard principal (read permission)"""
    return render_template('index.html', page_title='Dashboard')


# =====================
# Socket.IO handlers
# =====================
@socketio.on('connect', namespace='/monitoring')
def _on_connect():
  global realtime_monitor, alert_monitor, alert_rules_manager, _monitor_client_count
  _monitor_client_count += 1
  app.logger.info(f"Socket connected - clients={_monitor_client_count}")

  # Initialize alert rules manager (lazy init)
  if alert_rules_manager is None:
    try:
      alert_rules_manager = AlertRulesManager(mongo_client.db, es_client)
      app.logger.info("✅ AlertRulesManager initialisé")
    except Exception as e:
      app.logger.error(f"Failed to init alert rules manager: {e}")
  
  # Initialize monitors lazily when first client connects
  if alert_monitor is None:
    try:
      alert_monitor = AlertMonitor(socketio, es_client, alert_rules_manager)
      app.logger.info("✅ AlertMonitor initialisé avec rules manager")
    except Exception as e:
      app.logger.error(f"Failed to init alert monitor: {e}")
  
  if realtime_monitor is None:
    try:
      realtime_monitor = RealtimeMonitor(socketio, es_client, alert_monitor)
      realtime_monitor.start()
      app.logger.info("✅ RealtimeMonitor démarré")
    except Exception as e:
      app.logger.error(f"Failed to start realtime monitor: {e}")

  # Send an initial stats payload
  try:
    # Récupérer l'activité des zones pour les dernières 24 heures
    zones_activity = {}
    try:
      one_day_ago = (datetime.now() - timedelta(hours=24)).isoformat()
      zones_result = es_client.client.search(index='logs-iot-sensors-*', body={
        'query': {
          'range': {
            '@timestamp': {'gte': one_day_ago}
          }
        },
        'aggs': {
          'zones': {
            'terms': {
              'field': 'zone',  # zone est déjà de type keyword, pas besoin de .keyword
              'size': 10
            }
          }
        },
        'size': 0
      })
      
      for bucket in zones_result.get('aggregations', {}).get('zones', {}).get('buckets', []):
        zones_activity[bucket['key']] = bucket['doc_count']
      
      app.logger.info(f"Zones activity loaded: {zones_activity}")
    except Exception as e:
      app.logger.warning(f"Could not get zones activity: {e}")
    
    stats = {
      'total_logs': es_client.get_total_logs(),
      'logs_today': es_client.get_logs_today(),
      'errors_count': es_client.get_errors_count(),
      'sensors_active': es_client.get_sensors_active(),
      'zones_activity': zones_activity,
      'timestamp': datetime.now().isoformat()
    }
    emit('stats_update', stats, namespace='/monitoring')
  except Exception:
    app.logger.exception('Could not send initial stats')


@socketio.on('disconnect', namespace='/monitoring')
def _on_disconnect():
  global _monitor_client_count, realtime_monitor
  _monitor_client_count = max(0, _monitor_client_count - 1)
  app.logger.info(f"Socket disconnected - clients={_monitor_client_count}")

  # Optionally stop monitors when no clients remain
  if _monitor_client_count == 0 and realtime_monitor is not None:
    try:
      # Keep monitor running for a short period, but stop to conserve resources
      realtime_monitor.stop()
      realtime_monitor = None
      app.logger.info('Realtime monitor stopped (no clients)')
    except Exception:
      app.logger.exception('Error stopping realtime monitor')


@socketio.on('subscribe_monitoring', namespace='/monitoring')
def _on_subscribe(data=None):
  """Client demande à s'abonner explicitement (optional)"""
  app.logger.info('Client subscribed to monitoring')
  emit('connection_response', {'message': 'Vous êtes abonné au flux temps réel'}, namespace='/monitoring')


@socketio.on('unsubscribe_monitoring', namespace='/monitoring')
def _on_unsubscribe(data=None):
  app.logger.info('Client unsubscribed from monitoring')
  # client will be disconnected by browser if desired
  emit('connection_response', {'message': 'Vous avez été désabonné du flux temps réel'}, namespace='/monitoring')


@socketio.on('request_recent_logs', namespace='/monitoring')
def _on_request_recent_logs(payload=None):
  """Renvoie les logs récents immédiatement"""
  try:
    limit = int(payload.get('limit', 10)) if payload and isinstance(payload, dict) else 10
    app.logger.info(f"Client requested {limit} recent logs")
    
    # Query Elasticsearch for most recent logs
    res = es_client.client.search(index='logs-iot-*', body={
      'sort': [{'@timestamp': {'order': 'desc'}}],
      'size': limit
    })
    logs = []
    for hit in res.get('hits', {}).get('hits', []):
      s = hit.get('_source', {})
      logs.append({
        'timestamp': s.get('@timestamp', s.get('timestamp')),
        'zone': s.get('zone'),
        'sensor_type': s.get('sensor_type', s.get('event_type')),
        'value': s.get('value'),
        'unit': s.get('unit'),
        'status': s.get('status', s.get('severity')),
        'message': s.get('message', ''),
      })

    app.logger.info(f"Sending {len(logs)} recent logs to client")
    emit('recent_logs', {'count': len(logs), 'logs': logs}, namespace='/monitoring')
  except Exception as e:
    app.logger.exception('Error fetching recent logs')
    emit('error', {'message': 'Impossible de récupérer les logs récents'}, namespace='/monitoring')



@app.route('/upload')
@login_required
@permission_required('write')
def upload_page():
    """Page d'upload de fichiers (write permission)"""
    return render_template('upload.html', page_title='Upload de fichiers')


@app.route('/upload', methods=['POST'])
@login_required
@permission_required('write')
def upload_file():
    """
    Upload de fichier IoT
    Accepte les fichiers CSV, JSON, TXT (max 100MB)
    ---
    tags:
      - Upload
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: Fichier à uploader (CSV, JSON ou TXT)
    responses:
      200:
        description: Fichier uploadé avec succès
        schema:
          $ref: '#/definitions/UploadResponse'
        examples:
          application/json:
            success: true
            filename: "test_upload.csv"
            file_size: 310
            num_logs: 5
            file_id: "507f1f77bcf86cd799439011"
            message: "Fichier uploadé avec succès. Logstash va traiter 5 logs."
            preview: [["2025-10-30T10:00:00", "B", "temperature", "2001", "22.5", "°C", "ok"]]
      400:
        description: Fichier invalide ou manquant
        schema:
          $ref: '#/definitions/ErrorResponse'
        examples:
          application/json:
            error: "Fichier invalide"
            validation_errors: ["Colonnes manquantes : timestamp, zone"]
      413:
        description: Fichier trop volumineux
        schema:
          $ref: '#/definitions/ErrorResponse'
      500:
        description: Erreur serveur
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    start_time = time.time()
    
    # Vérifier qu'un fichier est présent
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'Nom de fichier vide'}), 400
    
    # Validation de l'extension
    allowed_extensions = app.config['ALLOWED_EXTENSIONS']
    file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    if file_extension not in allowed_extensions:
        return jsonify({'error': f'Extension non autorisée. Formats acceptés : {", ".join(allowed_extensions)}'}), 400
    
    # Sécurisation du nom de fichier
    filename = secure_filename(file.filename)
    
    # Vérifier si le fichier existe déjà
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        # Ajouter timestamp pour éviter les conflits
        name, ext = filename.rsplit('.', 1)
        filename = f"{name}_{int(time.time())}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        # Sauvegarder le fichier
        file.save(filepath)
        file_size = os.path.getsize(filepath)
        
        # Valider la structure du fichier
        validation = validate_file(filepath, file_extension)
        
        if not validation['valid']:
            # Supprimer le fichier invalide
            os.remove(filepath)
            return jsonify({
                'error': 'Fichier invalide',
                'validation_errors': validation['errors']
            }), 400
        
        num_logs = validation.get('num_lines', validation.get('num_items', 0))
        
        # Créer les métadonnées dans MongoDB
        processing_time = time.time() - start_time
        file_id = mongo_client.save_file_metadata(
            filename=filename,
            file_size=file_size,
            file_type=file_extension,
            status='processing',  # Logstash va traiter
            num_logs=num_logs,
            processing_time=processing_time
        )
        
        # Logstash détectera automatiquement le nouveau fichier
        logging.info(f"✅ Fichier uploadé: {filename} ({file_size} bytes, {num_logs} logs)")
        
        return jsonify({
            'success': True,
            'filename': filename,
            'file_size': file_size,
            'num_logs': num_logs,
            'file_id': file_id,
            'preview': validation.get('preview', [])[:5],  # 5 premières lignes
            'message': f'Fichier uploadé avec succès. Logstash va traiter {num_logs} logs.'
        }), 200
        
    except Exception as e:
        logging.error(f"❌ Erreur upload fichier: {e}")
        
        # Supprimer le fichier en cas d'erreur
        if os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify({'error': f'Erreur lors de l\'upload: {str(e)}'}), 500


@app.route('/search')
@login_required
@permission_required('read')
def search_page():
    """Page de recherche de logs (read permission)"""
    return render_template('search.html', page_title='Recherche')


@app.route('/results')
@login_required
@permission_required('read')
def results_page():
    """Page d'affichage des résultats (read permission)"""
    query = request.args.get('query', '')
    return render_template('results.html', page_title='Résultats', query=query)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health')
def health():
    """
    Health check endpoint
    Vérifie la disponibilité de tous les services backend
    ---
    tags:
      - Health
    responses:
      200:
        description: Statut de santé du système
        schema:
          $ref: '#/definitions/HealthResponse'
        examples:
          application/json:
            status: healthy
            timestamp: "2025-10-30T08:00:00.000000"
            service: iot-webapp
            version: "1.0.0"
            elasticsearch: connected
            mongodb: connected
            redis: connected
    """
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'iot-webapp',
        'version': '1.0.0'
    }
    
    # Vérification des services backend
    try:
        if es_client.is_connected():
            health_status['elasticsearch'] = 'connected'
        else:
            health_status['elasticsearch'] = 'disconnected'
            health_status['status'] = 'degraded'
    except:
        health_status['elasticsearch'] = 'error'
        health_status['status'] = 'degraded'
    
    try:
        if mongo_client.is_connected():
            health_status['mongodb'] = 'connected'
        else:
            health_status['mongodb'] = 'disconnected'
            health_status['status'] = 'degraded'
    except:
        health_status['mongodb'] = 'error'
        health_status['status'] = 'degraded'
    
    try:
        if redis_client.is_connected():
            health_status['redis'] = 'connected'
        else:
            health_status['redis'] = 'disconnected'
            health_status['status'] = 'degraded'
    except:
        health_status['redis'] = 'error'
        health_status['status'] = 'degraded'
    
    return jsonify(health_status), 200


@app.route('/api/v1/stats')
def api_stats():
    """
    Statistiques globales du système
    Retourne les KPIs en temps réel avec cache Redis (TTL: 5min)
    ---
    tags:
      - Statistics
    responses:
      200:
        description: Statistiques système
        schema:
          $ref: '#/definitions/StatsResponse'
        examples:
          application/json:
            total_logs: 24934
            logs_today: 1092
            errors_count: 245
            files_uploaded: 3
            zones_active: 9
            sensors_active: 712
            last_update: "2025-10-30T08:00:00.000000"
      500:
        description: Erreur serveur
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    # Vérifier le cache Redis (TTL: 5 minutes)
    cached_stats = redis_client.get_cached_stats()
    if cached_stats:
        return jsonify(cached_stats), 200
    
    # Requêtes Elasticsearch pour statistiques réelles
    try:
        stats = {
            'total_logs': es_client.get_total_logs(),
            'logs_today': es_client.get_logs_today(),
            'errors_count': es_client.get_errors_count(),
            'files_uploaded': mongo_client.get_files_count(),
            'zones_active': 9,  # A-I zones
            'sensors_active': es_client.get_sensors_active(),
            'last_update': datetime.utcnow().isoformat()
        }
        
        # Mettre en cache pour 5 minutes
        redis_client.cache_stats(stats, ttl=300)
        
        return jsonify(stats), 200
    except Exception as e:
        logging.error(f"Erreur récupération stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/logs')
def api_logs():
    """
    Recherche de logs IoT avec filtres
    Supporte la pagination et les filtres multiples
    ---
    tags:
      - Logs
    parameters:
      - name: q
        in: query
        type: string
        description: Recherche textuelle
        example: "anomaly"
      - name: level
        in: query
        type: string
        description: Niveau de log
        enum: [ok, warning, error]
      - name: zone
        in: query
        type: string
        description: Zone du bâtiment (A-I)
        example: "A"
      - name: sensor_type
        in: query
        type: string
        description: Type de capteur
        enum: [temperature, humidity, luminosity, co2]
      - name: date_from
        in: query
        type: string
        format: date
        description: Date de début (ISO 8601)
        example: "2025-10-29"
      - name: date_to
        in: query
        type: string
        format: date
        description: Date de fin (ISO 8601)
        example: "2025-10-30"
      - name: page
        in: query
        type: integer
        default: 1
        description: Numéro de page
      - name: per_page
        in: query
        type: integer
        default: 50
        description: Résultats par page (max 100)
    responses:
      200:
        description: Liste des logs filtrés
        schema:
          $ref: '#/definitions/LogsResponse'
      500:
        description: Erreur serveur
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    # Paramètres de requête
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', app.config['RESULTS_PER_PAGE'], type=int)
    level = request.args.get('level', None)
    zone = request.args.get('zone', None)
    sensor_type = request.args.get('sensor_type', None)
    date_from = request.args.get('date_from', None)
    date_to = request.args.get('date_to', None)
    query_string = request.args.get('q', None)
    
    # Requête Elasticsearch avec filtres
    try:
        result = es_client.search_logs(
            query_string=query_string,
            level=level,
            zone=zone,
            sensor_type=sensor_type,
            date_from=date_from,
            date_to=date_to,
            page=page,
            per_page=per_page
        )
        
        return jsonify(result), 200
    except Exception as e:
        logging.error(f"Erreur recherche logs: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/files')
def api_files():
    """
    Liste des fichiers uploadés
    Récupère les métadonnées depuis MongoDB
    ---
    tags:
      - Files
    responses:
      200:
        description: Liste des fichiers
        schema:
          $ref: '#/definitions/FilesResponse'
        examples:
          application/json:
            count: 3
            files:
              - _id: "507f1f77bcf86cd799439011"
                filename: "sensors_test.csv"
                file_size: 310
                file_type: "csv"
                num_logs: 5
                status: "processed"
                upload_date: "2025-10-30T08:00:00"
                processing_time: 0.5
      500:
        description: Erreur serveur
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    try:
        files = mongo_client.get_uploaded_files(limit=100)
        
        return jsonify({
            'files': files,
            'count': len(files)
        }), 200
    except Exception as e:
        logging.error(f"Erreur récupération fichiers: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# GESTION DES ERREURS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Page 404 personnalisée"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Resource not found'}), 404
    return render_template('404.html', page_title='Page non trouvée'), 404


@app.errorhandler(500)
def internal_error(error):
    """Page 500 personnalisée"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('500.html', page_title='Erreur serveur'), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """Fichier trop volumineux"""
    max_size = app.config['MAX_FILE_SIZE_MB']
    return jsonify({
        'error': f'File too large. Maximum size: {max_size}MB'
    }), 413


# ============================================================================
# FILTRES JINJA2 PERSONNALISÉS
# ============================================================================

@app.template_filter('datetime')
def format_datetime(value, format='%d/%m/%Y %H:%M:%S'):
    """Formater une date pour l'affichage"""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except:
            return value
    if value is None:
        return ''
    return value.strftime(format)


@app.template_filter('filesize')
def format_filesize(bytes):
    """Formater une taille de fichier en unités lisibles"""
    if bytes is None:
        return '0 B'
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"


# ============================================================================
# CONTEXTE GLOBAL POUR LES TEMPLATES
# ============================================================================

@app.context_processor
def inject_global_vars():
    """Injecter des variables globales dans tous les templates"""
    return {
        'app_name': 'IoT Smart Building',
        'app_version': '1.0.0',
        'current_year': datetime.now().year,
        'zones': app.config['BUILDING_ZONES'],
        'sensor_types': app.config['SENSOR_TYPES'],
        'current_user': current_user
    }


# ============================================================================
# GESTIONNAIRES D'ERREURS
# ============================================================================

@app.errorhandler(403)
def forbidden(error):
    """Page d'erreur 403 - Accès refusé"""
    return render_template('403.html'), 403


@app.errorhandler(404)
def not_found(error):
    """Page d'erreur 404 - Page non trouvée"""
    return render_template('404.html'), 404 if os.path.exists('templates/404.html') else ('Page non trouvée', 404)


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == '__main__':
    # NE PAS démarrer le monitoring ici - il démarrera quand le premier client se connecte
    # Cela évite les erreurs de connexion au démarrage si ES n'est pas prêt
    logging.info("⏳ Monitoring en attente de connexion client WebSocket...")
    
    # Mode développement avec SocketIO
    # En production, utiliser gunicorn avec worker threading
    socketio.run(
        app,
        host='0.0.0.0',
        port=8000,
        debug=True
    )

