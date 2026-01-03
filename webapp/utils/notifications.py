"""
Configuration et utilitaires pour les notifications email
Utilise Flask-Mail pour l'envoi d'emails
"""

from flask_mail import Mail, Message
from flask import current_app, render_template_string
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Instance Mail globale
mail = Mail()


def init_mail(app):
    """
    Initialise Flask-Mail avec l'application Flask
    
    Configuration attendue dans app.config:
    - MAIL_SERVER: Serveur SMTP (default: localhost)
    - MAIL_PORT: Port SMTP (default: 587)
    - MAIL_USE_TLS: Utiliser TLS (default: True)
    - MAIL_USE_SSL: Utiliser SSL (default: False)
    - MAIL_USERNAME: Nom d'utilisateur SMTP
    - MAIL_PASSWORD: Mot de passe SMTP
    - MAIL_DEFAULT_SENDER: Expéditeur par défaut
    """
    mail.init_app(app)
    logger.info("✅ Flask-Mail initialisé")


def send_alert_email(
    rule: Dict,
    matching_logs: List[Dict],
    recipients: List[str],
    avg_value: float = None,
    zones_affected: List[str] = None
) -> bool:
    """
    Envoie une notification email pour une alerte déclenchée
    
    Args:
        rule: Règle d'alerte déclenchée
        matching_logs: Logs ayant déclenché l'alerte
        recipients: Liste des destinataires
        avg_value: Valeur moyenne (optionnel)
        zones_affected: Zones concernées (optionnel)
    
    Returns:
        True si l'email a été envoyé, False sinon
    """
    try:
        # Construire le sujet
        severity = rule.get('severity', 'medium').upper()
        rule_name = rule.get('name', 'Alerte')
        subject = f"🚨 [{severity}] {rule_name} - IoT Smart Building"
        
        # Construire le corps de l'email
        html_body = render_alert_email_html(
            rule=rule,
            matching_logs=matching_logs,
            avg_value=avg_value,
            zones_affected=zones_affected
        )
        
        text_body = render_alert_email_text(
            rule=rule,
            matching_logs=matching_logs,
            avg_value=avg_value,
            zones_affected=zones_affected
        )
        
        # Créer le message
        msg = Message(
            subject=subject,
            recipients=recipients,
            body=text_body,
            html=html_body
        )
        
        # Envoyer l'email
        mail.send(msg)
        
        logger.info(f"✅ Email envoyé à {recipients} pour règle '{rule_name}'")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur envoi email: {e}")
        return False


