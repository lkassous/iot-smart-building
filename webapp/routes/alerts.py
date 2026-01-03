"""
Routes pour la gestion des règles d'alertes
Interface CRUD pour créer, modifier, supprimer et gérer les règles
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

alerts_bp = Blueprint('alerts', __name__, url_prefix='/alerts')


def get_rules_manager():
    """Récupère l'instance du gestionnaire de règles"""
    from utils import mongo_client
    from utils.alert_rules_manager import AlertRulesManager
    return AlertRulesManager(mongo_client.db)


@alerts_bp.route('/')
def index():
    """
    Page principale de gestion des alertes
    Affiche la liste des règles et leur statut
    """
    try:
        rules_manager = get_rules_manager()
        rules = rules_manager.get_all_rules()
        
        # Calculer les statistiques globales
        stats = {
            'total_rules': len(rules),
            'enabled_rules': sum(1 for r in rules if r.get('enabled', False)),
            'disabled_rules': sum(1 for r in rules if not r.get('enabled', False)),
            'critical_rules': sum(1 for r in rules if r.get('severity') == 'critical'),
            'total_triggers': sum(r.get('trigger_count', 0) for r in rules)
        }
        
        return render_template('alerts/index.html', rules=rules, stats=stats)
        
    except Exception as e:
        logger.error(f"❌ Erreur page alertes: {e}")
        flash(f"Erreur lors du chargement des règles: {str(e)}", 'error')
        return render_template('alerts/index.html', rules=[], stats={})


@alerts_bp.route('/create', methods=['GET', 'POST'])
def create():
    """
    Page de création d'une nouvelle règle
    GET: Affiche le formulaire
    POST: Crée la règle
    """
    if request.method == 'GET':
        return render_template('alerts/form.html', rule=None, mode='create')
    
    try:
        rules_manager = get_rules_manager()
        
        # Récupérer les données du formulaire
        rule_data = {
            'name': request.form.get('name', '').strip(),
            'description': request.form.get('description', '').strip(),
            'rule_type': request.form.get('rule_type', 'threshold'),
            'enabled': request.form.get('enabled') == 'on',
            'severity': request.form.get('severity', 'medium'),
            'conditions': {
                'field': request.form.get('condition_field', 'value'),
                'operator': request.form.get('condition_operator', '>'),
                'threshold': float(request.form.get('condition_threshold', 0))
            },
            'filters': {},
            'actions': [],
            'cooldown_seconds': int(request.form.get('cooldown', 300))
        }
        
        # Ajouter les filtres optionnels
        if request.form.get('filter_zone'):
            rule_data['filters']['zone'] = request.form.get('filter_zone')
        if request.form.get('filter_sensor_type'):
            rule_data['filters']['sensor_type'] = request.form.get('filter_sensor_type')
        if request.form.get('filter_building'):
            rule_data['filters']['building'] = request.form.get('filter_building')
        
        # Ajouter les actions
        if request.form.get('action_email'):
            recipients = request.form.get('email_recipients', '').split(',')
            recipients = [r.strip() for r in recipients if r.strip()]
            if recipients:
                rule_data['actions'].append({
                    'type': 'email',
                    'config': {'recipients': recipients}
                })
        
        if request.form.get('action_webhook'):
            webhook_url = request.form.get('webhook_url', '').strip()
            if webhook_url:
                rule_data['actions'].append({
                    'type': 'webhook',
                    'config': {'url': webhook_url}
                })
        
        if request.form.get('action_slack'):
            slack_url = request.form.get('slack_webhook_url', '').strip()
            if slack_url:
                rule_data['actions'].append({
                    'type': 'slack',
                    'config': {'webhook_url': slack_url}
                })
        
        # Pour les règles de type range
        if rule_data['rule_type'] == 'range':
            rule_data['conditions']['min_value'] = float(request.form.get('range_min', 0))
            rule_data['conditions']['max_value'] = float(request.form.get('range_max', 100))
            rule_data['conditions']['operator'] = 'out_of_range'
        
        # Pour les règles de type pattern
        if rule_data['rule_type'] == 'pattern':
            rule_data['conditions']['min_count'] = int(request.form.get('pattern_count', 3))
            rule_data['conditions']['time_window_seconds'] = int(request.form.get('pattern_window', 300))
        
        # Créer la règle
        success, message, rule_id = rules_manager.create_rule(rule_data)
        
        if success:
            flash(f"Règle '{rule_data['name']}' créée avec succès!", 'success')
            return redirect(url_for('alerts.index'))
        else:
            flash(f"Erreur: {message}", 'error')
            return render_template('alerts/form.html', rule=rule_data, mode='create')
            
    except Exception as e:
        logger.error(f"❌ Erreur création règle: {e}")
        flash(f"Erreur: {str(e)}", 'error')
        return render_template('alerts/form.html', rule=None, mode='create')


