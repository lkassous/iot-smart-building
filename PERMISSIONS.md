# 🔐 Système de Permissions et Rôles - IoT Smart Building

## Vue d'Ensemble

Le système d'authentification implémente un **contrôle d'accès basé sur les rôles (RBAC)** avec 3 niveaux de permissions :

### Rôles Disponibles

| Rôle | Permissions | Description |
|------|-------------|-------------|
| **Viewer** | `read` | Accès en lecture seule (dashboard, recherche, visualisations) |
| **User** | `read`, `write` | Lecture + écriture (upload de fichiers, modification de données) |
| **Admin** | `read`, `write`, `delete`, `admin`, `manage_users` | Accès complet à toutes les fonctionnalités |

## Matrice de Permissions

| Fonctionnalité | Viewer | User | Admin |
|----------------|:------:|:----:|:-----:|
| 📊 Dashboard (/) | ✅ | ✅ | ✅ |
| 🔍 Recherche de logs (/search) | ✅ | ✅ | ✅ |
| 📄 Consultation résultats (/results) | ✅ | ✅ | ✅ |
| 📊 Kibana visualisations | ✅ | ✅ | ✅ |
| 👤 Profil utilisateur (/profile) | ✅ | ✅ | ✅ |
| 📤 Upload de fichiers (/upload) | ❌ | ✅ | ✅ |
| ✏️ Modification de données | ❌ | ✅ | ✅ |
| 🗑️ Suppression de fichiers | ❌ | ❌ | ✅ |
| 👥 Gestion utilisateurs | ❌ | ❌ | ✅ |
| ⚙️ Administration système | ❌ | ❌ | ✅ |

## Implémentation Technique

### 1. Décorateurs de Permissions

#### `@permission_required(permission)`
Vérifie qu'un utilisateur possède une permission spécifique.

```python
from utils.permissions import permission_required

@app.route('/upload')
@login_required
@permission_required('write')
def upload_page():
    # Seuls les users et admins peuvent accéder
    return render_template('upload.html')
```

**Permissions disponibles:**
- `'read'` - Lecture (viewer, user, admin)
- `'write'` - Écriture (user, admin)
- `'delete'` - Suppression (admin uniquement)
- `'admin'` - Administration (admin uniquement)
- `'manage_users'` - Gestion des utilisateurs (admin uniquement)

#### `@role_required(*roles)`
Vérifie qu'un utilisateur a un rôle spécifique.

```python
from utils.permissions import role_required

@app.route('/admin/users')
@login_required
@role_required('admin')
def manage_users():
    # Seuls les admins peuvent accéder
    return render_template('admin/users.html')
```

#### `@admin_required`
Raccourci pour vérifier que l'utilisateur est admin.

```python
from utils.permissions import admin_required

@app.route('/admin/settings')
@login_required
@admin_required
def admin_settings():
    # Seuls les admins
    return render_template('admin/settings.html')
```

### 2. Vérification dans les Modèles

La classe `User` implémente la méthode `has_permission(permission)`:

```python
user = current_user

if user.has_permission('write'):
    # Autoriser l'upload
    pass

if user.has_permission('admin'):
    # Afficher le panneau admin
    pass
```

### 3. Gestion des Erreurs

#### Page 403 - Accès Refusé
Affichée automatiquement quand un utilisateur n'a pas les permissions requises.

**Template:** `templates/403.html`
- Affiche le rôle actuel de l'utilisateur
- Message personnalisé selon la permission manquante
- Liens vers dashboard et profil

**Exemple de déclenchement:**
```python
from flask import abort

if not current_user.has_permission('delete'):
    flash('Permission refusée: suppression requise', 'danger')
    abort(403)  # → Affiche templates/403.html
```

## Page de Profil Utilisateur

### Route: `/profile`

**Fonctionnalités:**

1. **Informations du compte**
   - Nom d'utilisateur (non modifiable)
   - Email (modifiable)
   - Rôle avec badge coloré
   - Date de création du compte
   - Dernière connexion
   - Statut actif/inactif

2. **Permissions & Droits**
   - Liste des permissions par rôle
   - Description détaillée de chaque permission
   - Badge de rôle avec alerte contextuelle

3. **Statistiques d'utilisation**
   - Nombre de fichiers uploadés (total système)
   - Nombre de recherches effectuées (total système)
   - Jours depuis dernière connexion

4. **Modification du profil (Modal)**
   - Mise à jour de l'email
   - Changement de mot de passe (avec confirmation)
   - Validation sécurisée

### Route: `/profile/update` (POST)

**Paramètres:**
- `email` - Nouvel email
- `current_password` - Mot de passe actuel (requis pour changement)
- `new_password` - Nouveau mot de passe (min 6 caractères)
- `confirm_password` - Confirmation

**Validations:**
- Email unique (vérification dans MongoDB)
- Mot de passe actuel correct
- Nouveau mot de passe >= 6 caractères
- Confirmation identique

**Exemple de requête:**
```bash
curl -X POST http://localhost:8000/profile/update \
  -b cookies.txt \
  -d "email=newemail@example.com" \
  -d "current_password=admin123" \
  -d "new_password=newpass456" \
  -d "confirm_password=newpass456"
```

