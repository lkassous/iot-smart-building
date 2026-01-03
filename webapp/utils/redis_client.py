"""
Client Redis pour IoT Smart Building
Gère le cache et les sessions
"""
import redis
import json
import logging
from functools import wraps
from config import get_config

logger = logging.getLogger(__name__)

class RedisClient:
    """Client Redis avec méthodes de cache"""
    
    def __init__(self):
        config = get_config()
        self.host = config.REDIS_HOST
        self.port = config.REDIS_PORT
        self.cache_ttl = config.REDIS_CACHE_TTL
        
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test de connexion
            self.client.ping()
            logger.info(f"✅ Connecté à Redis: {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"❌ Erreur connexion Redis: {e}")
            self.client = None
    
    def is_connected(self):
        """Vérifie si la connexion est active"""
        if not self.client:
            return False
        try:
            return self.client.ping()
        except:
            return False
    
    # ========================================================================
    # MÉTHODES DE CACHE GÉNÉRIQUES
    # ========================================================================
    
    def get(self, key):
        """
        Récupère une valeur depuis le cache
        
        Args:
            key: Clé du cache
        
        Returns:
            dict/list/str: Valeur désérialisée ou None
        """
        try:
            if not self.client:
                return None
            
            value = self.client.get(key)
            if value:
                # Tenter de désérialiser JSON
                try:
                    return json.loads(value)
                except:
                    return value
            return None
        except Exception as e:
            logger.error(f"Erreur Redis GET {key}: {e}")
            return None
    
    def set(self, key, value, ttl=None):
        """
        Stocke une valeur dans le cache
        
        Args:
            key: Clé du cache
            value: Valeur à stocker (dict/list/str)
            ttl: Temps de vie en secondes (par défaut: config.REDIS_CACHE_TTL)
        
        Returns:
            bool: True si succès
        """
        try:
            if not self.client:
                return False
            
            # Sérialiser les objets complexes
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            ttl = ttl or self.cache_ttl
            self.client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Erreur Redis SET {key}: {e}")
            return False
    
    def delete(self, key):
        """Supprime une clé du cache"""
        try:
            if not self.client:
                return False
            
            return self.client.delete(key) > 0
        except Exception as e:
            logger.error(f"Erreur Redis DELETE {key}: {e}")
            return False
    
    def exists(self, key):
        """Vérifie si une clé existe"""
        try:
            if not self.client:
                return False
            
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Erreur Redis EXISTS {key}: {e}")
            return False
    
    def flush_all(self):
        """Vide tout le cache (ATTENTION: utiliser avec précaution)"""
        try:
            if not self.client:
                return False
            
            self.client.flushall()
            logger.warning("⚠️ Cache Redis vidé complètement")
            return True
        except Exception as e:
            logger.error(f"Erreur Redis FLUSHALL: {e}")
            return False
    
    # ========================================================================
    # MÉTHODES SPÉCIFIQUES POUR LES STATISTIQUES
    # ========================================================================
    
    def cache_stats(self, stats_data, ttl=None):
        """
        Cache les statistiques du dashboard
        
        Args:
            stats_data: Dictionnaire des stats
            ttl: Temps de vie (par défaut: 5 minutes)
        """
        return self.set('dashboard:stats', stats_data, ttl or 300)
    
    def get_cached_stats(self):
        """Récupère les stats en cache"""
        return self.get('dashboard:stats')
    
    def cache_search_results(self, query_hash, results, ttl=None):
        """
        Cache les résultats d'une recherche
        
        Args:
            query_hash: Hash unique de la requête
            results: Résultats de la recherche
            ttl: Temps de vie (par défaut: config.REDIS_CACHE_TTL)
        """
        key = f'search:{query_hash}'
        return self.set(key, results, ttl)
    
    def get_cached_search(self, query_hash):
        """Récupère les résultats de recherche en cache"""
        key = f'search:{query_hash}'
        return self.get(key)
    
    # ========================================================================
    # COMPTEURS ET INCRÉMENTS
    # ========================================================================
    
    def increment_counter(self, key, amount=1):
        """
        Incrémente un compteur
        
        Args:
            key: Clé du compteur
            amount: Montant à incrémenter
        
        Returns:
            int: Nouvelle valeur du compteur
        """
        try:
            if not self.client:
                return 0
            
            return self.client.incr(key, amount)
        except Exception as e:
            logger.error(f"Erreur Redis INCR {key}: {e}")
            return 0
    
    def get_counter(self, key):
        """Récupère la valeur d'un compteur"""
        try:
            if not self.client:
                return 0
            
            value = self.client.get(key)
            return int(value) if value else 0
        except Exception as e:
            logger.error(f"Erreur Redis GET counter {key}: {e}")
            return 0
    
    # ========================================================================
    # GESTION DES SESSIONS
    # ========================================================================
    
    def set_session(self, session_id, data, ttl=3600):
        """
        Stocke les données de session
        
        Args:
            session_id: ID de la session
            data: Données à stocker
            ttl: Durée de vie en secondes (par défaut: 1 heure)
        """
        key = f'session:{session_id}'
        return self.set(key, data, ttl)
    
    def get_session(self, session_id):
        """Récupère les données de session"""
        key = f'session:{session_id}'
        return self.get(key)
    
    def delete_session(self, session_id):
        """Supprime une session"""
        key = f'session:{session_id}'
        return self.delete(key)


# ========================================================================
# DÉCORATEUR POUR CACHE AUTOMATIQUE
# ========================================================================

def cache_result(key_prefix, ttl=None):
    """
    Décorateur pour cacher automatiquement le résultat d'une fonction
    
    Usage:
        @cache_result('my_function', ttl=300)
        def my_function(arg1, arg2):
            # Calcul coûteux
            return result
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Créer une clé unique basée sur les arguments
            cache_key = f'{key_prefix}:{str(args)}:{str(kwargs)}'
            
            # Essayer de récupérer depuis le cache
            cached = redis_client.get(cache_key)
            if cached is not None:
                logger.debug(f"🎯 Cache HIT: {cache_key}")
                return cached
            
            # Si pas en cache, exécuter la fonction
            logger.debug(f"❌ Cache MISS: {cache_key}")
            result = func(*args, **kwargs)
            
            # Mettre en cache le résultat
            redis_client.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


# Instance globale
redis_client = RedisClient()