@alerts_bp.route('/<rule_id>/edit', methods=['GET', 'POST'])
def edit(rule_id):
    """
    Page d'édition d'une règle existante
    """
    rules_manager = get_rules_manager()
    
    if request.method == 'GET':
        rule = rules_manager.get_rule(rule_id)
        if not rule:
            flash("Règle non trouvée", 'error')
            return redirect(url_for('alerts.index'))
        return render_template('alerts/form.html', rule=rule, mode='edit')
    
    try:
        # Récupérer les données du formulaire (même logique que create)
        updates = {
            'name': request.form.get('name', '').strip(),
            'description': request.form.get('description', '').strip(),
            'rule_type': request.form.get('rule_type', 'threshold'),
            'enabled': request.form.get('enabled') == 'on',
            'severity': request.form.get('severity', 'medium'),
            'conditions': {
                'field': request.form.get('condition_field', 'value'),
                'operator': request.form.get('condition_operator', '>'),
                'threshold': float(request.form.get('condition_threshold', 0))
            },
            'filters': {},
            'actions': [],
            'cooldown_seconds': int(request.form.get('cooldown', 300))
        }
        
        # Ajouter les filtres optionnels
        if request.form.get('filter_zone'):
            updates['filters']['zone'] = request.form.get('filter_zone')
        if request.form.get('filter_sensor_type'):
            updates['filters']['sensor_type'] = request.form.get('filter_sensor_type')
        if request.form.get('filter_building'):
            updates['filters']['building'] = request.form.get('filter_building')
        
        # Ajouter les actions
        if request.form.get('action_email'):
            recipients = request.form.get('email_recipients', '').split(',')
            recipients = [r.strip() for r in recipients if r.strip()]
            if recipients:
                updates['actions'].append({
                    'type': 'email',
                    'config': {'recipients': recipients}
                })
        
        if request.form.get('action_webhook'):
            webhook_url = request.form.get('webhook_url', '').strip()
            if webhook_url:
                updates['actions'].append({
                    'type': 'webhook',
                    'config': {'url': webhook_url}
                })
        
        # Pour les règles de type range
        if updates['rule_type'] == 'range':
            updates['conditions']['min_value'] = float(request.form.get('range_min', 0))
            updates['conditions']['max_value'] = float(request.form.get('range_max', 100))
            updates['conditions']['operator'] = 'out_of_range'
        
        # Pour les règles de type pattern
        if updates['rule_type'] == 'pattern':
            updates['conditions']['min_count'] = int(request.form.get('pattern_count', 3))
            updates['conditions']['time_window_seconds'] = int(request.form.get('pattern_window', 300))
        
        success, message = rules_manager.update_rule(rule_id, updates)
        
        if success:
            flash(f"Règle mise à jour avec succès!", 'success')
            return redirect(url_for('alerts.index'))
        else:
            flash(f"Erreur: {message}", 'error')
            
    except Exception as e:
        logger.error(f"❌ Erreur modification règle: {e}")
        flash(f"Erreur: {str(e)}", 'error')
    
    rule = rules_manager.get_rule(rule_id)
    return render_template('alerts/form.html', rule=rule, mode='edit')


@alerts_bp.route('/<rule_id>/delete', methods=['POST'])
def delete(rule_id):
    """Supprime une règle"""
    try:
        rules_manager = get_rules_manager()
        success, message = rules_manager.delete_rule(rule_id)
        
        if success:
            flash("Règle supprimée avec succès", 'success')
        else:
            flash(f"Erreur: {message}", 'error')
            
    except Exception as e:
        logger.error(f"❌ Erreur suppression règle: {e}")
        flash(f"Erreur: {str(e)}", 'error')
    
    return redirect(url_for('alerts.index'))


