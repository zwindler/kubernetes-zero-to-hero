# TP Module 4 : Application Production-Ready avec Blue/Green Deployment

## Objectif

Déployer une application Python Flask prête pour la production avec toutes les bonnes pratiques du cycle de vie :
- Health checks (startup, liveness, readiness probes)
- Gestion des ressources (requests/limits)
- Horizontal Pod Autoscaler (HPA)
- Stratégie de déploiement Blue/Green
- Monitoring et observabilité

## Prérequis

- Cluster Kubernetes fonctionnel (kind installé dans le TP2, ou autre)
- kubectl configuré
- ingress controller opérationnel (nginx dans TP-3 ou autre)
- metrics-server installé (pour HPA)

## Architecture de l'application

```
Internet
    ↓
Ingress Controller
    ↓
Ingress (webapp.local)
    ↓
Service WebApp (ClusterIP:80 → 5000)
    ↓
Deployment WebApp (scaling automatique avec HPA)
    ↓
ConfigMap (configuration) + Secret (credentials)
    ↓
Monitoring (métriques applicatives)
```

**Note technique :** L'application Flask écoute sur le port 5000, mais le Service expose le port 80.

## Application utilisée

Nous utiliserons une application Python Flask simple qui expose :
- `GET /` : Page d'accueil avec informations de version
- `GET /health` : Health check basique (liveness probe)
- `GET /ready` : Readiness check avec vérification de dépendance externe
- `GET /startup` : Startup check avec délai configurable
- `GET /metrics` : Métriques Prometheus (compteurs de requêtes, santé)
- `GET /load` : Endpoint pour générer de la charge CPU
- `POST /crash` : Simule un crash de l'application
- `GET /version` : Information de version de l'application

L'application est packagée dans une image Docker `zwindler/webapp-python:v1.0.0`.

**Note :** Cette image est disponible sur Docker Hub. Si vous souhaitez la construire vous-même, les fichiers `Dockerfile`, `app.py` et `requirements.txt` sont fournis dans ce dossier.

## Partie 1 : Prérequis et Configuration de Base

Vérifiez que metrics-server est installé :

```bash
kubectl get deployment metrics-server -n kube-system
```

Si ce n'est pas le cas, installez-le :

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

Pour kind, ajoutez l'option `--kubelet-insecure-tls` :

```bash
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'
```

## Partie 2 : Déploiement avec Health Checks et Ressources

### 2.1 Créer le namespace et une configMap

Créez un namespace qui s'appelle `webapp-prod`, ainsi qu'une ConfigMap `webapp-config` pour la configuration de l'application, contenant les données suivantes :

```yaml
$ vi configmap.yaml
[...]
data:
  VERSION: "v1.0.0"      # Version affichée par l'application
  STARTUP_DELAY: "5"     # Délai de démarrage en secondes (pour tester startup probe)
```

### 2.2 Créer le Deployment et le Service "production-ready"

Vous trouverez dans ce dossier un fichier `deployment-and-service.yaml`. Cependant, il est incomplet. Remplir toutes les sections indiquées `# TODO` avec les valeurs qu'on attendrait en production.

Une fois le fichier corrigé, déployez l'application et vérifiez qu'elle fonctionne.

**Validation :**
```bash
# Vérifier que les pods démarrent correctement
kubectl get pods -n webapp-prod -w

# Tester les health checks
kubectl port-forward svc/webapp-service 8080:80 -n webapp-prod
curl http://localhost:8080/health
curl http://localhost:8080/ready
curl http://localhost:8080/startup
```

## Partie 3 : Horizontal Pod Autoscaler (HPA)

### 3.1 Créer l'HPA

```yaml
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

### 3.2 Tester l'HPA

```bash
kubectl apply -f webapp-hpa.yaml

# Vérifier l'HPA
kubectl get hpa
kubectl describe hpa webapp-hpa

# Générer de la charge pour tester le scaling
kubectl run load-generator --image=busybox --restart=Never -- \
  /bin/sh -c "while true; do wget -q -O- http://webapp-service.webapp-prod.svc.cluster.local:80/load; done"

# Alternative avec plusieurs générateurs de charge
for i in {1..3}; do
  kubectl run load-generator-$i --image=busybox --restart=Never -- \
    /bin/sh -c "while true; do wget -q -O- http://webapp-service.webapp-prod.svc.cluster.local:80/load; sleep 0.1; done"
done

# Observer le scaling
kubectl get hpa -w
kubectl get pods -w

