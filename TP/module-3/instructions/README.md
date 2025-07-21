# TP Module 3 : Stack de monitoring avec Prometheus et Grafana

## Objectif

Déployer une stack de monitoring complète utilisant toutes les ressources de base de Kubernetes : [Prometheus](https://prometheus.io/) pour collecter les métriques et [Grafana](https://grafana.com/) pour les visualiser, le tout exposé via un Ingress.

## Prérequis

- Cluster Kubernetes fonctionnel (kind installé dans le TP2, ou autre)
- kubectl configuré
- Ingress Controller installé (nginx-ingress recommandé)

## Architecture de l'application

```
Internet
    ↓
Ingress Controller (1 ou plusieurs replicas)
    ↓
Ingress (monitoring.local)
    ↓
Service Grafana (ClusterIP:3000)
    ↓
Deployment Grafana (1 réplica)
    ↓
ConfigMap (datasources) + Secret (credentials)
    ↓
Service Prometheus (ClusterIP:9090)
    ↓
Deployment Prometheus (1 réplica)
    ↓
ConfigMap (prometheus.yml)
```

**Note importante** : dans ce TP, nous allons créer des manifests définissant notre application **à la main**, de manière à valider les concepts. Cependant, dans un contexte de production, nous utiliserons des outils de déploiement et de templating pour réaliser ces actions à notre place.

## Exercice 1 : Prérequis - Ingress Controller

### 1.1 Installer un Ingress Controller

Si vous utilisez kind (cf TP-2) :

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
```

Attendez que l'Ingress Controller soit prêt :

```bash
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

Retrouvez les Pods créés et vérifiez qu'ils fonctionnent

## Exercice 2 : Namespace et configuration

### 2.1 Créer le namespace

Créez un namespace `monitoring` pour isoler toutes les ressources de monitoring.

Vérifiez que le **Namespace** a bien été créé.

### 2.2 Créer les ConfigMaps et Secrets

Le monitoring aura besoin de :

- **ConfigMap** `prometheus-config` avec la configuration Prometheus :
  - Fichier `prometheus.yml` qui configure les targets à scraper
  - Scraping des métriques Kubernetes (API server, nodes, pods)

- **ConfigMap** `grafana-datasources` avec la connexion à Prometheus :
  - Configuration de Prometheus comme datasource
  - URL interne : `http://prometheus-service:9090`

- **Secret** `grafana-credentials` avec :
  - `admin-user` : `admin`
  - `admin-password` : `supersecret`

Note : un exemple de contenu des configMap à créer est donné en annexe, vous pouvez les utiliser.

## Exercice 3 : Grafana (interface de visualisation)

### 3.1 Créer le Deployment Grafana

Créez un Deployment `grafana-deployment` avec :
- Image officielle de grafana, version `12.0.2+security-01`
- 1 réplica
- Port 3000
- Variables d'environnement depuis le Secret pour l'authentification
- Volume avec la ConfigMap des datasources montée sur `/etc/grafana/provisioning/datasources/`
- Volume emptyDir (éphémère) pour les données temporaires sur `/var/lib/grafana`

**Aide - Squelette de manifest :**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana-deployment
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: #TODO ajouter une image grafana
        ports:
        # TODO ajouter un port
        env:
        # TODO: Ajouter les variables d'environnement directement depuis le Secret
        # - name: GF_SECURITY_ADMIN_USER
        #   ...
        volumeMounts:
        - name: datasources
          mountPath: /etc/grafana/provisioning/datasources/
        - name: storage
          mountPath: /var/lib/grafana
      volumes:
      # TODO: Ajouter les volumes (indice, il y en a 2)
```

### 3.2 Créer le Service Grafana

Créez un Service `grafana-service` de type ClusterIP sur le port 3000.

## Exercice 4 : Prometheus (collecteur de métriques)

### 4.1 Créer le Deployment Prometheus

Créez un Deployment `prometheus-deployment` avec :
- Image : `prom/prometheus`, version 3.4.2
- 1 réplica
- Port 9090
- Volume avec la ConfigMap montée sur `/etc/prometheus/`
- Volume emptyDir pour le stockage temporaire sur `/prometheus`
- Les arguments suivants pour que prometheus démarre correctement

```yaml
    spec:
      containers:
      - name: prometheus
        [...]
        args:
        - "--config.file=/etc/prometheus/prometheus.yml"
        - "--storage.tsdb.path=/prometheus/"
        - "--web.console.libraries=/etc/prometheus/console_libraries"
        - "--web.console.templates=/etc/prometheus/consoles"
        - "--storage.tsdb.retention.time=200h"
        - "--web.enable-lifecycle"
```

**Aide - Commande kubectl :**
```bash
# Générer un squelette de deployment à modifier
kubectl create deployment prometheus-deployment \
  --image=prom/prometheus:latest \
  --dry-run=client -o yaml > prometheus-deployment.yaml

# Puis éditez le fichier pour ajouter les volumes et configurations manquantes
```

### 4.2 Créer le Service Prometheus

Créez un Service `prometheus-service` de type ClusterIP sur le port 9090.

## Exercice 5 : Exposition avec Ingress

### 5.1 Créer l'Ingress

Créez un Ingress `monitoring-ingress` qui :
- Expose Grafana sur `monitoring.local`
- Optionnel : Expose Prometheus sur `monitoring.local/prometheus` (path-based routing)

### 5.2 Configurer l'accès local

Ajoutez à votre `/etc/hosts` pour pouvoir résoudre localement les URLs de votre cluster kind :

```
127.0.0.1 monitoring.local
```

## Exercice 6 : Tests et vérifications

### 6.1 Vérifier le déploiement

```bash
# Vérifier que tous les pods sont en cours d'exécution
kubectl get pods -n monitoring

# Vérifier les services et leurs endpoints
kubectl get svc -n monitoring
kubectl get endpoints -n monitoring

# Vérifier l'ingress
kubectl get ingress -n monitoring
```

### 6.2 Tester l'application

```bash
# Test depuis l'intérieur du cluster
kubectl run test-pod --image=curlimages/curl -it --rm -n monitoring -- sh
# Puis : curl http://prometheus-service:9090/metrics
# Et : curl http://grafana-service:3000

# Test depuis l'extérieur
curl http://monitoring.local
```

### 6.3 Explorer Grafana

1. Accédez à http://monitoring.local
2. Connectez-vous avec admin/supersecret
3. Vérifiez que Prometheus est configuré comme datasource
4. Explorez les métriques disponibles

## Exercice 7 : Gestion des ressources

### 6.1 Scaler l'Ingress Controller

Scalez le deployment de l'Ingress Controller pour observer le load balancing :

```bash
# Voir les deployments de l'ingress controller
kubectl get deployments -n ingress-nginx

# Scaler l'ingress controller à 2 replicas (comme prévu dans l'architecture)
kubectl scale deployment ingress-nginx-controller --replicas=2 -n ingress-nginx

# Observer les pods et la répartition
kubectl get pods -n ingress-nginx -w

# Tester la répartition de charge en accédant plusieurs fois à l'application, puis en allant voir les logs des pods de l'ingress controller
for i in {1..10}; do curl -s http://monitoring.local | head -1; done
```

### 6.2 Observer les métriques

Dans Grafana, créez des requêtes simples :
- `up` : voir tous les services qui sont "up"
- `kube_pod_info` : informations sur les pods
- `container_memory_usage_bytes` : utilisation mémoire des containers

### 6.3 Mettre à jour Prometheus

Simulez une mise à jour en changeant la version de Prometheus et observez le rolling update :

```bash
kubectl set image deployment/prometheus-deployment prometheus=prom/prometheus:v3.5.0 -n monitoring
kubectl rollout status deployment/prometheus-deployment -n monitoring
```

## Annexes

### Commandes utiles en cas de problèmes

```bash
# Voir les événements du namespace
kubectl get events -n monitoring --sort-by='.lastTimestamp'

# Débugger un pod spécifique
kubectl describe pod <nom-du-pod> -n monitoring
kubectl logs <nom-du-pod> -n monitoring

# Vérifier les configurations
kubectl get configmap prometheus-config -o yaml -n monitoring
kubectl get configmap grafana-datasources -o yaml -n monitoring
kubectl get secret grafana-credentials -o yaml -n monitoring

# Tester les services internes
kubectl port-forward svc/prometheus-service 9090:9090 -n monitoring
kubectl port-forward svc/grafana-service 3000:3000 -n monitoring
```

### Configuration Prometheus (prometheus.yml)

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'kubernetes-apiservers'
    kubernetes_sd_configs:
      - role: endpoints
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
      - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
        action: keep
        regex: default;kubernetes;https
```

### Configuration Grafana Datasource

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus-service:9090
    isDefault: true
```

