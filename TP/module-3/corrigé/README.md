# TP Module 3 - Corrigé : Stack de monitoring avec Prometheus et Grafana

## Commandes complètes et manifests

### Exercice 1 : Prérequis - Ingress Controller

```bash
# Installation de l'Ingress Controller pour kind
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Attendre que l'Ingress Controller soit prêt
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s

# Vérifier les pods créés
kubectl get pods -n ingress-nginx
```

### Exercice 2 : Namespace et configuration

#### 2.1 Créer le namespace

```bash
# Créer le namespace monitoring
kubectl create namespace monitoring

# Vérifier la création
kubectl get namespaces
```

#### 2.2 Créer les ConfigMaps et Secrets

**ConfigMap Prometheus :**

```bash
# Créer le fichier prometheus.yml
cat > prometheus.yml << EOF
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
EOF

# Créer la ConfigMap prometheus-config
kubectl create configmap prometheus-config \
  --from-file=prometheus.yml \
  -n monitoring
```

**ConfigMap Grafana Datasources :**

```bash
# Créer le fichier datasources.yml
cat > datasources.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus-service:9090
    isDefault: true
EOF

# Créer la ConfigMap grafana-datasources
kubectl create configmap grafana-datasources \
  --from-file=datasources.yml \
  -n monitoring
```

**Secret Grafana :**

```bash
# Créer le secret grafana-credentials
kubectl create secret generic grafana-credentials \
  --from-literal=admin-user=admin \
  --from-literal=admin-password=supersecret \
  -n monitoring
```

### Exercice 3 : Grafana (interface de visualisation)

#### 3.1 Deployment Grafana

```yaml
# grafana-deployment.yaml
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
        image: grafana/grafana:12.0.2+security-01
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_USER
          valueFrom:
            secretKeyRef:
              name: grafana-credentials
              key: admin-user
        - name: GF_SECURITY_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: grafana-credentials
              key: admin-password
        volumeMounts:
        - name: datasources
          mountPath: /etc/grafana/provisioning/datasources/
        - name: storage
          mountPath: /var/lib/grafana
      volumes:
      - name: datasources
        configMap:
          name: grafana-datasources
      - name: storage
        emptyDir: {}
```

```bash
# Appliquer le deployment
kubectl apply -f grafana-deployment.yaml
```

#### 3.2 Service Grafana

```yaml
# grafana-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: grafana-service
  namespace: monitoring
spec:
  selector:
    app: grafana
  ports:
  - port: 3000
    targetPort: 3000
  type: ClusterIP
```

```bash
# Appliquer le service
kubectl apply -f grafana-service.yaml
```

### Exercice 4 : Prometheus (collecteur de métriques)

#### 4.1 Deployment Prometheus

```bash
# Générer le squelette
kubectl create deployment prometheus-deployment \
  --image=prom/prometheus:v3.4.2 \
  --dry-run=client -o yaml > prometheus-deployment.yaml
```

**Prometheus Deployment complet :**

```yaml
# prometheus-deployment.yaml (version finale)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus-deployment
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:v3.4.2
        ports:
        - containerPort: 9090
        args:
        - "--config.file=/etc/prometheus/prometheus.yml"
        - "--storage.tsdb.path=/prometheus/"
        - "--web.console.libraries=/etc/prometheus/console_libraries"
        - "--web.console.templates=/etc/prometheus/consoles"
        - "--storage.tsdb.retention.time=200h"
        - "--web.enable-lifecycle"
        volumeMounts:
        - name: prometheus-config
          mountPath: /etc/prometheus/
        - name: prometheus-storage
          mountPath: /prometheus/
      volumes:
      - name: prometheus-config
        configMap:
          name: prometheus-config
      - name: prometheus-storage
        emptyDir: {}
```

```bash
# Appliquer le deployment
kubectl apply -f prometheus-deployment.yaml
```

#### 4.2 Service Prometheus

```yaml
# prometheus-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: prometheus-service
  namespace: monitoring
spec:
  selector:
    app: prometheus
  ports:
  - port: 9090
    targetPort: 9090
  type: ClusterIP
```

```bash
# Appliquer le service
kubectl apply -f prometheus-service.yaml
```

### Exercice 5 : Exposition avec Ingress

#### 5.1 Ingress

```yaml
# monitoring-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: monitoring-ingress
  namespace: monitoring
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: monitoring.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: grafana-service
            port:
              number: 3000
```

```bash
# Appliquer l'ingress (version simple)
kubectl apply -f monitoring-ingress.yaml
```

#### 5.2 Configuration /etc/hosts

```bash
# Ajouter à /etc/hosts
echo "127.0.0.1 monitoring.local" | sudo tee -a /etc/hosts
```

### Exercice 6 : Tests et vérifications

#### 6.1 Vérifications du déploiement

```bash
# Vérifier que tous les pods sont en cours d'exécution
kubectl get pods -n monitoring

# Sortie attendue :
# NAME                                   READY   STATUS    RESTARTS   AGE
# grafana-deployment-xxxx                1/1     Running   0          5m
# prometheus-deployment-xxxx             1/1     Running   0          3m

# Vérifier les services et leurs endpoints
kubectl get svc -n monitoring
kubectl get endpoints -n monitoring

# Vérifier l'ingress
kubectl get ingress -n monitoring
```

#### 6.2 Tests de l'application

```bash
# Test depuis l'intérieur du cluster
kubectl run test-pod --image=curlimages/curl -it --rm -n monitoring -- sh

# Dans le pod de test :
curl http://prometheus-service:9090/metrics
curl http://grafana-service:3000

# Test depuis l'extérieur
curl http://monitoring.local

# Test avec un navigateur
open http://monitoring.local  # macOS
```

#### 6.3 Explorer Grafana

1. **Accéder à Grafana :** http://monitoring.local
2. **Se connecter :**
   - Username: `admin`
   - Password: `supersecret`
3. **Vérifier la datasource :** Aller dans Configuration → Data sources
4. **Tester les métriques :** Aller dans Explore et essayer :
   - `up`
   - `kube_pod_info`
   - `container_memory_usage_bytes`

### Exercice 7 : Gestion des ressources

#### 7.1 Scaler l'Ingress Controller

```bash
# Voir les deployments de l'ingress controller
kubectl get deployments -n ingress-nginx

# Scaler l'ingress controller à 2 replicas
kubectl scale deployment ingress-nginx-controller --replicas=2 -n ingress-nginx

# Observer les pods et la répartition
kubectl get pods -n ingress-nginx -w
```

#### 7.2 Observer les métriques

Dans Grafana, créer des requêtes :

- `up` : voir tous les services "up"
- `kube_pod_info` : informations sur les pods
- `container_memory_usage_bytes` : utilisation mémoire

#### 7.3 Rolling update de Prometheus

```bash
# Simuler une mise à jour
kubectl set image deployment/prometheus-deployment \
  prometheus=prom/prometheus:v3.5.0 -n monitoring

# Suivre le rollout
kubectl rollout status deployment/prometheus-deployment -n monitoring

# Vérifier l'historique
kubectl rollout history deployment/prometheus-deployment -n monitoring

# En cas de problème, rollback
kubectl rollout undo deployment/prometheus-deployment -n monitoring
```

## Commandes de débogage utiles

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

# Tester les services internes avec port-forward
kubectl port-forward svc/prometheus-service 9090:9090 -n monitoring &
kubectl port-forward svc/grafana-service 3000:3000 -n monitoring &

# Accéder aux services via localhost
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
```