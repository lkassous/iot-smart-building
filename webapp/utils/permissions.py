"""
Décorateurs et utilitaires pour la gestion des permissions
"""
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def permission_required(permission):
    """
    Décorateur pour vérifier qu'un utilisateur a une permission spécifique
    
    Usage:
        @permission_required('write')
        def upload_file():
            ...
    
    Permissions disponibles:
        - 'read': Lecture des données (viewer, user, admin)
        - 'write': Écriture/upload (user, admin)
        - 'admin': Administration complète (admin uniquement)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if not current_user.has_permission(permission):
                flash(f'Accès refusé. Permission requise: {permission}', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def role_required(*roles):
    """
    Décorateur pour vérifier qu'un utilisateur a un rôle spécifique
    
    Usage:
        @role_required('admin')
        def admin_panel():
            ...
        
        @role_required('admin', 'user')
        def upload_file():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if current_user.role not in roles:
                flash(f'Accès refusé. Rôle requis: {", ".join(roles)}', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """
    Décorateur raccourci pour vérifier que l'utilisateur est admin
    
    Usage:
        @admin_required
        def delete_user():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if current_user.role != 'admin':
            flash('Accès refusé. Droits administrateur requis.', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def get_user_permissions(user):
    """
    Retourne la liste des permissions d'un utilisateur
    """
    permissions = {
        'admin': ['read', 'write', 'delete', 'admin', 'manage_users'],
        'user': ['read', 'write'],
        'viewer': ['read']
    }
    return permissions.get(user.role, [])


def can_edit_user(current_user, target_user):
    """
    Vérifie si l'utilisateur courant peut modifier un autre utilisateur
    
    Règles:
    - Admin peut modifier tout le monde
    - User peut modifier son propre profil uniquement
    - Viewer ne peut modifier personne
    """
    if current_user.role == 'admin':
        return True
    
    if current_user.id == target_user.id:
        # Un utilisateur peut toujours modifier son propre profil (email, mot de passe)
        # mais pas son rôle
        return True
    
    return False
