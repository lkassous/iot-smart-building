"""
Gestionnaire des règles d'alertes intelligentes
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from bson import ObjectId

logger = logging.getLogger(__name__)


class AlertRulesManager:
    """
    Gestionnaire centralisé pour les règles d'alertes
    
    Responsabilités:
    - CRUD des règles d'alertes
    - Évaluation des règles contre les données
    - Gestion du cooldown
    - Statistiques de déclenchement
    """
    
    def __init__(self, mongo_db, es_client=None):
        """
        Args:
            mongo_db: Instance de base MongoDB
            es_client: Client Elasticsearch pour requêtes avancées (optionnel)
        """
        self.db = mongo_db
        self.collection = self.db.alert_rules
        self.es_client = es_client
        
        # Créer les index MongoDB pour performance
        self._create_indexes()
    
    def _create_indexes(self):
        """Crée les index MongoDB pour optimiser les requêtes"""
        try:
            self.collection.create_index('name', unique=True)
            self.collection.create_index('enabled')
            self.collection.create_index([('enabled', 1), ('severity', 1)])
            self.collection.create_index('last_triggered')
            logger.info("✅ Index MongoDB créés pour alert_rules")
        except Exception as e:
            logger.warning(f"Index MongoDB déjà existants: {e}")
    
    # ==================== CRUD Operations ====================
    
    def create_rule(self, rule: Dict) -> Tuple[bool, str, Optional[str]]:
        """
        Crée une nouvelle règle d'alerte
        
        Args:
            rule: Dictionnaire contenant la règle
            
        Returns:
            tuple: (success, message, rule_id)
        """
        from models.alert_rule import AlertRule
        
        try:
            # Validation
            is_valid, error = AlertRule.validate_rule(rule)
            if not is_valid:
                return False, error, None
            
            # Vérifier unicité du nom
            if self.collection.find_one({'name': rule['name']}):
                return False, f"Une règle avec le nom '{rule['name']}' existe déjà", None
            
            # Ajouter métadonnées
            rule['created_at'] = datetime.now()
            rule['updated_at'] = datetime.now()
            rule['last_triggered'] = None
            rule['trigger_count'] = 0
            
            if 'stats' not in rule:
                rule['stats'] = {
                    'total_triggers': 0,
                    'last_7_days_triggers': 0,
                    'avg_value_on_trigger': 0,
                    'zones_affected': []
                }
            
            # Insérer dans MongoDB
            result = self.collection.insert_one(rule)
            rule_id = str(result.inserted_id)
            
            logger.info(f"✅ Règle créée: {rule['name']} (ID: {rule_id})")
            return True, "Règle créée avec succès", rule_id
            
        except Exception as e:
            logger.error(f"❌ Erreur création règle: {e}")
            return False, str(e), None
    
    def get_rule(self, rule_id: str) -> Optional[Dict]:
        """
        Récupère une règle par son ID
        
        Args:
            rule_id: ID de la règle (string)
            
        Returns:
            Dictionnaire de la règle ou None
        """
        try:
            rule = self.collection.find_one({'_id': ObjectId(rule_id)})
            if rule:
                rule['_id'] = str(rule['_id'])  # Convertir ObjectId en string
            return rule
        except Exception as e:
            logger.error(f"❌ Erreur récupération règle {rule_id}: {e}")
            return None
    
    def get_all_rules(self, enabled_only: bool = False) -> List[Dict]:
        """
        Récupère toutes les règles
        
        Args:
            enabled_only: Si True, retourne uniquement les règles actives
            
        Returns:
            Liste de règles
        """
        try:
            query = {'enabled': True} if enabled_only else {}
            rules = list(self.collection.find(query).sort('priority', 1))
            
            # Convertir ObjectId en string
            for rule in rules:
                rule['_id'] = str(rule['_id'])
            
            return rules
        except Exception as e:
            logger.error(f"❌ Erreur récupération règles: {e}")
            return []
    
    def update_rule(self, rule_id: str, updates: Dict) -> Tuple[bool, str]:
        """
        Met à jour une règle existante
        
        Args:
            rule_id: ID de la règle
            updates: Dictionnaire des champs à mettre à jour
            
        Returns:
            tuple: (success, message)
        """
        from models.alert_rule import AlertRule
        
        try:
            # Récupérer la règle actuelle
            current_rule = self.get_rule(rule_id)
            if not current_rule:
                return False, "Règle non trouvée"
            
            # Fusionner avec les updates
            updated_rule = {**current_rule, **updates}
            
            # Validation
            is_valid, error = AlertRule.validate_rule(updated_rule)
            if not is_valid:
                return False, error
            
            # Mettre à jour updated_at
            updates['updated_at'] = datetime.now()
            
            # Update dans MongoDB
            result = self.collection.update_one(
                {'_id': ObjectId(rule_id)},
                {'$set': updates}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Règle mise à jour: {rule_id}")
                return True, "Règle mise à jour avec succès"
            else:
                return False, "Aucune modification effectuée"
                
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour règle {rule_id}: {e}")
            return False, str(e)
    
    def delete_rule(self, rule_id: str) -> Tuple[bool, str]:
        """
        Supprime une règle
        
        Args:
            rule_id: ID de la règle
            
        Returns:
            tuple: (success, message)
        """
        try:
            result = self.collection.delete_one({'_id': ObjectId(rule_id)})
            
            if result.deleted_count > 0:
                logger.info(f"✅ Règle supprimée: {rule_id}")
                return True, "Règle supprimée avec succès"
            else:
                return False, "Règle non trouvée"
                
        except Exception as e:
            logger.error(f"❌ Erreur suppression règle {rule_id}: {e}")
            return False, str(e)
    
    def toggle_rule(self, rule_id: str) -> Tuple[bool, str, bool]:
        """
        Active/Désactive une règle
        
        Args:
            rule_id: ID de la règle
            
        Returns:
            tuple: (success, message, new_state)
        """
        try:
            rule = self.get_rule(rule_id)
            if not rule:
                return False, "Règle non trouvée", False
            
            new_state = not rule.get('enabled', False)
            
            result = self.collection.update_one(
                {'_id': ObjectId(rule_id)},
                {'$set': {'enabled': new_state, 'updated_at': datetime.now()}}
            )
            
            if result.modified_count > 0:
                state_str = "activée" if new_state else "désactivée"
                logger.info(f"✅ Règle {state_str}: {rule['name']}")
                return True, f"Règle {state_str}", new_state
            else:
                return False, "Erreur lors du changement d'état", rule.get('enabled', False)
                
        except Exception as e:
            logger.error(f"❌ Erreur toggle règle {rule_id}: {e}")
            return False, str(e), False
    
    # ==================== Rule Evaluation ====================
    
    def evaluate_rule(self, rule: Dict, logs: List[Dict]) -> Tuple[bool, List[Dict]]:
        """
        Évalue une règle contre un ensemble de logs
        
        Args:
            rule: Règle à évaluer
            logs: Liste de logs récents
            
        Returns:
            tuple: (rule_triggered, matching_logs)
        """
        if not rule.get('enabled', False):
            return False, []
        
        rule_type = rule.get('rule_type', 'threshold')
        
        try:
            if rule_type == 'threshold':
                return self._evaluate_threshold(rule, logs)
            elif rule_type == 'range':
                return self._evaluate_range(rule, logs)
            elif rule_type == 'pattern':
                return self._evaluate_pattern(rule, logs)
            elif rule_type == 'trend':
                return self._evaluate_trend(rule, logs)
            else:
                logger.warning(f"Type de règle inconnu: {rule_type}")
                return False, []
                
        except Exception as e:
            logger.error(f"❌ Erreur évaluation règle {rule.get('name')}: {e}")
            return False, []
    
    def _evaluate_threshold(self, rule: Dict, logs: List[Dict]) -> Tuple[bool, List[Dict]]:
        """Évalue une règle de type threshold"""
        conditions = rule.get('conditions', {})
        field = conditions.get('field', 'value')
        operator = conditions.get('operator', '>')
        threshold = conditions.get('threshold', 0)
        
        # Filtrer les logs selon les conditions
        matching_logs = self._filter_logs(logs, conditions.get('filters', {}))
        
        # Vérifier le seuil
        triggered_logs = []
        for log in matching_logs:
            value = log.get(field)
            if value is None:
                continue
            
            triggered = False
            if operator == '>' and value > threshold:
                triggered = True
            elif operator == '<' and value < threshold:
                triggered = True
            elif operator == '>=' and value >= threshold:
                triggered = True
            elif operator == '<=' and value <= threshold:
                triggered = True
            elif operator == '==' and value == threshold:
                triggered = True
            elif operator == '!=' and value != threshold:
                triggered = True
            
            if triggered:
                triggered_logs.append(log)
        
        return len(triggered_logs) > 0, triggered_logs
    
    def _evaluate_range(self, rule: Dict, logs: List[Dict]) -> Tuple[bool, List[Dict]]:
        """Évalue une règle de type range (valeur hors plage)"""
        conditions = rule.get('conditions', {})
        field = conditions.get('field', 'value')
        min_value = conditions.get('min_value', 0)
        max_value = conditions.get('max_value', 100)
        
        matching_logs = self._filter_logs(logs, conditions.get('filters', {}))
        
        # Logs hors de la plage [min, max]
        out_of_range_logs = []
        for log in matching_logs:
            value = log.get(field)
            if value is None:
                continue
            
            if value < min_value or value > max_value:
                out_of_range_logs.append(log)
        
        return len(out_of_range_logs) > 0, out_of_range_logs
    
    def _evaluate_pattern(self, rule: Dict, logs: List[Dict]) -> Tuple[bool, List[Dict]]:
        """Évalue une règle de type pattern (N events dans fenêtre temps)"""
        conditions = rule.get('conditions', {})
        time_window = conditions.get('time_window', 300)  # 5 minutes par défaut
        event_count = conditions.get('event_count', 3)
        
        matching_logs = self._filter_logs(logs, conditions.get('filters', {}))
        
        # Vérifier si assez d'events dans la fenêtre
        if len(matching_logs) >= event_count:
            # Vérifier que tous les events sont dans la fenêtre temporelle
            now = datetime.now()
            cutoff_time = now - timedelta(seconds=time_window)
            
            recent_logs = [
                log for log in matching_logs
                if self._parse_timestamp(log.get('timestamp', log.get('@timestamp'))) >= cutoff_time
            ]
            
            if len(recent_logs) >= event_count:
                return True, recent_logs[:event_count]
        
        return False, []
    
    def _evaluate_trend(self, rule: Dict, logs: List[Dict]) -> Tuple[bool, List[Dict]]:
        """Évalue une règle de type trend (variation anormale)"""
        # TODO: Implémenter logique de détection de tendance
        # Nécessite calcul de delta/variance sur fenêtre temporelle
        return False, []
    
    def _filter_logs(self, logs: List[Dict], filters: Dict) -> List[Dict]:
        """Filtre les logs selon les critères"""
        filtered = logs
        
        # Filtre par zone
        if filters.get('zone') and len(filters['zone']) > 0:
            filtered = [log for log in filtered if log.get('zone') in filters['zone']]
        
        # Filtre par type de capteur
        if filters.get('sensor_type') and len(filters['sensor_type']) > 0:
            filtered = [log for log in filtered if log.get('sensor_type') in filters['sensor_type']]
        
        # Filtre par statut
        if filters.get('status') and len(filters['status']) > 0:
            filtered = [log for log in filtered if log.get('status') in filters['status']]
        
        # Filtre par bâtiment (gère le cas où building est une liste ou une string)
        if filters.get('building'):
            target_building = filters['building']
            def match_building(log):
                building_val = log.get('building')
                if building_val is None:
                    return False
                if isinstance(building_val, list):
                    return target_building in building_val
                return building_val == target_building
            filtered = [log for log in filtered if match_building(log)]
        
        return filtered
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse un timestamp ISO"""
        try:
            # Supprimer le 'Z' et les microsecondes excédentaires
            ts = timestamp_str.replace('Z', '').split('.')[0]
            return datetime.fromisoformat(ts)
        except:
            return datetime.now()
    
    # ==================== Cooldown Management ====================
    
    def check_cooldown(self, rule_id: str) -> bool:
        """
        Vérifie si le cooldown d'une règle est expiré
        
        Args:
            rule_id: ID de la règle
            
        Returns:
            True si la règle peut être déclenchée, False sinon
        """
        try:
            rule = self.get_rule(rule_id)
            if not rule:
                return False
            
            last_triggered = rule.get('last_triggered')
            if not last_triggered:
                return True  # Jamais déclenchée
            
            cooldown = rule.get('cooldown', 300)  # 5 min par défaut
            now = datetime.now()
            
            time_since_last = (now - last_triggered).total_seconds()
            
            return time_since_last >= cooldown
            
        except Exception as e:
            logger.error(f"❌ Erreur check cooldown {rule_id}: {e}")
            return False
    
    def update_last_triggered(self, rule_id: str, zones_affected: List[str] = None, avg_value: float = None):
        """
        Met à jour le timestamp de dernier déclenchement
        
        Args:
            rule_id: ID de la règle
            zones_affected: Zones concernées par le déclenchement
            avg_value: Valeur moyenne ayant déclenché la règle
        """
        try:
            now = datetime.now()
            
            # Récupérer la règle actuelle
            rule = self.get_rule(rule_id)
            if not rule:
                logger.error(f"❌ Règle {rule_id} non trouvée pour update")
                return
            
            # Calculer les nouvelles stats
            stats = rule.get('stats', {})
            current_trigger_count = rule.get('trigger_count', 0) + 1
            stats['total_triggers'] = stats.get('total_triggers', 0) + 1
            
            if zones_affected:
                current_zones = set(stats.get('zones_affected', []))
                current_zones.update(zones_affected)
                stats['zones_affected'] = list(current_zones)
            
            if avg_value is not None:
                # Moyenne mobile
                current_avg = stats.get('avg_value_on_trigger', 0)
                total = stats['total_triggers']
                if total > 1:
                    stats['avg_value_on_trigger'] = (current_avg * (total - 1) + avg_value) / total
                else:
                    stats['avg_value_on_trigger'] = avg_value
            
            # Mise à jour avec $set et $inc séparés
            self.collection.update_one(
                {'_id': ObjectId(rule_id)},
                {
                    '$set': {
                        'last_triggered': now,
                        'stats': stats
                    },
                    '$inc': {
                        'trigger_count': 1
                    }
                }
            )
            
            logger.info(f"✅ Règle {rule['name']} - Trigger #{current_trigger_count} enregistré")
            
        except Exception as e:
            logger.error(f"❌ Erreur update last_triggered {rule_id}: {e}")
    
    # ==================== Statistics ====================
    
    def get_rules_stats(self) -> Dict:
        """Retourne des statistiques globales sur les règles"""
        try:
            total_rules = self.collection.count_documents({})
            enabled_rules = self.collection.count_documents({'enabled': True})
            
            # Règles par sévérité
            severity_counts = {}
            for severity in ['low', 'medium', 'high', 'critical']:
                count = self.collection.count_documents({'severity': severity, 'enabled': True})
                severity_counts[severity] = count
            
            # Règles les plus déclenchées
            top_triggered = list(
                self.collection.find({'enabled': True})
                .sort('trigger_count', -1)
                .limit(5)
            )
            
            for rule in top_triggered:
                rule['_id'] = str(rule['_id'])
            
            return {
                'total_rules': total_rules,
                'enabled_rules': enabled_rules,
                'disabled_rules': total_rules - enabled_rules,
                'by_severity': severity_counts,
                'top_triggered': top_triggered
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur stats règles: {e}")
            return {}
