# TP Module 5 : Sécurité dans Kubernetes

## Objectif

Mettre en pratique les concepts de sécurité Kubernetes en implémentant :
- Contrôle d'accès RBAC
- Security Context
- Détection de vulnérabilités avec Trivy

## Prérequis

- Cluster Kubernetes fonctionnel (kind installé dans le TP2, ou autre)
- kubectl configuré
- curl installé

## Architecture du TP

```
Namespace: secure-app
    ↓
ServiceAccounts
    ↓
Roles et ClusterRoles
    ↓
RoleBindings associés
    ↓
Deployments avec Security Context avancé
    ↓
Tests de sécurité et scan Trivy
```

## Partie 1 : Contrôle d'accès RBAC

### 1.1 Créer un namespace et ServiceAccounts

```bash
# Créer le namespace
kubectl create namespace secure-app

# Créer un ServiceAccount dédié
kubectl create serviceaccount app-reader -n secure-app

# Vérifier la création
kubectl get serviceaccount -n secure-app
```

### 1.2 Créer un Role avec permissions limitées

Créez un Role `pod-reader` qui permet uniquement de :
- Lister et récupérer les Pods
- Lister les Services
- Accéder aux logs des Pods

```yaml
# role-pod-reader.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: secure-app
  name: pod-reader
rules:
# TODO: Ajouter les règles pour pods (get, list)
# TODO: Ajouter les règles pour services (get, list)  
# TODO: Ajouter les règles pour logs (get)
```

### 1.3 Créer un RoleBinding

Liez le ServiceAccount `app-reader` au Role `pod-reader` :

```yaml
# rolebinding-app-reader.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-reader-binding
  namespace: secure-app
subjects:
# TODO: Référencer le ServiceAccount app-reader
roleRef:
# TODO: Référencer le Role pod-reader
```

### 1.4 Tester les permissions

```bash
# Appliquer les ressources RBAC
kubectl apply -f role-pod-reader.yaml
kubectl apply -f rolebinding-app-reader.yaml
```

Testez les permissions avec `kubectl auth can-i`. En particulier, vérifiez que le ServiceAccount app-reader peut :

- ✅ Lister les pods dans secure-app
- ✅ Récupérer les logs des pods dans secure-app
- ❌ Créer des deployments dans secure-app
- ❌ Supprimer des secrets dans secure-app

## Partie 2 : Security Context avancé

### 2.1 Créer un Deployment sécurisé

Créez un Deployment avec un Security Context robuste en ajoutant les éléments suivants :

**Au niveau Pod (securityContext) :**
- `runAsUser: 1001`
- `runAsGroup: 1001`  
- `fsGroup: 1001`

**Au niveau Container (securityContext) :**
- `allowPrivilegeEscalation: false`
- `readOnlyRootFilesystem: true`
- `runAsNonRoot: true`
- `capabilities.drop: [ALL]`

**Volumes nécessaires :**
- Volume `emptyDir` pour `/tmp`
- Volume `emptyDir` pour `/var/cache/nginx`

```yaml
# manifest secure-webapp-deployment.yaml à améliorer
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-webapp
  namespace: secure-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: secure-webapp
  template:
    metadata:
      labels:
        app: secure-webapp
    spec:
      serviceAccountName: app-reader
      containers:
      - name: webapp
        image: nginx:1.29-alpine
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
```

### 2.2 Configurer Nginx pour non-root

Créez une ConfigMap pour configurer Nginx sur le port 8080 :

```yaml
# nginx-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
  namespace: secure-app
data:
  nginx.conf: |
    events {
        worker_connections 1024;
    }
    http {
        server {
            listen 8080;
            location / {
                root /usr/share/nginx/html;
                index index.html;
            }
        }
    }
```

### 2.3 Déployer et tester

```bash
# Appliquer les ressources
kubectl apply -f nginx-config.yaml
kubectl apply -f secure-webapp-deployment.yaml

# Vérifier le déploiement
kubectl get pods -n secure-app
kubectl describe pod -l app=secure-webapp -n secure-app

# Tester l'accès à l'application
kubectl port-forward deployment/secure-webapp 8080:8080 -n secure-app &
curl http://localhost:8080
```

### 2.4 Test d'escalade de privilèges

