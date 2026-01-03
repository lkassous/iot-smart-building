"""
Client MongoDB pour IoT Smart Building
Gère les métadonnées des fichiers et l'historique des recherches
"""
from pymongo import MongoClient
from datetime import datetime
import logging
from config import get_config

logger = logging.getLogger(__name__)

class MongoDBClient:
    """Client MongoDB avec méthodes utilitaires"""
    
    def __init__(self):
        config = get_config()
        self.uri = config.MONGODB_URI
        self.db_name = config.MONGODB_DB
        
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Test de connexion
            self.client.server_info()
            self.db = self.client[self.db_name]
            logger.info(f"✅ Connecté à MongoDB: {self.db_name}")
        except Exception as e:
            logger.error(f"❌ Erreur connexion MongoDB: {e}")
            self.client = None
            self.db = None
    
    def is_connected(self):
        """Vérifie si la connexion est active"""
        if not self.client:
            return False
        try:
            self.client.server_info()
            return True
        except:
            return False
    
    # ========================================================================
    # GESTION DES FICHIERS UPLOADÉS
    # ========================================================================
    
    def save_file_metadata(self, filename, file_size, file_type, status='uploaded', 
                          num_logs=0, processing_time=0, errors=None):
        """
        Sauvegarde les métadonnées d'un fichier uploadé
        
        Args:
            filename: Nom du fichier
            file_size: Taille en bytes
            file_type: Type (csv, json, txt)
            status: uploaded, processing, processed, error
            num_logs: Nombre de logs dans le fichier
            processing_time: Temps de traitement en secondes
            errors: Liste des erreurs éventuelles
        
        Returns:
            str: ID du document créé
        """
        try:
            metadata = {
                'filename': filename,
                'original_name': filename,
                'upload_date': datetime.utcnow(),
                'file_size': file_size,
                'file_type': file_type,
                'status': status,
                'num_logs': num_logs,
                'processing_time': processing_time,
                'errors': errors or [],
                'logstash_pipeline': 'csv-pipeline' if file_type == 'csv' else 'json-pipeline'
            }
            
            result = self.db.uploaded_files.insert_one(metadata)
            logger.info(f"📄 Métadonnées fichier sauvegardées: {filename}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Erreur save_file_metadata: {e}")
            return None
    
    def update_file_status(self, filename, status, num_logs=None, processing_time=None, errors=None):
        """Met à jour le statut d'un fichier"""
        try:
            update_data = {'status': status, 'updated_at': datetime.utcnow()}
            
            if num_logs is not None:
                update_data['num_logs'] = num_logs
            if processing_time is not None:
                update_data['processing_time'] = processing_time
            if errors is not None:
                update_data['errors'] = errors
            
            result = self.db.uploaded_files.update_one(
                {'filename': filename},
                {'$set': update_data}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Erreur update_file_status: {e}")
            return False
    
    def get_uploaded_files(self, limit=100, skip=0):
        """
        Récupère la liste des fichiers uploadés
        
        Returns:
            list: Liste des métadonnées de fichiers
        """
        try:
            files = list(
                self.db.uploaded_files
                .find()
                .sort('upload_date', -1)
                .skip(skip)
                .limit(limit)
            )
            
            # Convertir ObjectId en string
            for file in files:
                file['_id'] = str(file['_id'])
            
            return files
        except Exception as e:
            logger.error(f"Erreur get_uploaded_files: {e}")
            return []
    
    def get_files_count(self):
        """Récupère le nombre total de fichiers uploadés"""
        try:
            return self.db.uploaded_files.count_documents({})
        except Exception as e:
            logger.error(f"Erreur get_files_count: {e}")
            return 0
    
    # ========================================================================
    # GESTION DE L'HISTORIQUE DES RECHERCHES
    # ========================================================================
    
    def save_search_history(self, query, filters, num_results, execution_time, user_id=None):
        """
        Sauvegarde une recherche dans l'historique
        
        Args:
            query: Texte de la recherche
            filters: Dictionnaire des filtres appliqués
            num_results: Nombre de résultats
            execution_time: Temps d'exécution en secondes
            user_id: ID de l'utilisateur (optionnel)
        
        Returns:
            str: ID de l'historique créé
        """
        try:
            search = {
                'user_id': user_id or 'anonymous',
                'query': query or '',
                'filters': filters or {},
                'num_results': num_results,
                'execution_time': execution_time,
                'timestamp': datetime.utcnow()
            }
            
            result = self.db.search_history.insert_one(search)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Erreur save_search_history: {e}")
            return None
    
    def get_search_history(self, limit=20, user_id=None):
        """
        Récupère l'historique des recherches
        
        Args:
            limit: Nombre de recherches à récupérer
            user_id: Filtrer par utilisateur
        
        Returns:
            list: Liste des recherches
        """
        try:
            query = {}
            if user_id:
                query['user_id'] = user_id
            
            searches = list(
                self.db.search_history
                .find(query)
                .sort('timestamp', -1)
                .limit(limit)
            )
            
            # Convertir ObjectId en string
            for search in searches:
                search['_id'] = str(search['_id'])
            
            return searches
        except Exception as e:
            logger.error(f"Erreur get_search_history: {e}")
            return []
    
    def get_popular_searches(self, limit=10):
        """Récupère les recherches les plus fréquentes"""
        try:
            pipeline = [
                {"$match": {"query": {"$ne": ""}}},
                {"$group": {
                    "_id": "$query",
                    "count": {"$sum": 1},
                    "avg_results": {"$avg": "$num_results"},
                    "last_search": {"$max": "$timestamp"}
                }},
                {"$sort": {"count": -1}},
                {"$limit": limit}
            ]
            
            results = list(self.db.search_history.aggregate(pipeline))
            return results
        except Exception as e:
            logger.error(f"Erreur get_popular_searches: {e}")
            return []


# Instance globale
mongo_client = MongoDBClient()
