/**
 * WebSocket Temps Réel - IoT Smart Building
 * Gère la connexion Socket.IO et les mises à jour en temps réel
 */

class RealtimeMonitoring {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        this.stats = {};
        
        this.init();
    }
    
    init() {
        // Connexion au serveur Socket.IO avec URL relative
        const protocol = window.location.protocol;
        const host = window.location.host;
        
        this.socket = io(`${protocol}//${host}/monitoring`, {
            reconnection: true,
            reconnectionDelay: this.reconnectDelay,
            reconnectionAttempts: this.maxReconnectAttempts,
            transports: ['polling', 'websocket'], // Préférer polling en premier pour éviter les erreurs
            timeout: 10000
        });
        
        this.setupEventListeners();
        this.updateConnectionStatus('Connexion en cours...', 'warning');
    }
    
    setupEventListeners() {
        // Connexion établie
        this.socket.on('connect', () => {
            console.log('✅ Connecté au serveur WebSocket');
            this.connected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus('Connecté - Temps réel actif', 'success');
            
            // S'abonner au monitoring
            this.socket.emit('subscribe_monitoring');
            
            // Demander immédiatement les logs récents
            setTimeout(() => {
                this.requestRecentLogs(10);
            }, 500);
        });
        
        // Déconnexion
        this.socket.on('disconnect', (reason) => {
            console.warn('🔌 Déconnecté:', reason);
            this.connected = false;
            this.updateConnectionStatus('Déconnecté - Reconnexion...', 'danger');
        });
        
        // Réponse de connexion
        this.socket.on('connection_response', (data) => {
            console.log('📡 Serveur:', data.message);
            this.showNotification(data.message, 'info');
        });
        
        // Mise à jour des statistiques
        this.socket.on('stats_update', (data) => {
            console.log('📊 Stats mises à jour:', data);
            this.updateStats(data);
        });
        
        // Nouveaux logs
        this.socket.on('new_logs', (data) => {
            console.log(`📝 ${data.count} nouveaux logs reçus`);
            this.handleNewLogs(data);
        });
        
        // Logs récents
        this.socket.on('recent_logs', (data) => {
            console.log(`📋 ${data.count} logs récents reçus`);
            this.displayRecentLogs(data.logs);
        });
        
        // Alertes critiques
        this.socket.on('critical_alert', (data) => {
            console.warn(`🚨 ${data.count} alertes critiques!`);
            this.handleCriticalAlert(data);
        });
        
        // Erreurs
        this.socket.on('error', (data) => {
            console.error('❌ Erreur WebSocket:', data.message);
            this.showNotification(data.message, 'danger');
        });
    }
    
    updateConnectionStatus(message, type) {
        const statusEl = document.getElementById('realtime-status');
        if (statusEl) {
            statusEl.className = `badge bg-${type} ms-2`;
            statusEl.innerHTML = `<i class="bi bi-broadcast"></i> ${message}`;
        }
    }
    
    updateStats(data) {
        // Mettre à jour les KPI cards
        this.animateNumberChange('total-logs', data.total_logs);
        this.animateNumberChange('logs-today', data.logs_today);
        this.animateNumberChange('errors-count', data.errors_count);
        this.animateNumberChange('sensors-active', data.sensors_active);
        
        // Mettre à jour le timestamp
        const timestampEl = document.getElementById('last-update');
        if (timestampEl) {
            const time = new Date(data.timestamp).toLocaleTimeString('fr-FR');
            timestampEl.textContent = `Dernière mise à jour: ${time}`;
        }
        
        // Mettre à jour l'activité des zones
        if (data.zones_activity && Object.keys(data.zones_activity).length > 0) {
            this.updateZonesActivity(data.zones_activity);
        } else {
            // Afficher un message si pas d'activité
            const container = document.getElementById('zones-activity');
            if (container) {
                container.innerHTML = `
                    <p class="text-muted text-center">
                        <i class="bi bi-info-circle"></i> Aucune activité détectée dans les 24 dernières heures
                    </p>
                `;
            }
        }
        
        this.stats = data;
    }
    
    animateNumberChange(elementId, newValue) {
        const el = document.getElementById(elementId);
        if (!el) return;
        
        const oldValue = parseInt(el.textContent.replace(/[^\d]/g, '')) || 0;
        
        if (oldValue !== newValue) {
            // Animation de changement
            el.classList.add('number-change');
            
            // Compteur animé
            this.animateCounter(el, oldValue, newValue, 500);
            
            setTimeout(() => {
                el.classList.remove('number-change');
            }, 500);
        }
    }
    
    animateCounter(element, start, end, duration) {
        const range = end - start;
        const increment = range / (duration / 16); // 60 FPS
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                current = end;
                clearInterval(timer);
            }
            element.textContent = Math.round(current).toLocaleString('fr-FR');
        }, 16);
    }
    
    handleNewLogs(data) {
        // Ajouter une badge de notification
        const notifCount = document.getElementById('new-logs-count');
        if (notifCount) {
            notifCount.textContent = `+${data.count}`;
            notifCount.classList.remove('d-none');
            
            // Cacher après 5 secondes
            setTimeout(() => {
                notifCount.classList.add('d-none');
            }, 5000);
        }
        
        // Afficher les logs dans le tableau temps réel
        this.displayRecentLogs(data.logs);
        
        // Animation de pulse sur la carte
        const logsCard = document.querySelector('.card.border-success');
        if (logsCard) {
            logsCard.classList.add('pulse-animation');
            setTimeout(() => {
                logsCard.classList.remove('pulse-animation');
            }, 1000);
        }
    }
    
    displayRecentLogs(logs) {
        const tableBody = document.getElementById('realtime-logs-tbody');
        if (!tableBody) return;
        
        // Limiter à 10 logs
        const recentLogs = logs.slice(0, 10);
        
        tableBody.innerHTML = recentLogs.map(log => {
            const statusBadge = this.getStatusBadge(log.status);
            const time = new Date(log.timestamp).toLocaleTimeString('fr-FR');
            
            return `
                <tr class="fade-in">
                    <td><small>${time}</small></td>
                    <td><span class="badge bg-secondary">${log.zone}</span></td>
                    <td>${log.sensor_type || log.message.substring(0, 30)}</td>
                    <td>${log.value} ${log.unit || ''}</td>
                    <td>${statusBadge}</td>
                </tr>
            `;
        }).join('');
    }
    
    getStatusBadge(status) {
        const badges = {
            'ok': '<span class="badge bg-success">OK</span>',
            'warning': '<span class="badge bg-warning">Warning</span>',
            'error': '<span class="badge bg-danger">Error</span>',
            'critical': '<span class="badge bg-danger"><i class="bi bi-exclamation-triangle-fill"></i> Critical</span>',
            'high': '<span class="badge bg-warning">High</span>',
            'info': '<span class="badge bg-info">Info</span>'
        };
        return badges[status] || `<span class="badge bg-secondary">${status}</span>`;
    }
    
    handleCriticalAlert(data) {
        // Son de notification (optionnel)
        this.playNotificationSound();
        
        // Notification visuelle
        this.showNotification(
            `🚨 ${data.count} alerte(s) critique(s) détectée(s) !`,
            'danger',
            true
        );
        
        // Afficher les alertes dans une modal ou toast
        data.alerts.forEach(alert => {
            this.showAlert(alert);
        });
    }
    
    showAlert(alert) {
        const alertsContainer = document.getElementById('alerts-container');
        if (!alertsContainer) return;
        
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show mb-2';
        alertDiv.innerHTML = `
            <strong><i class="bi bi-exclamation-triangle-fill"></i> Alerte ${alert.severity}</strong><br>
            <small>Zone ${alert.zone} - ${alert.message}</small><br>
            <small class="text-muted">${new Date(alert.timestamp).toLocaleString('fr-FR')}</small>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertsContainer.insertBefore(alertDiv, alertsContainer.firstChild);
        
        // Auto-supprimer après 10 secondes
        setTimeout(() => {
            alertDiv.remove();
        }, 10000);
    }
    
    showNotification(message, type = 'info', persistent = false) {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        const container = document.querySelector('.toast-container') || this.createToastContainer();
        container.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, { delay: persistent ? 10000 : 3000 });
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
    
    createToastContainer() {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(container);
        return container;
    }
    
    playNotificationSound() {
        // Audio simple (optionnel)
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    }
    
    updateZonesActivity(zonesData) {
        const container = document.getElementById('zones-activity');
        if (!container) return;
        
        if (!zonesData || Object.keys(zonesData).length === 0) {
            container.innerHTML = `
                <p class="text-muted text-center">
                    <i class="bi bi-info-circle"></i> Aucune activité détectée dans les 24 dernières heures
                </p>
            `;
            return;
        }
        
        const sortedZones = Object.entries(zonesData)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 9); // Afficher les 9 zones (A-I)
        
        const maxCount = Math.max(...Object.values(zonesData));
        
        container.innerHTML = sortedZones.map(([zone, count]) => {
            const percentage = (count / maxCount) * 100;
            return `
                <div class="mb-2">
                    <div class="d-flex justify-content-between mb-1">
                        <small><strong>Zone ${zone}</strong></small>
                        <small class="text-muted">${count} logs</small>
                    </div>
                    <div class="progress" style="height: 8px;">
                        <div class="progress-bar bg-primary" style="width: ${percentage}%"></div>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    requestRecentLogs(limit = 10) {
        if (this.connected) {
            this.socket.emit('request_recent_logs', { limit });
        }
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.emit('unsubscribe_monitoring');
            this.socket.disconnect();
        }
    }
}

// Initialiser au chargement de la page
let realtimeMonitor;

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initialisation du monitoring temps réel...');
    realtimeMonitor = new RealtimeMonitoring();
});

// Déconnexion propre avant de quitter
window.addEventListener('beforeunload', () => {
    if (realtimeMonitor) {
        realtimeMonitor.disconnect();
    }
});
