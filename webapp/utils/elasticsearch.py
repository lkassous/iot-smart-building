"""
Client Elasticsearch pour IoT Smart Building
Gère les connexions et requêtes vers Elasticsearch
"""
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
import logging
from config import get_config

logger = logging.getLogger(__name__)

class ElasticsearchClient:
    """Client Elasticsearch avec méthodes utilitaires"""
    
    def __init__(self):
        config = get_config()
        self.host = config.ELASTICSEARCH_HOST
        self.index_sensors = config.ELASTICSEARCH_INDEX_SENSORS
        self.index_alerts = config.ELASTICSEARCH_INDEX_ALERTS
        
        try:
            self.client = Elasticsearch([self.host])
            # Test de connexion
            if self.client.ping():
                logger.info(f"✅ Connecté à Elasticsearch: {self.host}")
            else:
                logger.error(f"❌ Impossible de se connecter à Elasticsearch")
        except Exception as e:
            logger.error(f"❌ Erreur connexion Elasticsearch: {e}")
            self.client = None
    
    def is_connected(self):
        """Vérifie si la connexion est active"""
        if not self.client:
            return False
        try:
            return self.client.ping()
        except:
            return False
    
    def get_total_logs(self):
        """Récupère le nombre total de logs (sensors + alerts)"""
        try:
            sensors_count = self.client.count(index=self.index_sensors)['count']
            alerts_count = self.client.count(index=self.index_alerts)['count']
            return sensors_count + alerts_count
        except Exception as e:
            logger.error(f"Erreur get_total_logs: {e}")
            return 0
    
    def get_logs_today(self):
        """Récupère le nombre de logs aujourd'hui"""
        try:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            query = {
                "query": {
                    "range": {
                        "@timestamp": {
                            "gte": today.isoformat()
                        }
                    }
                }
            }
            
            sensors_count = self.client.count(index=self.index_sensors, body=query)['count']
            alerts_count = self.client.count(index=self.index_alerts, body=query)['count']
            
            return sensors_count + alerts_count
        except Exception as e:
            logger.error(f"Erreur get_logs_today: {e}")
            return 0
    
    def get_errors_count(self):
        """Récupère le nombre d'alertes critiques"""
        try:
            query = {
                "query": {
                    "bool": {
                        "should": [
                            {"term": {"status": "warning"}},
                            {"term": {"status": "error"}},
                            {"term": {"severity": "critical"}},
                            {"term": {"severity": "high"}},
                            {"exists": {"field": "tags"}},
                            {"term": {"tags": "anomaly"}}
                        ],
                        "minimum_should_match": 1
                    }
                }
            }
            
            sensors_errors = self.client.count(index=self.index_sensors, body=query)['count']
            alerts_critical = self.client.count(index=self.index_alerts, body=query)['count']
            
            return sensors_errors + alerts_critical
        except Exception as e:
            logger.error(f"Erreur get_errors_count: {e}")
            return 0
    
    def get_sensors_active(self):
        """Récupère le nombre de capteurs actifs (uniques)"""
        try:
            query = {
                "size": 0,
                "aggs": {
                    "unique_sensors": {
                        "cardinality": {
                            "field": "sensor_id"
                        }
                    }
                }
            }
            
            response = self.client.search(index=self.index_sensors, body=query)
            return response['aggregations']['unique_sensors']['value']
        except Exception as e:
            logger.error(f"Erreur get_sensors_active: {e}")
            return 0
    
    def get_recent_logs(self, size=10):
        """Récupère les derniers logs"""
        try:
            query = {
                "size": size,
                "sort": [
                    {"@timestamp": {"order": "desc"}}
                ],
                "query": {
                    "match_all": {}
                }
            }
            
            response = self.client.search(index=self.index_sensors, body=query)
            
            logs = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                logs.append({
                    'timestamp': source.get('@timestamp'),
                    'zone': source.get('zone'),
                    'sensor_type': source.get('sensor_type'),
                    'sensor_id': source.get('sensor_id'),
                    'value': source.get('value'),
                    'unit': source.get('unit'),
                    'status': source.get('status'),
                    'floor': source.get('floor')
                })
            
            return logs
        except Exception as e:
            logger.error(f"Erreur get_recent_logs: {e}")
            return []
    
    def search_logs(self, query_string=None, level=None, zone=None, sensor_type=None, 
                   date_from=None, date_to=None, page=1, per_page=50):
        """
        Recherche avancée de logs
        
        Args:
            query_string: Texte libre
            level: Niveau (ok, warning, error)
            zone: Zone du bâtiment
            sensor_type: Type de capteur
            date_from: Date de début
            date_to: Date de fin
            page: Numéro de page
            per_page: Résultats par page
        
        Returns:
            dict: {logs: [], total: int, page: int, pages: int}
        """
        try:
            # Construction de la requête
            must_clauses = []
            
            if query_string:
                must_clauses.append({
                    "query_string": {
                        "query": query_string,
                        "default_field": "message"
                    }
                })
            
            if level:
                must_clauses.append({"match": {"status": level}})
            
            if zone:
                must_clauses.append({"match": {"zone": zone}})
            
            if sensor_type:
                must_clauses.append({"match": {"sensor_type": sensor_type}})
            
            if date_from or date_to:
                range_query = {"range": {"@timestamp": {}}}
                if date_from:
                    range_query["range"]["@timestamp"]["gte"] = date_from
                if date_to:
                    range_query["range"]["@timestamp"]["lte"] = date_to
                must_clauses.append(range_query)
            
            # Si aucun filtre, match all
            if not must_clauses:
                query = {"match_all": {}}
            else:
                query = {
                    "bool": {
                        "must": must_clauses
                    }
                }
            
            # Calcul pagination
            from_index = (page - 1) * per_page
            
            # Requête Elasticsearch
            body = {
                "query": query,
                "sort": [{"@timestamp": {"order": "desc"}}],
                "from": from_index,
                "size": per_page
            }
            
            print(f"DEBUG search_logs: body = {body}")
            response = self.client.search(index=f"{self.index_sensors},{self.index_alerts}", body=body)
            print(f"DEBUG search_logs: total = {response['hits']['total']['value']}")
            
            # Extraction des résultats
            logs = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                logs.append({
                    'id': hit['_id'],
                    'index': hit['_index'],
                    'timestamp': source.get('@timestamp'),
                    'zone': source.get('zone'),
                    'sensor_type': source.get('sensor_type'),
                    'sensor_id': source.get('sensor_id'),
                    'value': source.get('value'),
                    'unit': source.get('unit'),
                    'status': source.get('status'),
                    'message': source.get('message', ''),
                    'floor': source.get('floor'),
                    'severity': source.get('severity'),
                    'alert_type': source.get('alert_type')
                })
            
            total = response['hits']['total']['value']
            pages = (total + per_page - 1) // per_page
            
            return {
                'logs': logs,
                'total': total,
                'page': page,
                'pages': pages,
                'per_page': per_page
            }
            
        except Exception as e:
            logger.error(f"Erreur search_logs: {e}")
            return {
                'logs': [],
                'total': 0,
                'page': 1,
                'pages': 0,
                'per_page': per_page
            }
    
    def get_stats_by_sensor_type(self):
        """Récupère le nombre de logs par type de capteur"""
        try:
            query = {
                "size": 0,
                "aggs": {
                    "by_sensor_type": {
                        "terms": {
                            "field": "sensor_type.keyword",
                            "size": 10
                        }
                    }
                }
            }
            
            response = self.client.search(index=self.index_sensors, body=query)
            
            stats = {}
            for bucket in response['aggregations']['by_sensor_type']['buckets']:
                stats[bucket['key']] = bucket['doc_count']
            
            return stats
        except Exception as e:
            logger.error(f"Erreur get_stats_by_sensor_type: {e}")
            return {}
    
    def get_logs_last_7_days(self):
        """Récupère le nombre de logs par jour sur les 7 derniers jours"""
        try:
            query = {
                "size": 0,
                "query": {
                    "range": {
                        "@timestamp": {
                            "gte": "now-7d/d"
                        }
                    }
                },
                "aggs": {
                    "logs_per_day": {
                        "date_histogram": {
                            "field": "@timestamp",
                            "calendar_interval": "day",
                            "format": "yyyy-MM-dd"
                        }
                    }
                }
            }
            
            response = self.client.search(index=self.index_sensors, body=query)
            
            daily_logs = {}
            for bucket in response['aggregations']['logs_per_day']['buckets']:
                daily_logs[bucket['key_as_string']] = bucket['doc_count']
            
            return daily_logs
        except Exception as e:
            logger.error(f"Erreur get_logs_last_7_days: {e}")
            return {}


# Instance globale
es_client = ElasticsearchClient()