```bash
# Se connecter à un container et tester les limitations
kubectl exec -it deployment/secure-webapp -n secure-app -- sh

# Dans le container, tester :
whoami                   # Doit afficher un utilisateur non-root
id                       # Vérifier les groupes
touch /etc/test          # Doit échouer (read-only filesystem)
ps aux                   # Voir les processus
ping 8.8.8.8             # Doit échouer (pas de capability NET_RAW)
```

### 2.5 Exercice avec capabilities

Créez un Pod qui nécessite des capabilities spécifiques. 

Pour pouvoir faire un "ping", il est nécessaire d'ajouter la capability `NET_RAW`

```yaml
# manifest network-tools-pod.yaml à modifier
apiVersion: v1
kind: Pod
metadata:
  name: network-tools
  namespace: secure-app
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1001
  containers:
  - name: tools
    image: busybox:1.37
    command: ["sleep", "3600"]
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
```

```bash
# Déployer et tester les capabilities
kubectl apply -f network-tools-pod.yaml
kubectl exec -it network-tools -n secure-app -- ping -c 3 8.8.8.8

# Comparer avec un Pod sans capabilities
kubectl run no-caps --image=busybox:1.37 --restart=Never -n secure-app --overrides='
{
  "spec": {
    "securityContext": {"runAsNonRoot": true, "runAsUser": 1001},
    "containers": [{
      "name": "no-caps",
      "image": "busybox:1.37",
      "command": ["sleep", "3600"],
      "securityContext": {
        "capabilities": {"drop": ["ALL"]},
        "allowPrivilegeEscalation": false
      }
    }]
  }
}' -- sleep 3600

kubectl exec -it no-caps -n secure-app -- ping -c 1 8.8.8.8 || echo "Ping échoué comme attendu"
```

## Partie 3 : Détection de vulnérabilités avec Trivy

### 3.1 Installation de Trivy

```bash
# Installation sur Linux/macOS avec script officiel
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Vérifier l'installation
trivy version

# Alternative : installation via package manager
# macOS: brew install trivy
# Ubuntu: apt-get install trivy
```

### 3.2 Scanner des images pour identifier les vulnérabilités

Analysons les images utilisées dans notre cluster :

```bash
# Scanner l'image nginx utilisée dans notre déploiement sécurisé
echo "=== Scan de nginx:1.29-alpine (image récente) ==="
trivy image nginx:1.29-alpine

# Scanner une image volontairement ancienne pour voir les différences
echo "=== Scan de nginx:1.20 (image ancienne) ==="
trivy image nginx:1.20

# Scanner busybox
echo "=== Scan de busybox:1.37 ==="
trivy image busybox:1.37
```

### 3.3 Analyser les résultats et filtrer par gravité

```bash
# Afficher seulement les vulnérabilités HIGH et CRITICAL
trivy image --severity HIGH,CRITICAL nginx:1.29-alpine

# Scanner en format JSON pour traitement automatique
trivy image --format json --output nginx-scan.json nginx:1.29-alpine

# Scanner avec seuil de sortie (exit code 1 si vulnérabilités critiques)
trivy image --exit-code 1 --severity CRITICAL nginx:1.29-alpine
echo "Exit code: $?"
```

### 3.4 Scanner les images en cours d'exécution dans le cluster

```bash
# Récupérer toutes les images des pods dans notre namespace
echo "=== Images utilisées dans le namespace secure-app ==="
kubectl get pods -n secure-app -o jsonpath='{range .items[*]}{.spec.containers[*].image}{"\n"}{end}' | sort -u

# Scanner automatiquement toutes les images du namespace
echo "=== Scan automatique de toutes les images ==="
kubectl get pods -n secure-app -o jsonpath='{range .items[*]}{.spec.containers[*].image}{"\n"}{end}' | sort -u | xargs -I {} trivy image --severity HIGH,CRITICAL {}

# Scanner les images de tout le cluster (attention, peut être long!)
echo "=== Images du cluster complet ==="
kubectl get pods -A -o jsonpath='{range .items[*]}{.spec.containers[*].image}{"\n"}{end}' | sort -u | head -10
```

## Ressources complémentaires

- [RBAC Good Practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/)
- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Trivy Documentation](https://trivy.dev/)
- [Security Context Configuration](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)