def render_alert_email_html(
    rule: Dict,
    matching_logs: List[Dict],
    avg_value: float = None,
    zones_affected: List[str] = None
) -> str:
    """
    Génère le corps HTML de l'email d'alerte
    """
    severity_colors = {
        'low': '#17a2b8',
        'medium': '#ffc107', 
        'high': '#fd7e14',
        'critical': '#dc3545'
    }
    
    severity = rule.get('severity', 'medium')
    color = severity_colors.get(severity, '#6c757d')
    
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: {{ color }}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }
            .content { background: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; }
            .alert-badge { display: inline-block; padding: 5px 15px; border-radius: 4px; 
                          background: white; color: {{ color }}; font-weight: bold; }
            .stats { background: white; padding: 15px; border-radius: 4px; margin: 15px 0; }
            .stat-item { display: inline-block; margin-right: 30px; }
            .stat-value { font-size: 24px; font-weight: bold; color: {{ color }}; }
            .stat-label { font-size: 12px; color: #666; }
            .logs-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
            .logs-table th, .logs-table td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
            .logs-table th { background: #e9ecef; }
            .footer { margin-top: 20px; font-size: 12px; color: #666; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0;">🚨 Alerte IoT Smart Building</h1>
                <div class="alert-badge">{{ severity | upper }}</div>
            </div>
            
            <div class="content">
                <h2>{{ rule_name }}</h2>
                <p>{{ rule_description }}</p>
                
                <div class="stats">
                    <div class="stat-item">
                        <div class="stat-value">{{ matching_count }}</div>
                        <div class="stat-label">Événements détectés</div>
                    </div>
                    {% if avg_value is not none %}
                    <div class="stat-item">
                        <div class="stat-value">{{ avg_value | round(2) }}</div>
                        <div class="stat-label">Valeur moyenne</div>
                    </div>
                    {% endif %}
                    {% if zones_affected %}
                    <div class="stat-item">
                        <div class="stat-value">{{ zones_affected | length }}</div>
                        <div class="stat-label">Zones affectées</div>
                    </div>
                    {% endif %}
                </div>
                
                {% if zones_affected %}
                <p><strong>Zones concernées:</strong> {{ zones_affected | join(', ') }}</p>
                {% endif %}
                
                <h3>Détails des événements</h3>
                <table class="logs-table">
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Zone</th>
                            <th>Type</th>
                            <th>Valeur</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for log in logs[:5] %}
                        <tr>
                            <td>{{ log.get('@timestamp', log.get('timestamp', 'N/A')) }}</td>
                            <td>{{ log.get('zone', 'N/A') }}</td>
                            <td>{{ log.get('sensor_type', log.get('event_type', 'N/A')) }}</td>
                            <td>{{ log.get('value', 'N/A') }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% if matching_count > 5 %}
                <p style="font-style: italic; color: #666;">
                    ... et {{ matching_count - 5 }} autres événements
                </p>
                {% endif %}
                
                <div class="footer">
                    <p>
                        Cet email a été généré automatiquement par le système d'alerting IoT Smart Building.<br>
                        <a href="{{ dashboard_url }}">Accéder au Dashboard</a>
                    </p>
                    <p>
                        Déclenchement: {{ timestamp }}
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(
        template,
        color=color,
        severity=severity,
        rule_name=rule.get('name', 'Règle'),
        rule_description=rule.get('description', ''),
        matching_count=len(matching_logs),
        avg_value=avg_value,
        zones_affected=zones_affected,
        logs=matching_logs,
        dashboard_url='http://localhost:8000/',
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )


def render_alert_email_text(
    rule: Dict,
    matching_logs: List[Dict],
    avg_value: float = None,
    zones_affected: List[str] = None
) -> str:
    """
    Génère le corps texte de l'email d'alerte
    """
    severity = rule.get('severity', 'medium').upper()
    rule_name = rule.get('name', 'Règle')
    
    lines = [
        f"🚨 ALERTE IOT SMART BUILDING [{severity}]",
        "=" * 50,
        "",
        f"Règle: {rule_name}",
        f"Description: {rule.get('description', 'N/A')}",
        "",
        f"Événements détectés: {len(matching_logs)}",
    ]
    
    if avg_value is not None:
        lines.append(f"Valeur moyenne: {avg_value:.2f}")
    
    if zones_affected:
        lines.append(f"Zones affectées: {', '.join(zones_affected)}")
    
    lines.extend([
        "",
        "Détails des 5 premiers événements:",
        "-" * 40
    ])
    
    for log in matching_logs[:5]:
        timestamp = log.get('@timestamp', log.get('timestamp', 'N/A'))
        zone = log.get('zone', 'N/A')
        sensor_type = log.get('sensor_type', log.get('event_type', 'N/A'))
        value = log.get('value', 'N/A')
        lines.append(f"  [{timestamp}] Zone {zone} | {sensor_type}: {value}")
    
    if len(matching_logs) > 5:
        lines.append(f"  ... et {len(matching_logs) - 5} autres événements")
    
    lines.extend([
        "",
        "-" * 40,
        f"Déclenché le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "Ce message a été généré automatiquement par le système d'alerting IoT Smart Building."
    ])
    
    return "\n".join(lines)


class NotificationManager:
    """
    Gestionnaire de notifications multi-canal
    Supporte email, webhook, Slack, Discord
    """
    
    def __init__(self, app=None):
        self.app = app
        self.handlers = {
            'email': self._send_email,
            'webhook': self._send_webhook,
            'slack': self._send_slack,
            'discord': self._send_discord
        }
    
    def send_notification(
        self,
        action: Dict,
        rule: Dict,
        matching_logs: List[Dict],
        **kwargs
    ) -> bool:
        """
        Envoie une notification selon le type d'action configuré
        
        Args:
            action: Configuration de l'action (type, config)
            rule: Règle déclenchée
            matching_logs: Logs ayant déclenché l'alerte
            **kwargs: Arguments supplémentaires (avg_value, zones_affected)
        
        Returns:
            True si la notification a été envoyée, False sinon
        """
        action_type = action.get('type', 'email')
        handler = self.handlers.get(action_type)
        
        if not handler:
            logger.warning(f"⚠️ Type de notification non supporté: {action_type}")
            return False
        
        return handler(action.get('config', {}), rule, matching_logs, **kwargs)
    
    def _send_email(
        self,
        config: Dict,
        rule: Dict,
        matching_logs: List[Dict],
        **kwargs
    ) -> bool:
        """Envoie une notification par email"""
        recipients = config.get('recipients', [])
        
        if not recipients:
            logger.warning("⚠️ Aucun destinataire email configuré")
            return False
        
        return send_alert_email(
            rule=rule,
            matching_logs=matching_logs,
            recipients=recipients,
            avg_value=kwargs.get('avg_value'),
            zones_affected=kwargs.get('zones_affected')
        )
    
    def _send_webhook(
        self,
        config: Dict,
        rule: Dict,
        matching_logs: List[Dict],
        **kwargs
    ) -> bool:
        """Envoie une notification par webhook"""
        import requests
        
        url = config.get('url')
        if not url:
            logger.warning("⚠️ URL webhook non configurée")
            return False
        
        payload = {
            'rule_name': rule.get('name'),
            'severity': rule.get('severity'),
            'matching_count': len(matching_logs),
            'avg_value': kwargs.get('avg_value'),
            'zones_affected': kwargs.get('zones_affected'),
            'timestamp': datetime.now().isoformat(),
            'logs_sample': matching_logs[:5]
        }
        
        try:
            headers = config.get('headers', {'Content-Type': 'application/json'})
            method = config.get('method', 'POST').upper()
            timeout = config.get('timeout', 10)
            
            if method == 'POST':
                response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            else:
                response = requests.get(url, params=payload, headers=headers, timeout=timeout)
            
            if response.status_code < 400:
                logger.info(f"✅ Webhook envoyé à {url}")
                return True
            else:
                logger.warning(f"⚠️ Webhook failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur webhook: {e}")
            return False
    
    def _send_slack(
        self,
        config: Dict,
        rule: Dict,
        matching_logs: List[Dict],
        **kwargs
    ) -> bool:
        """Envoie une notification Slack"""
        import requests
        
        webhook_url = config.get('webhook_url')
        if not webhook_url:
            logger.warning("⚠️ Webhook Slack non configuré")
            return False
        
        severity_emoji = {
            'low': '📘',
            'medium': '⚠️',
            'high': '🔶',
            'critical': '🚨'
        }
        
        severity = rule.get('severity', 'medium')
        emoji = severity_emoji.get(severity, '📢')
        
        # Construire le message Slack
        payload = {
            'attachments': [{
                'color': {'low': '#17a2b8', 'medium': '#ffc107', 'high': '#fd7e14', 'critical': '#dc3545'}.get(severity, '#6c757d'),
                'title': f"{emoji} {rule.get('name', 'Alerte')}",
                'text': rule.get('description', ''),
                'fields': [
                    {
                        'title': 'Sévérité',
                        'value': severity.upper(),
                        'short': True
                    },
                    {
                        'title': 'Événements',
                        'value': str(len(matching_logs)),
                        'short': True
                    }
                ],
                'footer': 'IoT Smart Building Alerting',
                'ts': int(datetime.now().timestamp())
            }]
        }
        
        if kwargs.get('zones_affected'):
            payload['attachments'][0]['fields'].append({
                'title': 'Zones',
                'value': ', '.join(kwargs['zones_affected']),
                'short': False
            })
        
        if kwargs.get('avg_value') is not None:
            payload['attachments'][0]['fields'].append({
                'title': 'Valeur moyenne',
                'value': f"{kwargs['avg_value']:.2f}",
                'short': True
            })
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Notification Slack envoyée")
                return True
            else:
                logger.warning(f"⚠️ Slack webhook failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur Slack: {e}")
            return False
    
    def _send_discord(
        self,
        config: Dict,
        rule: Dict,
        matching_logs: List[Dict],
        **kwargs
    ) -> bool:
        """Envoie une notification Discord"""
        import requests
        
        webhook_url = config.get('webhook_url')
        if not webhook_url:
            logger.warning("⚠️ Webhook Discord non configuré")
            return False
        
        severity_colors = {
            'low': 0x17a2b8,
            'medium': 0xffc107,
            'high': 0xfd7e14,
            'critical': 0xdc3545
        }
        
        severity = rule.get('severity', 'medium')
        
        # Construire l'embed Discord
        embed = {
            'title': f"🚨 {rule.get('name', 'Alerte')}",
            'description': rule.get('description', ''),
            'color': severity_colors.get(severity, 0x6c757d),
            'fields': [
                {
                    'name': 'Sévérité',
                    'value': severity.upper(),
                    'inline': True
                },
                {
                    'name': 'Événements',
                    'value': str(len(matching_logs)),
                    'inline': True
                }
            ],
            'footer': {
                'text': 'IoT Smart Building Alerting'
            },
            'timestamp': datetime.now().isoformat()
        }
        
        if kwargs.get('zones_affected'):
            embed['fields'].append({
                'name': 'Zones affectées',
                'value': ', '.join(kwargs['zones_affected']),
                'inline': False
            })
        
        payload = {
            'embeds': [embed]
        }
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            
            if response.status_code in [200, 204]:
                logger.info("✅ Notification Discord envoyée")
                return True
            else:
                logger.warning(f"⚠️ Discord webhook failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur Discord: {e}")
            return False


# Instance globale du gestionnaire de notifications
notification_manager = NotificationManager()