# Nettoyer les générateurs de charge
kubectl delete pod load-generator
kubectl delete pod load-generator-1 load-generator-2 load-generator-3
```

## Partie 4 : Exposition via Ingress

### 4.1 Créer l'Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: webapp-ingress
  namespace: webapp-prod
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
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

### 4.2 Configuration locale

Si vous utilisez kind, pour accéder facilement à l'application, ajoutez à votre `/etc/hosts` :

```
127.0.0.1 webapp.local
```

Testez l'accès depuis un terminal de votre PC :

```bash
curl http://webapp.local
curl http://webapp.local/health
curl http://webapp.local/version
```

## Partie 5 : Stratégie Blue/Green Deployment

Le but de cette partie est de simuler le pattern de déploiement blue/green à l'aide des primitives disponibles dans Kubernetes. 

**Note :** en production, ces actions ne devraient pas être réalisées manuellement (sauf exception), mais via des outils.

### 5.1 Préparer un déploiement "Green"

Créez une nouvelle version de l'application pour simuler un déploiement Blue/Green. Vous pouvez repartir des manifests précédents qui nous ont permis de créer la ConfigMap, le Service et le Deployment.

La différence principale réside dans le fait que les labels doivent être différents, et que le `/version`doit renvoyer "green" et pas "v1.0.0".

Déployez et testez Green séparément :

```bash
kubectl apply -f configmap-green.yaml
kubectl apply -f webapp-deployment-and-service-green.yaml

# Tester Green via port-forward
kubectl port-forward svc/webapp-service-green 8080:80 -n webapp-prod
curl http://localhost:8080/version  # Doit afficher "green"
```

Une fois que vous avez validé que l'application "green" fonctionne correctement, basculez le traffic principal vers l'application en version "green".

### 5.2 Basculer le trafic vers Green

Une fois Green validé, basculez le Service principal :

```bash
# Méthode 1 : Patch du selector
kubectl patch service webapp-service -p \
  '{"spec":{"selector":{"app":"webapp","version":"green"}}}'

# Méthode 2 : Édition du Service
kubectl edit service webapp-service
# Changez selector.version de "v1" vers "green"
```

### 5.3 Vérifier le basculement

```bash
# Tester via l'Ingress
curl http://webapp.local/version

# Vérifier les endpoints
kubectl get endpoints webapp-service

# Observer les pods qui reçoivent le trafic
kubectl logs -f deployment/webapp-deployment-green
```

### 5.4 Rollback rapide si nécessaire

En cas de problème détecté sur l'application "green", effectuez un rollback :

```bash
# Rollback vers Blue (v1)
kubectl patch service webapp-service -n webapp-prod -p \
  '{"spec":{"selector":{"app":"webapp","version":"v1"}}}'

# Vérifier le rollback
curl http://webapp.local/version  # Doit afficher "v1.0.0"
kubectl get endpoints webapp-service -n webapp-prod

# Nettoyer l'environnement Green après validation du rollback
kubectl delete deployment webapp-deployment-green -n webapp-prod
kubectl delete service webapp-service-green -n webapp-prod
kubectl delete configmap webapp-config-green -n webapp-prod
```

## Partie 6 : Monitoring et Observabilité

### 6.1 Vérifier les métriques

```bash
# Métriques des pods
kubectl top pods

# Métriques des nœuds
kubectl top nodes

# Logs de l'application
kubectl logs -f deployment/webapp-deployment

# Événements
kubectl get events --sort-by=.metadata.creationTimestamp
```

### 6.2 Tests de robustesse

**Test de liveness probe :**

```bash
# Simuler un crash
curl -X POST http://webapp.local/crash

# Observer le redémarrage automatique
kubectl get pods -w
kubectl describe pod <pod-name>
```

**Test de readiness probe :**

L'application simule une dépendance externe. Testez le comportement de readiness :

```bash
# L'application doit être "ready" normalement
curl http://webapp.local/ready

# Simuler une indisponibilité de dépendance externe
kubectl exec deployment/webapp-deployment -- curl -X POST http://localhost:5000/unready

# Vérifier que le pod est retiré des endpoints (sans redémarrage)
kubectl get endpoints webapp-service
kubectl get pods  # Les pods restent "Running" mais ne reçoivent plus de trafic

# Rétablir la readiness après 30 secondes automatiquement
# Ou manuellement :
kubectl exec deployment/webapp-deployment -- curl -X POST http://localhost:5000/recover
```

## Ressources Complémentaires

### Documentation Officielle
- [Kubernetes Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [HPA Walkthrough](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/)
- [Deployment Strategies](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#strategy)
- [Resource Management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Security Context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)

### Articles et Bonnes Pratiques
- [Blue/Green Deployments](https://martinfowler.com/bliki/BlueGreenDeployment.html)
- [Production Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Health Check Patterns](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#container-probes)

### Outils Complémentaires
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
