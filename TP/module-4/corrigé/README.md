# TP Module 4 - Corrigé : Application Production-Ready avec Blue/Green Deployment

## Solutions complètes et manifests

### Partie 1 : Prérequis et Configuration de Base

#### Vérification et installation de metrics-server

```bash
# Vérifier metrics-server
kubectl get deployment metrics-server -n kube-system

# Si absent, installer :
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Pour kind, patcher avec --kubelet-insecure-tls
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

# Vérifier que metrics-server fonctionne
kubectl get pods -n kube-system | grep metrics-server
kubectl top nodes
```

### Partie 2 : Déploiement avec Health Checks et Ressources

#### 2.1 Namespace et ConfigMap

```bash
# Créer le namespace
kubectl create namespace webapp-prod

# Vérifier la création
kubectl get namespaces | grep webapp-prod
```

**ConfigMap webapp-config :**

```yaml
# webapp-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: webapp-config
  namespace: webapp-prod
data:
  VERSION: "v1.0.0"
  STARTUP_DELAY: "5"
```

```bash
# Appliquer la ConfigMap
kubectl apply -f webapp-config.yaml
```

#### 2.2 Deployment et Service complets

**deployment-and-service.yaml corrigé :**

```yaml
---
apiVersion: v1
kind: Service
metadata:
  name: webapp-service
  namespace: webapp-prod
  labels:
    app: webapp
spec:
  selector:
    app: webapp
    version: v1  # Permet le routage Blue/Green
  ports:
  - port: 80
    targetPort: 5000
    protocol: TCP
    name: http
  type: ClusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp-deployment
  namespace: webapp-prod
  labels:
    app: webapp
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
      version: v1
  template:
    metadata:
      labels:
        app: webapp
        version: v1
    spec:
      containers:
      - name: webapp
        image: zwindler/webapp-python:v1.0.0
        ports:
        - containerPort: 5000
          name: http
        env:
        - name: FLASK_ENV
          value: "production"
        envFrom:
        - configMapRef:
            name: webapp-config
        resources:
          requests:
            memory: "128Mi"
            cpu: "250m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        startupProbe:
          httpGet:
            path: /startup
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 6
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        # Bonnes pratiques de sécurité
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
```

```bash
# Déployer l'application
kubectl apply -f deployment-and-service.yaml

# Validation
kubectl get pods -n webapp-prod -w
kubectl port-forward svc/webapp-service 8080:80 -n webapp-prod &
curl http://localhost:8080/health
curl http://localhost:8080/ready
curl http://localhost:8080/startup
```

### Partie 3 : Horizontal Pod Autoscaler (HPA)

#### 3.1 HPA Configuration

```yaml
# webapp-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: webapp-hpa
  namespace: webapp-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: webapp-deployment
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

#### 3.2 Test de l'HPA

```bash
# Appliquer l'HPA
kubectl apply -f webapp-hpa.yaml

# Vérifier l'HPA
kubectl get hpa -n webapp-prod
kubectl describe hpa webapp-hpa -n webapp-prod

# Générer de la charge (méthode simple)
kubectl run load-generator --image=busybox --restart=Never -n webapp-prod -- \
  /bin/sh -c "while true; do wget -q -O- http://webapp-service.webapp-prod.svc.cluster.local:80/load; done"

# Méthode intensive (plusieurs générateurs)
for i in {1..3}; do
  kubectl run load-generator-$i --image=busybox --restart=Never -n webapp-prod -- \
    /bin/sh -c "while true; do wget -q -O- http://webapp-service.webapp-prod.svc.cluster.local:80/load; sleep 0.1; done"
done

# Observer le scaling
kubectl get hpa -n webapp-prod -w
kubectl get pods -n webapp-prod -w

# Arrêter la charge et observer le scale-down
kubectl delete pod load-generator -n webapp-prod
kubectl delete pod load-generator-1 load-generator-2 load-generator-3 -n webapp-prod
```

### Partie 4 : Exposition via Ingress

#### 4.1 Ingress Configuration

```yaml
# webapp-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: webapp-ingress
  namespace: webapp-prod
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: webapp.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: webapp-service
            port:
              number: 80
```

#### 4.2 Configuration et tests

```bash
# Appliquer l'Ingress
kubectl apply -f webapp-ingress.yaml

# Configurer /etc/hosts
echo "127.0.0.1 webapp.local" | sudo tee -a /etc/hosts

