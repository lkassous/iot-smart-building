"""
Service de monitoring temps réel avec WebSocket
Surveille Elasticsearch et émet les nouveaux logs via Socket.IO
"""
import time
import threading
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RealtimeMonitor:
    """
    Moniteur temps réel qui surveille Elasticsearch et émet les événements
    """
    
    def __init__(self, socketio, es_client, alert_monitor=None, interval=5):
        """
        Args:
            socketio: Instance Flask-SocketIO
            es_client: Client Elasticsearch
            alert_monitor: Instance AlertMonitor pour vérification des alertes
            interval: Intervalle de polling en secondes (défaut: 5)
        """
        self.socketio = socketio
        self.es_client = es_client
        self.alert_monitor = alert_monitor
        self.interval = interval
        self.running = False
        self.thread = None
        self.last_check = None
        
    def start(self):
        """Démarre le monitoring en arrière-plan"""
        if not self.running:
            self.running = True
            self.last_check = datetime.now()
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
            logger.info("🔴 Monitoring temps réel démarré")
    
    def stop(self):
        """Arrête le monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("⏹️ Monitoring temps réel arrêté")
    
    def _monitor_loop(self):
        """Boucle de monitoring principale"""
        while self.running:
            try:
                # Récupérer les nouveaux logs depuis le dernier check
                new_logs = self._get_new_logs()
                
                if new_logs:
                    # Émettre les logs via WebSocket
                    self.socketio.emit('new_logs', {
                        'count': len(new_logs),
                        'logs': new_logs,
                        'timestamp': datetime.now().isoformat()
                    }, namespace='/monitoring')
                    
                    logger.debug(f"📡 {len(new_logs)} nouveaux logs émis")
                
                # Émettre les statistiques mises à jour
                stats = self._get_stats()
                self.socketio.emit('stats_update', stats, namespace='/monitoring')
                
                # Vérifier les alertes critiques
                if self.alert_monitor:
                    try:
                        self.alert_monitor.check_alerts()
                    except Exception as e:
                        logger.error(f"❌ Erreur vérification alertes: {e}")
                
                # Mettre à jour le timestamp
                self.last_check = datetime.now()
                
            except Exception as e:
                logger.error(f"❌ Erreur monitoring: {e}")
            
            # Attendre avant le prochain cycle
            time.sleep(self.interval)
    
    def _get_new_logs(self):
        """
        Récupère les logs créés depuis le dernier check
        
        Returns:
            Liste de logs récents
        """
        try:
            # Chercher les logs des dernières X secondes
            time_filter = (self.last_check - timedelta(seconds=self.interval * 2)).isoformat()
            
            query = {
                "query": {
                    "range": {
                        "@timestamp": {
                            "gte": time_filter
                        }
                    }
                },
                "sort": [
                    {"@timestamp": {"order": "desc"}}
                ],
                "size": 20
            }
            
            # Chercher dans les deux indices
            results = self.es_client.client.search(
                index="logs-iot-*",
                body=query
            )
            
            logs = []
            for hit in results['hits']['hits']:
                source = hit['_source']
                log = {
                    'timestamp': source.get('@timestamp', source.get('timestamp', 'N/A')),
                    'zone': source.get('zone', 'Unknown'),
                    'sensor_type': source.get('sensor_type', source.get('event_type', 'alert')),
                    'value': source.get('value', 0),
                    'unit': source.get('unit', ''),
                    'status': source.get('status', source.get('severity', 'info')),
                    'message': source.get('message', ''),
                    'sensor_id': source.get('sensor_id', 'N/A'),
                    'index': hit['_index']
                }
                logs.append(log)
            
            return logs
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération nouveaux logs: {e}")
            return []
    
    def _get_stats(self):
        """
        Récupère les statistiques actuelles
        
        Returns:
            Dict avec les stats
        """
        try:
            stats = {
                'total_logs': self.es_client.get_total_logs(),
                'logs_today': self.es_client.get_logs_today(),
                'errors_count': self.es_client.get_errors_count(),
                'sensors_active': self.es_client.get_sensors_active(),
                'timestamp': datetime.now().isoformat()
            }
            
            # Ajouter les stats par zone
            zones_stats = self._get_zones_activity()
            stats['zones_activity'] = zones_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération stats: {e}")
            return {
                'total_logs': 0,
                'logs_today': 0,
                'errors_count': 0,
                'sensors_active': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_zones_activity(self):
        """
        Récupère l'activité par zone (dernières 5 minutes)
        
        Returns:
            Dict {zone: count}
        """
        try:
            time_filter = (datetime.now() - timedelta(minutes=5)).isoformat()
            
            query = {
                "query": {
                    "range": {
                        "@timestamp": {
                            "gte": time_filter
                        }
                    }
                },
                "aggs": {
                    "zones": {
                        "terms": {
                            "field": "zone",
                            "size": 20
                        }
                    }
                },
                "size": 0
            }
            
            result = self.es_client.client.search(
                index="logs-iot-*",
                body=query
            )
            
            zones = {}
            for bucket in result['aggregations']['zones']['buckets']:
                zones[bucket['key']] = bucket['doc_count']
            
            return zones
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération zones: {e}")
            return {}


class AlertMonitor:
    """
    Moniteur d'alertes en temps réel
    Détecte les alertes critiques et envoie des notifications
    Évalue les règles d'alertes configurables
    """
    
    def __init__(self, socketio, es_client, rules_manager=None):
        self.socketio = socketio
        self.es_client = es_client
        self.rules_manager = rules_manager
        self.last_alert_check = datetime.now()
    
    def check_alerts(self):
        """
        Vérifie les nouvelles alertes critiques
        Évalue les règles d'alertes configurées
        
        Returns:
            Liste d'alertes critiques
        """
        try:
            # 1. Vérification des alertes ES standard (severity critical/high)
            standard_alerts = self._check_standard_alerts()
            
            # 2. Évaluation des règles d'alertes configurables
            rule_triggered_alerts = []
            if self.rules_manager:
                rule_triggered_alerts = self._evaluate_alert_rules()
            
            # Combiner les deux types d'alertes
            all_alerts = standard_alerts + rule_triggered_alerts
            
            if all_alerts:
                # Émettre une notification d'alerte
                self.socketio.emit('critical_alert', {
                    'count': len(all_alerts),
                    'alerts': all_alerts[:10],  # Limiter à 10 pour ne pas surcharger
                    'timestamp': datetime.now().isoformat(),
                    'has_rule_triggers': len(rule_triggered_alerts) > 0
                }, namespace='/monitoring')
            
            self.last_alert_check = datetime.now()
            return all_alerts
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification alertes: {e}")
            return []
    
    def _check_standard_alerts(self):
        """Vérifie les alertes standard ES (severity critical/high)"""
        try:
            time_filter = (self.last_alert_check - timedelta(seconds=10)).isoformat()
            
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": time_filter
                                    }
                                }
                            },
                            {
                                "terms": {
                                    "severity": ["critical", "high"]
                                }
                            }
                        ]
                    }
                },
                "size": 10,
                "sort": [{"@timestamp": {"order": "desc"}}]
            }
            
            result = self.es_client.client.search(
                index="logs-iot-alerts-*",
                body=query
            )
            
            alerts = []
            for hit in result['hits']['hits']:
                source = hit['_source']
                alert = {
                    'timestamp': source.get('@timestamp', 'N/A'),
                    'zone': source.get('zone', 'Unknown'),
                    'severity': source.get('severity', 'unknown'),
                    'message': source.get('message', ''),
                    'value': source.get('value', 0),
                    'sensor_id': source.get('sensor_id', 'N/A'),
                    'source': 'elasticsearch'
                }
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification alertes standard: {e}")
            return []
    
    def _evaluate_alert_rules(self):
        """Évalue les règles d'alertes configurées"""
        try:
            # Récupérer les règles actives
            active_rules = self.rules_manager.get_all_rules(enabled_only=True)
            
            if not active_rules:
                return []
            
            # Récupérer les logs récents pour évaluation
            recent_logs = self._get_recent_logs_for_evaluation()
            
            triggered_alerts = []
            
            for rule in active_rules:
                rule_id = rule['_id']
                
                # Vérifier le cooldown
                if not self.rules_manager.check_cooldown(rule_id):
                    logger.debug(f"⏳ Règle {rule['name']} en cooldown")
                    continue
                
                # Évaluer la règle
                is_triggered, matching_logs = self.rules_manager.evaluate_rule(rule, recent_logs)
                
                if is_triggered and matching_logs:
                    logger.warning(f"🚨 Règle déclenchée: {rule['name']} ({len(matching_logs)} logs)")
                    
                    # Calculer valeur moyenne et zones affectées
                    zones_affected = list(set([log.get('zone', 'Unknown') for log in matching_logs]))
                    values = [log.get('value', 0) for log in matching_logs if log.get('value') is not None]
                    avg_value = sum(values) / len(values) if values else 0
                    
                    # Mettre à jour le timestamp de déclenchement
                    self.rules_manager.update_last_triggered(
                        rule_id,
                        zones_affected=zones_affected,
                        avg_value=avg_value
                    )
                    
                    # Créer l'alerte
                    alert = {
                        'timestamp': datetime.now().isoformat(),
                        'zone': ', '.join(zones_affected),
                        'severity': rule.get('severity', 'medium'),
                        'message': f"[Règle: {rule['name']}] {len(matching_logs)} événement(s) détecté(s)",
                        'value': avg_value,
                        'sensor_id': 'RULE_ENGINE',
                        'source': 'alert_rule',
                        'rule_id': rule_id,
                        'rule_name': rule['name'],
                        'matching_count': len(matching_logs)
                    }
                    
                    triggered_alerts.append(alert)
                    
                    # TODO: Déclencher les actions configurées (email, webhook, etc.)
                    # Pour l'instant, on émet juste via WebSocket
                    self._trigger_rule_actions(rule, matching_logs, avg_value, zones_affected)
            
            return triggered_alerts
            
        except Exception as e:
            logger.error(f"❌ Erreur évaluation règles: {e}")
            return []
    
    def _get_recent_logs_for_evaluation(self, time_window: int = 60):
        """
        Récupère les logs récents pour évaluation des règles
        
        Args:
            time_window: Fenêtre temporelle en secondes (défaut: 60s)
        """
        try:
            time_filter = (datetime.now() - timedelta(seconds=time_window)).isoformat()
            
            query = {
                "query": {
                    "range": {
                        "@timestamp": {
                            "gte": time_filter
                        }
                    }
                },
                "size": 100,  # Limiter pour performance
                "sort": [{"@timestamp": {"order": "desc"}}]
            }
            
            result = self.es_client.client.search(
                index="logs-iot-*",
                body=query
            )
            
            logs = []
            for hit in result['hits']['hits']:
                logs.append(hit['_source'])
            
            return logs
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération logs pour évaluation: {e}")
            return []
    
    def _trigger_rule_actions(self, rule: dict, matching_logs: list, avg_value: float, zones_affected: list):
        """
        Déclenche les actions configurées pour une règle
        
        Args:
            rule: Règle déclenchée
            matching_logs: Logs ayant déclenché la règle
            avg_value: Valeur moyenne
            zones_affected: Zones concernées
        """
        try:
            from utils.notifications import notification_manager
            
            actions = rule.get('actions', [])
            
            for action in actions:
                action_type = action.get('type')
                
                # Log l'action
                logger.info(f"📧 Action {action_type} à déclencher pour règle {rule['name']}")
                
                # Envoyer la notification via le NotificationManager
                try:
                    success = notification_manager.send_notification(
                        action=action,
                        rule=rule,
                        matching_logs=matching_logs,
                        avg_value=avg_value,
                        zones_affected=zones_affected
                    )
                    
                    if success:
                        logger.info(f"✅ Notification {action_type} envoyée pour {rule['name']}")
                    else:
                        logger.warning(f"⚠️ Notification {action_type} non envoyée pour {rule['name']}")
                        
                except Exception as e:
                    logger.error(f"❌ Erreur notification {action_type}: {e}")
            
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement actions: {e}")

