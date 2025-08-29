#!/usr/bin/env python3
"""
Application Flask simple pour le TP Module 4 - Kubernetes
Endpoints pour tester les health checks et l'autoscaling
"""

from flask import Flask, jsonify, request
import time
import threading
import os
from datetime import datetime

app = Flask(__name__)

# État de l'application
app_state = {
    'healthy': True,
    'ready': True,
    'startup_complete': False,
    'request_count': 0,
    'cpu_load': 0
}

def simulate_startup():
    """Simule un temps de démarrage configurable"""
    startup_delay = int(os.getenv('STARTUP_DELAY', '10'))
    print(f"Démarrage en cours... ({startup_delay}s)")
    time.sleep(startup_delay)
    app_state['startup_complete'] = True
    print("Démarrage terminé")

# Démarrer la simulation de startup en arrière-plan
startup_thread = threading.Thread(target=simulate_startup)
startup_thread.daemon = True
startup_thread.start()

@app.before_request
def count_requests():
    """Compteur de requêtes"""
    app_state['request_count'] += 1

@app.route('/')
def home():
    """Page d'accueil avec informations de l'application"""
    return jsonify({
        'message': 'Bonjour depuis l\'Application Python Production-Ready',
        'version': os.getenv('VERSION', 'v1.0.0'),
        'hostname': os.getenv('HOSTNAME', 'unknown'),
        'requests': app_state['request_count'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    """Health check basique - pour liveness probe"""
    if app_state['healthy']:
        return jsonify({
            'status': 'en bonne santé',
            'timestamp': datetime.now().isoformat()
        }), 200
    else:
        return jsonify({
            'status': 'en mauvaise santé',
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/ready')
def ready():
    """Readiness check - vérifie si l'app peut recevoir du trafic"""
    if app_state['ready'] and app_state['startup_complete']:
        return jsonify({
            'status': 'prêt',
            'startup': app_state['startup_complete'],
            'timestamp': datetime.now().isoformat()
        }), 200
    else:
        return jsonify({
            'status': 'pas prêt',
            'startup': app_state['startup_complete'],
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/startup')
def startup():
    """Startup check - pour startup probe"""
    if app_state['startup_complete']:
        return jsonify({
            'status': 'démarré',
            'timestamp': datetime.now().isoformat()
        }), 200
    else:
        return jsonify({
            'status': 'en cours de démarrage',
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/metrics')
def metrics():
    """Métriques basiques au format Prometheus"""
    return f"""# HELP webapp_requests_total Total requests
# TYPE webapp_requests_total counter
webapp_requests_total {app_state['request_count']}

# HELP webapp_cpu_load Simulated CPU load
# TYPE webapp_cpu_load gauge
webapp_cpu_load {app_state['cpu_load']}

# HELP webapp_healthy Application health status
# TYPE webapp_healthy gauge
webapp_healthy {1 if app_state['healthy'] else 0}
""", 200, {'Content-Type': 'text/plain'}

@app.route('/load')
def generate_load():
    """Génère de la charge CPU pour tester l'HPA"""
    duration = float(request.args.get('duration', 1.0))
    
    # Simulation de charge CPU en sommant des carrés
    start_time = time.time()
    while time.time() - start_time < duration:
        sum(i * i for i in range(1000))
    
    app_state['cpu_load'] = min(100, app_state['cpu_load'] + 10)
    
    return jsonify({
        'message': 'Charge générée',
        'duration': duration,
        'cpu_load': app_state['cpu_load']
    })

@app.route('/crash', methods=['POST'])
def crash():
    """Simule un crash de l'application (pour tester liveness probe)"""
    print("Simulation d'un crash...")
    app_state['healthy'] = False
    
    # Récupération automatique après 30 secondes
    def recover():
        time.sleep(30)
        app_state['healthy'] = True
        print("Application récupérée")
    
    recovery_thread = threading.Thread(target=recover)
    recovery_thread.daemon = True
    recovery_thread.start()
    
    return jsonify({
        'message': 'Application crashée - le health check va échouer',
        'recovery_in': '30 secondes'
    })

@app.route('/unready', methods=['POST'])
def simulate_unready():
    """Simule une dépendance externe indisponible (pour tester readiness probe)"""
    print("Simulation d'une dépendance externe indisponible...")
    app_state['ready'] = False
    
    # Récupération automatique après 30 secondes
    def recover():
        time.sleep(30)
        app_state['ready'] = True
        print("Dépendance externe rétablie")
    
    recovery_thread = threading.Thread(target=recover)
    recovery_thread.daemon = True
    recovery_thread.start()
    
    return jsonify({
        'message': 'Dépendance externe indisponible - readiness check va échouer',
        'recovery_in': '30 secondes'
    })

@app.route('/recover', methods=['POST'])
def manual_recover():
    """Récupération manuelle de l'application"""
    app_state['healthy'] = True
    app_state['ready'] = True
    return jsonify({
        'message': 'Application et dépendances rétablies manuellement'
    })

@app.route('/version')
def version():
    """Endpoint dédié à la version (utile pour Blue/Green)"""
    return jsonify({
        'version': os.getenv('VERSION', 'v1.0.0'),
        'hostname': os.getenv('HOSTNAME', 'unknown'),
        'timestamp': datetime.now().isoformat()
    })

# Réduction graduelle de la charge CPU
def reduce_cpu_load():
    """Réduit progressivement la charge CPU simulée"""
    while True:
        time.sleep(1)
        if app_state['cpu_load'] > 0:
            app_state['cpu_load'] = max(0, app_state['cpu_load'] - 1)

cpu_thread = threading.Thread(target=reduce_cpu_load)
cpu_thread.daemon = True
cpu_thread.start()

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    print(f"Application Python Production-Ready démarrée sur le port {port}")
    print(f"Health check: http://localhost:{port}/health")
    print(f"Ready check: http://localhost:{port}/ready")
    print(f"Startup check: http://localhost:{port}/startup")
    print(f"Métriques: http://localhost:{port}/metrics")
    
    app.run(host='0.0.0.0', port=port, debug=False)