# Tests depuis l'extérieur
curl http://webapp.local
curl http://webapp.local/health
curl http://webapp.local/version
curl http://webapp.local/metrics

# Vérifier l'ingress
kubectl get ingress -n webapp-prod
kubectl describe ingress webapp-ingress -n webapp-prod
```

### Partie 5 : Stratégie Blue/Green Deployment

#### 5.1 Préparer le déploiement Green

**Note pédagogique :** Cette section du corrigé suit l'approche du TP qui demande aux apprenants de réfléchir par eux-mêmes en repartant des manifests précédents. L'idée est de comprendre les patterns plutôt que de copier-coller.

L'objectif est de créer une nouvelle version de l'application qui affiche "green" au lieu de "v1.0.0". Il faut créer une ConfigMap, un Deployment et un Service séparés.

**Étape 1 : ConfigMap Green**

```bash
# Option 1 : Créer la ConfigMap Green avec kubectl
kubectl create configmap webapp-config-green \
  --from-literal=VERSION="green" \
  --from-literal=STARTUP_DELAY="3" \
  -n webapp-prod

# Option 2 : Créer un fichier YAML
cat > configmap-green.yaml << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: webapp-config-green
  namespace: webapp-prod
data:
  VERSION: "green"
  STARTUP_DELAY: "3"
EOF

kubectl apply -f configmap-green.yaml
```

**Étape 2 : Deployment Green**

Créer un nouveau fichier basé sur le Deployment existant, avec les modifications suivantes :
- `metadata.name`: `webapp-deployment-green`
- `metadata.labels.version`: `green`
- `spec.selector.matchLabels.version`: `green`
- `spec.template.metadata.labels.version`: `green`
- `spec.template.spec.containers[0].envFrom.configMapRef.name`: `webapp-config-green`

```yaml
# webapp-deployment-green.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp-deployment-green
  namespace: webapp-prod
  labels:
    app: webapp
    version: green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
      version: green
  template:
    metadata:
      labels:
        app: webapp
        version: green
    spec:
      containers:
      - name: webapp
        image: zwindler/webapp-python:v1.0.0
        ports:
        - containerPort: 5000
          name: http
        env:
        - name: FLASK_ENV
          value: "production"
        envFrom:
        - configMapRef:
            name: webapp-config-green
        resources:
          requests:
            memory: "128Mi"
            cpu: "250m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        startupProbe:
          httpGet:
            path: /startup
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 6
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
```

**Étape 3 : Service Green (pour test isolé)**

Créer un service temporaire pour tester Green avant basculement :

```yaml
# webapp-service-green.yaml
apiVersion: v1
kind: Service
metadata:
  name: webapp-service-green
  namespace: webapp-prod
  labels:
    app: webapp
    version: green
spec:
  selector:
    app: webapp
    version: green
  ports:
  - port: 80
    targetPort: 5000
    protocol: TCP
    name: http
  type: ClusterIP
```

**Déploiement et test :**

```bash
# Déployer toutes les ressources Green
kubectl apply -f configmap-green.yaml
kubectl apply -f webapp-deployment-green.yaml
kubectl apply -f webapp-service-green.yaml

# Vérifier le déploiement
kubectl get pods -n webapp-prod -l version=green

# Tester Green via port-forward avant basculement
kubectl port-forward svc/webapp-service-green 8080:80 -n webapp-prod &
curl http://localhost:8080/version  # Doit afficher "green"
curl http://localhost:8080/health

# Arrêter le port-forward
pkill -f "kubectl port-forward.*webapp-service-green"
```

#### 5.2 Basculement vers Green

Une fois que Green est déployé et testé, basculer le trafic principal :

```bash
# Vérifier l'état actuel (Blue)
curl http://webapp.local/version  # Doit afficher "v1.0.0"

# Basculer le Service principal vers Green
kubectl patch service webapp-service -n webapp-prod -p \
  '{"spec":{"selector":{"app":"webapp","version":"green"}}}'

# Vérifier le basculement
curl http://webapp.local/version  # Doit maintenant afficher "green"

# Vérifier les endpoints
kubectl get endpoints webapp-service -n webapp-prod
kubectl describe service webapp-service -n webapp-prod
```

#### 5.3 Vérification du basculement

Vérifier que le basculement a bien fonctionné :

```bash
# Tester via l'Ingress
curl http://webapp.local/version  # Doit maintenant afficher "green"

