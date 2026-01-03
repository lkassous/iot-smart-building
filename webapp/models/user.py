"""
Modèle utilisateur pour Flask-Login
Gestion de l'authentification et des rôles
"""
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin):
    """Modèle utilisateur avec rôles"""
    
    def __init__(self, user_id, username, email, password_hash, role='viewer', active=True):
        self.id = str(user_id)
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role  # admin, user, viewer
        self.active = active
        self.created_at = datetime.utcnow()
        self.last_login = None
    
    def set_password(self, password):
        """Hash et sauvegarde le mot de passe"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Vérifie le mot de passe"""
        return check_password_hash(self.password_hash, password)
    
    def is_active(self):
        """Requis par Flask-Login"""
        return self.active
    
    def has_permission(self, permission):
        """Vérifie si l'utilisateur a une permission"""
        permissions = {
            'admin': ['read', 'write', 'delete', 'manage_users'],
            'user': ['read', 'write'],
            'viewer': ['read']
        }
        return permission in permissions.get(self.role, [])
    
    def to_dict(self):
        """Conversion en dictionnaire"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    @staticmethod
    def from_dict(data):
        """Création depuis un dictionnaire"""
        return User(
            user_id=data.get('_id', data.get('id')),
            username=data['username'],
            email=data['email'],
            password_hash=data['password_hash'],
            role=data.get('role', 'viewer'),
            active=data.get('active', True)
        )


# Utilisateurs par défaut (pour démo)
DEFAULT_USERS = [
    {
        'username': 'admin',
        'email': 'admin@iot-building.local',
        'password': 'admin123',  # À changer en production !
        'role': 'admin'
    },
    {
        'username': 'user',
        'email': 'user@iot-building.local',
        'password': 'user123',
        'role': 'user'
    },
    {
        'username': 'viewer',
        'email': 'viewer@iot-building.local',
        'password': 'viewer123',
        'role': 'viewer'
    }
]
