# TP Module 5 : Sécurité dans Kubernetes - Corrigé

## Vue d'ensemble

Ce corrigé présente les solutions complètes pour les 3 parties du TP :
1. **RBAC** : Contrôle d'accès avec rôles et permissions
2. **Security Context** : Sécurisation avancée des containers
3. **Trivy** : Détection de vulnérabilités d'images

---

## Partie 1 : Contrôle d'accès RBAC - Corrigé

### 1.2 Role pod-reader

```yaml
# role-pod-reader.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: secure-app
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["services"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]
```

### 1.3 RoleBinding app-reader

```yaml
# rolebinding-app-reader.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-reader-binding
  namespace: secure-app
subjects:
- kind: ServiceAccount
  name: app-reader
  namespace: secure-app
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

### 1.4 Tests des permissions

```bash
# ✅ Permissions autorisées - devraient retourner "yes"
kubectl auth can-i get pods --as=system:serviceaccount:secure-app:app-reader -n secure-app
kubectl auth can-i list pods --as=system:serviceaccount:secure-app:app-reader -n secure-app
kubectl auth can-i get services --as=system:serviceaccount:secure-app:app-reader -n secure-app
kubectl auth can-i get pods/log --as=system:serviceaccount:secure-app:app-reader -n secure-app

# ❌ Permissions interdites - devraient retourner "no"
kubectl auth can-i create deployments --as=system:serviceaccount:secure-app:app-reader -n secure-app
kubectl auth can-i delete secrets --as=system:serviceaccount:secure-app:app-reader -n secure-app
kubectl auth can-i create pods --as=system:serviceaccount:secure-app:app-reader -n secure-app

# Lister toutes les permissions (optionnel)
kubectl auth can-i --list --as=system:serviceaccount:secure-app:app-reader -n secure-app
```

---

## Partie 2 : Security Context avancé - Corrigé

### Deployment sécurisé complet

```yaml
# secure-webapp-deployment.yaml
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
      securityContext:
        runAsUser: 1001
        runAsGroup: 1001
        fsGroup: 1001
      containers:
      - name: webapp
        image: nginx:1.29-alpine
        ports:
        - containerPort: 8080
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          capabilities:
            drop: ["ALL"]
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /var/cache/nginx
        - name: run
          mountPath: /var/run
        - name: nginx-config
          mountPath: /etc/nginx/nginx.conf
          subPath: nginx.conf
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
      volumes:
      - name: tmp
        emptyDir: {}
      - name: cache
        emptyDir: {}
      - name: run
        emptyDir: {}
      - name: nginx-config
        configMap:
          name: nginx-config
```

### Network tools avec capabilities

```yaml
# network-tools-pod.yaml
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
        add: ["NET_RAW"]  # Nécessaire pour ping
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
```

## Partie 3 : Détection de vulnérabilités avec Trivy - Corrigé

### Script de validation sécurisée

```bash
#!/bin/bash
# validate-image.sh

IMAGE="$1"
if [ -z "$IMAGE" ]; then
    echo "Usage: $0 <image:tag>"
    exit 1
fi

echo "🔍 Scanning image: $IMAGE"

# Scanner avec trivy
SCAN_RESULT=$(trivy image --exit-code 1 --severity CRITICAL "$IMAGE" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Image $IMAGE : Aucune vulnérabilité CRITICAL détectée"
    
    # Scanner les vulnérabilités HIGH
    HIGH_VULNS=$(trivy image --severity HIGH --quiet "$IMAGE" 2>/dev/null | wc -l)
    echo "ℹ️  Vulnérabilités HIGH détectées: $HIGH_VULNS"
    
    echo "✅ Image approuvée pour déploiement"
    exit 0
else
    echo "❌ Image $IMAGE : Vulnérabilités CRITICAL détectées!"
    echo "🚫 Déploiement refusé"
    echo "$SCAN_RESULT"
    exit 1
fi
```