# Vérifier les endpoints
kubectl get endpoints webapp-service -n webapp-prod

# Observer les pods qui reçoivent le trafic
kubectl logs -f deployment/webapp-deployment-green -n webapp-prod
```

#### 5.4 Rollback si nécessaire

En cas de problème détecté sur l'application "green", effectuer un rollback :

```bash
# En cas de problème, rollback vers Blue
kubectl patch service webapp-service -n webapp-prod -p \
  '{"spec":{"selector":{"app":"webapp","version":"v1"}}}'

# Vérifier le rollback
curl http://webapp.local/version  # Doit afficher "v1.0.0"

# Nettoyer Green après validation du rollback
kubectl delete deployment webapp-deployment-green -n webapp-prod
kubectl delete service webapp-service-green -n webapp-prod
kubectl delete configmap webapp-config-green -n webapp-prod
```

### Partie 6 : Monitoring et Observabilité

#### 6.1 Métriques et logs

```bash
# Métriques des pods
kubectl top pods -n webapp-prod

# Métriques des nœuds
kubectl top nodes

# Logs de l'application
kubectl logs -f deployment/webapp-deployment -n webapp-prod

# Événements récents
kubectl get events -n webapp-prod --sort-by=.metadata.creationTimestamp

# Métriques Prometheus de l'application
curl http://webapp.local/metrics
```

#### 6.2 Tests de robustesse

**Test de liveness probe :**

```bash
# Simuler un crash
curl -X POST http://webapp.local/crash

# Observer le redémarrage automatique
kubectl get pods -n webapp-prod -w

# Vérifier les détails du restart
kubectl describe pod $(kubectl get pods -n webapp-prod -l app=webapp -o jsonpath='{.items[0].metadata.name}')

# Observer les événements de restart
kubectl get events -n webapp-prod --field-selector reason=Killing,reason=Started
```

**Test de readiness probe :**

```bash
# L'application doit être "ready" normalement
curl http://webapp.local/ready

# Simuler une indisponibilité de dépendance externe
kubectl exec deployment/webapp-deployment -n webapp-prod -- \
  curl -X POST http://localhost:5000/unready

# Vérifier que le pod est retiré des endpoints (sans redémarrage)
kubectl get endpoints webapp-service -n webapp-prod
kubectl get pods -n webapp-prod  # Pods restent "Running"

# Attendre la récupération automatique (30s) ou récupération manuelle
kubectl exec deployment/webapp-deployment -n webapp-prod -- \
  curl -X POST http://localhost:5000/recover

# Vérifier le retour dans les endpoints
kubectl get endpoints webapp-service -n webapp-prod
```

**Test de startup probe :**

```bash
# Créer un pod avec un délai de startup plus long
kubectl patch configmap webapp-config -n webapp-prod -p \
  '{"data":{"STARTUP_DELAY":"20"}}'

# Redémarrer les pods pour prendre en compte le nouveau délai
kubectl rollout restart deployment/webapp-deployment -n webapp-prod

# Observer le démarrage
kubectl get pods -n webapp-prod -w
kubectl describe pod $(kubectl get pods -n webapp-prod -l app=webapp -o jsonpath='{.items[0].metadata.name}')
```

## Commandes de débogage

```bash
# Debug général
kubectl get all -n webapp-prod
kubectl describe deployment webapp-deployment -n webapp-prod
kubectl describe hpa webapp-hpa -n webapp-prod

# Logs détaillés
kubectl logs -f deployment/webapp-deployment -n webapp-prod --previous
kubectl logs -f deployment/webapp-deployment -n webapp-prod -c webapp

# Événements
kubectl get events -n webapp-prod --sort-by=.metadata.creationTimestamp

# Tests de connectivité interne
kubectl run debug-pod --image=curlimages/curl -it --rm -n webapp-prod -- sh
# Dans le pod : curl http://webapp-service/health

# Port-forward pour debug
kubectl port-forward svc/webapp-service 8080:80 -n webapp-prod
```

## Nettoyage

```bash
# Supprimer toutes les ressources du TP
kubectl delete namespace webapp-prod

# Nettoyer /etc/hosts
sudo sed -i '' '/webapp.local/d' /etc/hosts

# Nettoyer les port-forwards si encore actifs
pkill -f "kubectl port-forward"
```
