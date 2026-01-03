"""
Gestionnaire d'utilisateurs avec MongoDB
CRUD operations pour les utilisateurs
"""
from models.user import User, DEFAULT_USERS
from werkzeug.security import generate_password_hash
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UserManager:
    """Gestionnaire d'utilisateurs"""
    
    def __init__(self, mongo_client):
        self.mongo_client = mongo_client
        self.db = mongo_client.db
        self.users_collection = self.db.users if self.db is not None else None
        
        # Créer les utilisateurs par défaut si la collection est vide
        if self.users_collection is not None:
            self._init_default_users()
    
    def _init_default_users(self):
        """Initialise les utilisateurs par défaut"""
        try:
            if self.users_collection.count_documents({}) == 0:
                logger.info("📝 Création des utilisateurs par défaut...")
                for user_data in DEFAULT_USERS:
                    self.create_user(
                        username=user_data['username'],
                        email=user_data['email'],
                        password=user_data['password'],
                        role=user_data['role']
                    )
                logger.info("✅ Utilisateurs par défaut créés")
        except Exception as e:
            logger.error(f"Erreur initialisation utilisateurs: {e}")
    
    def create_user(self, username, email, password, role='viewer'):
        """Crée un nouvel utilisateur"""
        try:
            # Vérifier si l'utilisateur existe déjà
            if self.users_collection.find_one({'username': username}):
                logger.warning(f"Utilisateur {username} existe déjà")
                return None
            
            user_doc = {
                'username': username,
                'email': email,
                'password_hash': generate_password_hash(password),
                'role': role,
                'active': True,
                'created_at': datetime.utcnow(),
                'last_login': None
            }
            
            result = self.users_collection.insert_one(user_doc)
            logger.info(f"✅ Utilisateur créé: {username} (role: {role})")
            
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Erreur création utilisateur: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """Récupère un utilisateur par son ID"""
        try:
            from bson.objectid import ObjectId
            user_doc = self.users_collection.find_one({'_id': ObjectId(user_id)})
            if user_doc:
                return User.from_dict(user_doc)
            return None
        except Exception as e:
            logger.error(f"Erreur get_user_by_id: {e}")
            return None
    
    def get_user_by_username(self, username):
        """Récupère un utilisateur par son nom d'utilisateur"""
        try:
            user_doc = self.users_collection.find_one({'username': username})
            if user_doc:
                return User.from_dict(user_doc)
            return None
        except Exception as e:
            logger.error(f"Erreur get_user_by_username: {e}")
            return None
    
    def update_last_login(self, user_id):
        """Met à jour la date de dernière connexion"""
        try:
            from bson.objectid import ObjectId
            self.users_collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'last_login': datetime.utcnow()}}
            )
        except Exception as e:
            logger.error(f"Erreur update_last_login: {e}")
    
    def get_all_users(self):
        """Récupère tous les utilisateurs"""
        try:
            users_docs = list(self.users_collection.find())
            users = [User.from_dict(doc) for doc in users_docs]
            return users
        except Exception as e:
            logger.error(f"Erreur get_all_users: {e}")
            return []
    
    def update_user_role(self, user_id, new_role):
        """Met à jour le rôle d'un utilisateur"""
        try:
            from bson.objectid import ObjectId
            result = self.users_collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'role': new_role}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Erreur update_user_role: {e}")
            return False
    
    def delete_user(self, user_id):
        """Supprime un utilisateur"""
        try:
            from bson.objectid import ObjectId
            result = self.users_collection.delete_one({'_id': ObjectId(user_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Erreur delete_user: {e}")
            return False
    
    def get_user_by_email(self, email):
        """Récupère un utilisateur par email"""
        try:
            user_doc = self.users_collection.find_one({'email': email})
            if user_doc:
                return User.from_dict(user_doc)
            return None
        except Exception as e:
            logger.error(f"Erreur get_user_by_email: {e}")
            return None
    
    def update_user_email(self, user_id, new_email):
        """Met à jour l'email d'un utilisateur"""
        try:
            from bson.objectid import ObjectId
            result = self.users_collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'email': new_email}}
            )
            logger.info(f"📧 Email mis à jour pour utilisateur {user_id}")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Erreur update_user_email: {e}")
            return False
    
    def update_user_password(self, user_id, new_password):
        """Met à jour le mot de passe d'un utilisateur"""
        try:
            from bson.objectid import ObjectId
            password_hash = generate_password_hash(new_password)
            result = self.users_collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'password_hash': password_hash}}
            )
            logger.info(f"🔐 Mot de passe mis à jour pour utilisateur {user_id}")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Erreur update_user_password: {e}")
            return False


# Instance globale (sera initialisée dans app.py)
user_manager = None