@alerts_bp.route('/<rule_id>/toggle', methods=['POST'])
def toggle(rule_id):
    """Active/désactive une règle"""
    try:
        rules_manager = get_rules_manager()
        
        success, message, new_state = rules_manager.toggle_rule(rule_id)
        
        if success:
            return jsonify({
                'success': True,
                'enabled': new_state,
                'message': message
            })
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f"❌ Erreur toggle règle: {e}")
        return jsonify({'error': str(e)}), 500


@alerts_bp.route('/<rule_id>/history')
def history(rule_id):
    """Affiche l'historique des déclenchements d'une règle"""
    try:
        rules_manager = get_rules_manager()
        rule = rules_manager.get_rule(rule_id)
        
        if not rule:
            flash("Règle non trouvée", 'error')
            return redirect(url_for('alerts.index'))
        
        # TODO: Récupérer l'historique des déclenchements depuis MongoDB
        # Pour l'instant, on affiche les stats de la règle
        
        return render_template('alerts/history.html', rule=rule)
        
    except Exception as e:
        logger.error(f"❌ Erreur historique règle: {e}")
        flash(f"Erreur: {str(e)}", 'error')
        return redirect(url_for('alerts.index'))


# =====================================================
# API JSON pour les opérations AJAX
# =====================================================

@alerts_bp.route('/api/rules')
def api_list_rules():
    """API: Liste toutes les règles"""
    try:
        rules_manager = get_rules_manager()
        rules = rules_manager.get_all_rules()
        
        # Convertir ObjectId en string pour JSON
        for rule in rules:
            rule['_id'] = str(rule['_id'])
            if rule.get('last_triggered'):
                rule['last_triggered'] = rule['last_triggered'].isoformat()
            if rule.get('created_at'):
                rule['created_at'] = rule['created_at'].isoformat()
        
        return jsonify({'rules': rules, 'total': len(rules)})
        
    except Exception as e:
        logger.error(f"❌ Erreur API rules: {e}")
        return jsonify({'error': str(e)}), 500


@alerts_bp.route('/api/rules/<rule_id>')
def api_get_rule(rule_id):
    """API: Récupère une règle spécifique"""
    try:
        rules_manager = get_rules_manager()
        rule = rules_manager.get_rule(rule_id)
        
        if not rule:
            return jsonify({'error': 'Règle non trouvée'}), 404
        
        rule['_id'] = str(rule['_id'])
        if rule.get('last_triggered'):
            rule['last_triggered'] = rule['last_triggered'].isoformat()
        
        return jsonify(rule)
        
    except Exception as e:
        logger.error(f"❌ Erreur API get rule: {e}")
        return jsonify({'error': str(e)}), 500


@alerts_bp.route('/api/rules/<rule_id>/test', methods=['POST'])
def api_test_rule(rule_id):
    """API: Teste une règle sur les données récentes"""
    try:
        rules_manager = get_rules_manager()
        rule = rules_manager.get_rule(rule_id)
        
        if not rule:
            return jsonify({'error': 'Règle non trouvée'}), 404
        
        # Récupérer les logs récents
        from utils.elasticsearch import ElasticsearchClient
        es_client = ElasticsearchClient()
        
        recent_logs = es_client.search(
            index='logs-iot-*',
            body={
                'query': {'range': {'@timestamp': {'gte': 'now-1h'}}},
                'size': 1000
            }
        )
        
        logs = [hit['_source'] for hit in recent_logs.get('hits', {}).get('hits', [])]
        
        # Évaluer la règle
        is_triggered, matching_logs = rules_manager.evaluate_rule(rule, logs)
        
        return jsonify({
            'rule_name': rule['name'],
            'is_triggered': is_triggered,
            'matching_count': len(matching_logs),
            'total_logs_checked': len(logs),
            'sample_matches': matching_logs[:5]
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur test règle: {e}")
        return jsonify({'error': str(e)}), 500
