"""
Routes d'authentification (login, logout)
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)

# user_manager sera injecté depuis app.py
user_manager = None

def init_auth_routes(um):
    """Initialise les routes avec le user_manager"""
    global user_manager
    user_manager = um

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Page de connexion et traitement de l'authentification
    ---
    tags:
      - Authentication
    parameters:
      - name: username
        in: formData
        type: string
        required: true
        description: Nom d'utilisateur
      - name: password
        in: formData
        type: string
        required: true
        description: Mot de passe
      - name: remember
        in: formData
        type: boolean
        required: false
        description: Se souvenir de moi
    responses:
      200:
        description: Page de login (GET) ou redirection après succès (POST)
      302:
        description: Redirection vers dashboard si déjà authentifié
      401:
        description: Identifiants incorrects
    """
    # Si déjà connecté, rediriger vers dashboard
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False) == 'on'
        
        # Validation
        if not username or not password:
            flash('Veuillez remplir tous les champs', 'danger')
            return render_template('login.html')
        
        # Récupérer l'utilisateur
        user = user_manager.get_user_by_username(username)
        
        if user and user.check_password(password):
            # Vérifier si le compte est actif
            if not user.active:
                flash('Votre compte est désactivé. Contactez un administrateur.', 'warning')
                return render_template('login.html')
            
            # Authentifier l'utilisateur
            login_user(user, remember=remember)
            
            # Mettre à jour la dernière connexion
            user_manager.update_last_login(user.id)
            
            # Rediriger vers la page demandée ou dashboard
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                flash(f'Bienvenue {user.username} !', 'success')
                return redirect(next_page)
            else:
                flash(f'Bienvenue {user.username} !', 'success')
                return redirect(url_for('index'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'danger')
            return render_template('login.html')
    
    # GET: Afficher le formulaire de login
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """
    Déconnexion de l'utilisateur
    ---
    tags:
      - Authentication
    responses:
      302:
        description: Redirection vers la page de login
    """
    username = current_user.username
    logout_user()
    flash(f'Vous êtes déconnecté, {username}. À bientôt !', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/api/v1/current-user')
@login_required
def current_user_api():
    """
    Obtenir les informations de l'utilisateur connecté
    ---
    tags:
      - Authentication
    responses:
      200:
        description: Informations utilisateur
        schema:
          type: object
          properties:
            id:
              type: string
              description: ID de l'utilisateur
            username:
              type: string
              description: Nom d'utilisateur
            email:
              type: string
              description: Email
            role:
              type: string
              description: Rôle (admin, user, viewer)
            active:
              type: boolean
              description: Compte actif
      401:
        description: Non authentifié
    """
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'role': current_user.role,
        'active': current_user.active
    })


@auth_bp.route('/profile')
@login_required
def profile():
    """
    Page de profil utilisateur
    ---
    tags:
      - Authentication
    responses:
      200:
        description: Page de profil de l'utilisateur connecté
    """
    from utils.permissions import get_user_permissions
    
    # Récupérer l'utilisateur complet depuis MongoDB
    user = user_manager.get_user_by_id(current_user.id)
    permissions = get_user_permissions(user)
    
    # Statistiques utilisateur
    stats = {}
    if user_manager.mongo_client.db is not None:
        # Fichiers uploadés par cet utilisateur (si on trackait l'uploader)
        files_collection = user_manager.mongo_client.db.uploaded_files
        stats['files_uploaded'] = files_collection.count_documents({})
        
        # Recherches effectuées
        search_collection = user_manager.mongo_client.db.search_history
        stats['searches_count'] = search_collection.count_documents({})
    
    return render_template('profile.html', 
                          page_title='Mon Profil',
                          user=user,
                          permissions=permissions,
                          stats=stats)


@auth_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """
    Mise à jour du profil utilisateur
    ---
    tags:
      - Authentication
    parameters:
      - name: email
        in: formData
        type: string
        description: Nouvel email
      - name: current_password
        in: formData
        type: string
        description: Mot de passe actuel (requis pour changement de password)
      - name: new_password
        in: formData
        type: string
        description: Nouveau mot de passe
      - name: confirm_password
        in: formData
        type: string
        description: Confirmation du nouveau mot de passe
    responses:
      302:
        description: Redirection vers profil après mise à jour
      400:
        description: Erreur de validation
    """
    email = request.form.get('email')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    user = user_manager.get_user_by_id(current_user.id)
    
    # Mise à jour de l'email
    if email and email != user.email:
        # Vérifier que l'email n'est pas déjà utilisé
        existing = user_manager.get_user_by_email(email)
        if existing and existing.id != user.id:
            flash('Cet email est déjà utilisé par un autre compte.', 'danger')
            return redirect(url_for('auth.profile'))
        
        user_manager.update_user_email(user.id, email)
        flash('Email mis à jour avec succès.', 'success')
    
    # Changement de mot de passe
    if new_password:
        if not current_password:
            flash('Veuillez entrer votre mot de passe actuel.', 'danger')
            return redirect(url_for('auth.profile'))
        
        if not user.check_password(current_password):
            flash('Mot de passe actuel incorrect.', 'danger')
            return redirect(url_for('auth.profile'))
        
        if new_password != confirm_password:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return redirect(url_for('auth.profile'))
        
        if len(new_password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères.', 'warning')
            return redirect(url_for('auth.profile'))
        
        user_manager.update_user_password(user.id, new_password)
        flash('Mot de passe mis à jour avec succès.', 'success')
    
    return redirect(url_for('auth.profile'))