## Tests de Permissions

### Script de Test Automatisé

```bash
#!/bin/bash
# Test des 3 rôles sur tous les endpoints

# VIEWER - Read only
curl -c viewer_cookies.txt -X POST http://localhost:8000/login \
  -d "username=viewer&password=viewer123"

curl -b viewer_cookies.txt http://localhost:8000/         # 200 OK
curl -b viewer_cookies.txt http://localhost:8000/search   # 200 OK
curl -b viewer_cookies.txt http://localhost:8000/upload   # 403 Forbidden ✅

# USER - Read + Write
curl -c user_cookies.txt -X POST http://localhost:8000/login \
  -d "username=user&password=user123"

curl -b user_cookies.txt http://localhost:8000/         # 200 OK
curl -b user_cookies.txt http://localhost:8000/upload   # 200 OK ✅

# ADMIN - All permissions
curl -c admin_cookies.txt -X POST http://localhost:8000/login \
  -d "username=admin&password=admin123"

curl -b admin_cookies.txt http://localhost:8000/        # 200 OK
curl -b admin_cookies.txt http://localhost:8000/upload  # 200 OK ✅
```

### Résultats Attendus

| Endpoint | Viewer | User | Admin |
|----------|--------|------|-------|
| GET / | 200 ✅ | 200 ✅ | 200 ✅ |
| GET /search | 200 ✅ | 200 ✅ | 200 ✅ |
| GET /upload | 403 ❌ | 200 ✅ | 200 ✅ |
| GET /profile | 200 ✅ | 200 ✅ | 200 ✅ |
| POST /upload | 403 ❌ | 200 ✅ | 200 ✅ |

## Utilisation dans les Templates Jinja2

### Vérifier les Permissions

```jinja2
{% if current_user.has_permission('write') %}
  <a href="{{ url_for('upload_page') }}" class="btn btn-primary">
    <i class="bi bi-cloud-upload"></i> Upload
  </a>
{% endif %}

{% if current_user.has_permission('admin') %}
  <a href="{{ url_for('admin_panel') }}" class="btn btn-danger">
    <i class="bi bi-gear"></i> Administration
  </a>
{% endif %}
```

### Afficher le Rôle

```jinja2
<span class="badge 
  {% if current_user.role == 'admin' %}bg-danger
  {% elif current_user.role == 'user' %}bg-info
  {% else %}bg-secondary{% endif %}">
  {{ current_user.role|upper }}
</span>
```

## Sécurité et Bonnes Pratiques

### ✅ Implémenté

1. **Authentification requise** - Toutes les routes protégées avec `@login_required`
2. **Contrôle d'accès granulaire** - Permissions vérifiées à chaque requête
3. **Messages flash** - Feedback utilisateur sur les erreurs de permissions
4. **Page 403 personnalisée** - Informative au lieu d'une erreur brute
5. **Validation des mots de passe** - Minimum 6 caractères, confirmation requise
6. **Hachage sécurisé** - Werkzeug scrypt pour les passwords
7. **Vérification email unique** - Empêche les doublons

### 🔒 Recommandations Production

1. **HTTPS obligatoire** - Chiffrer toutes les communications
2. **Rate limiting** - Limiter les tentatives de login (ex: Flask-Limiter)
3. **2FA (Two-Factor Auth)** - Ajouter une couche de sécurité supplémentaire
4. **Audit logs** - Logger toutes les actions admin dans MongoDB
5. **Session timeout** - Déconnexion auto après inactivité
6. **CSRF protection** - Activer Flask-WTF CSRF tokens
7. **Content Security Policy** - Headers de sécurité

## Exemples d'Utilisation Avancée

### Fonction Utilitaire: `get_user_permissions(user)`

```python
from utils.permissions import get_user_permissions

user = current_user
permissions = get_user_permissions(user)
# ['read', 'write', 'admin', 'delete', 'manage_users'] pour admin
# ['read', 'write'] pour user
# ['read'] pour viewer
```

### Fonction Utilitaire: `can_edit_user(current_user, target_user)`

```python
from utils.permissions import can_edit_user

# Un admin peut modifier tout le monde
# Un user peut modifier son propre profil (sauf son rôle)
# Un viewer ne peut modifier personne

if can_edit_user(current_user, other_user):
    # Autoriser la modification
    pass
```

## Structure des Fichiers

```
webapp/
├── utils/
│   └── permissions.py          # Décorateurs et fonctions de permissions
├── routes/
│   └── auth.py                 # Routes /profile, /profile/update
├── models/
│   └── user.py                 # Méthode has_permission(perm)
├── templates/
│   ├── profile.html            # Page de profil complète
│   ├── 403.html                # Page d'erreur permissions
│   └── base.html               # Dropdown avec lien profil
└── app.py                      # Gestionnaires d'erreurs, routes protégées
```

## Support et Documentation

- **Identifiants de test:** Voir `CREDENTIALS.md`
- **Tests automatisés:** `/tmp/test_permissions.sh`
- **Code source permissions:** `webapp/utils/permissions.py`
- **Modèle utilisateur:** `webapp/models/user.py`
