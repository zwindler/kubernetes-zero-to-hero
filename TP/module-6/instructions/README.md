# TP Module 6 : CNI avec Cilium et stockage persistant

## Objectifs 🎯

- Déployer un cluster kind avec Cilium comme CNI
- Configurer le stockage persistant avec extraMounts
- Déployer WordPress + MariaDB avec persistence
- Tester les Network Policies et observer avec Hubble
- Explorer l'extensibilité Kubernetes avec des Custom Resources

## Prérequis ✅

- kind installé et fonctionnel (TP 2)
- kubectl configuré
- Docker avec au moins 6 Go de RAM disponibles
- curl et jq installés

## Architecture du TP

```
Cluster kind avec Cilium
    ↓
Stockage persistant via extraMounts
    ↓
Déploiement WordPress + MariaDB
    ↓
Configuration Network Policies
    ↓
Observabilité avec Hubble
    ↓
Exploration des Custom Resources
```

## Partie 1 : Déployer un cluster kind avec Cilium

### 1.1 Configuration du cluster avec extraMounts

Créez un fichier `kind-config.yaml` pour configurer le cluster avec montage de volumes et désactivation du CNI par défaut :

```yaml
# Votre configuration ici
# Le cluster doit :
# - Avoir 1 control-plane et 2 worker nodes
# - Désactiver le CNI par défaut (disableDefaultCNI: true)
# - Configurer extraMounts pour le stockage local
# - Exposer les ports 30080 et 30443 pour les Ingress
```

**Indices** :
- Utilisez `kind: Cluster` et `apiVersion: kind.x-k8s.io/v1alpha4`
- Le paramètre `networking.disableDefaultCNI` doit être à `true`
- Pour les extraMounts, utilisez `/tmp/kind-data` sur l'hôte vers `/mnt/data` dans le container
- Le mapping de ports ressemblera à ça :

```yaml
  extraPortMappings:
  - containerPort: 30080
    hostPort: 80
    protocol: TCP
  - containerPort: 30443
    hostPort: 443
    protocol: TCP
```

### 1.2 Créer le cluster

```bash
# Créer le cluster avec la configuration
kind create cluster --config=kind-config.yaml --name=cilium-lab

# Vérifier que les nodes sont en NotReady (CNI manquant)
kubectl get nodes
```

### 1.3 Installer Cilium

```bash
# Télécharger le CLI Cilium
# Installation des manifests Cilium pour kind
# Vérifier l'installation
```

**Commandes à utiliser** :
- `curl` pour télécharger le CLI Cilium
- `cilium install` pour installer Cilium
- `cilium status` pour vérifier l'installation
- `kubectl get pods -n kube-system` pour voir les pods Cilium

**Indices** :
- URL du CLI : `https://github.com/cilium/cilium-cli/releases/latest/download/cilium-linux-amd64.tar.gz`
- Installation : `cilium install --set kubeProxyReplacement=true`
- Les nodes doivent passer à `Ready` après l'installation

#### 1.4 Déployer l'ingress controller nginx

Installer l'Ingress Controller NGINX pour kind

```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
```

Patcher le NodePort pour que le port HTTP non sécurisé soit le 30080 et le HTTPS soit le 30443

```bash
# Patcher le service ingress-nginx-controller pour fixer les ports NodePort
kubectl patch service ingress-nginx-controller -n ingress-nginx --type='json' \
  -p='[
    {"op": "replace", "path": "/spec/ports/0/nodePort", "value": 30080},
    {"op": "replace", "path": "/spec/ports/1/nodePort", "value": 30443}
  ]'

# Vérifier que les ports sont bien configurés
kubectl get service ingress-nginx-controller -n ingress-nginx
```

**Vérification** :
- Le service doit montrer les ports 30080 (HTTP) et 30443 (HTTPS)
- Attendre que l'Ingress Controller soit prêt avant de continuer

## Partie 2 : Configuration du stockage persistant

### 2.1 Créer une StorageClass pour le stockage local

Créez une StorageClass qui utilise le stockage local :

```yaml
# Votre StorageClass ici
# Elle doit :
# - Utiliser le provisioner kubernetes.io/no-provisioner
# - Être en mode volumeBindingMode: WaitForFirstConsumer
# - Avoir le nom "local-storage"
```

### 2.2 Créer les PersistentVolumes

Créez deux PersistentVolumes pour WordPress et MariaDB :

```yaml
# PV pour MariaDB (5Gi)
# PV pour WordPress (10Gi)
# Les deux doivent utiliser hostPath avec /mnt/data/mysql et /mnt/data/wordpress
```

**Indices** :
- Utilisez `accessModes: ["ReadWriteOnce"]`
- `persistentVolumeReclaimPolicy: Retain`
- `storageClassName: local-storage`

### 2.3 Appliquer les manifests de stockage

```bash
# Appliquer la StorageClass et les PVs
kubectl apply -f storage-config.yaml

# Vérifier les PVs
kubectl get pv
```

## Partie 3 : Déploiement de WordPress et MariaDB

### 3.1 Créer le namespace et les secrets

```bash
# Créer le namespace
kubectl create namespace wordpress

# Créer le secret pour les mots de passe MySQL
kubectl create secret generic mysql-pass \
  --from-literal=password=verySecurePassword! \
  -n wordpress
```

### 3.2 Déployer MariaDB

Modifiez le manifest `mariadb.yaml` de manière à obtenir :

- Un PersistentVolumeClaim (5Gi)
- Un Service de type ClusterIP
- Un Deployment avec l'image `mariadb:12.0.2`, les volumes + volumeMounts et les variables d'environnement appropriées

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  # TODO
spec:
  # TODO
---
apiVersion: v1
kind: Service
metadata:
  name: mariadb
  namespace: wordpress
  labels:
    app: mariadb
spec:
  ports:
    - #TODO
  selector:
    # TODO
  type: #TODO
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mariadb
  namespace: wordpress
  labels:
    app: mariadb
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mariadb
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        app: mariadb
    spec:
      containers:
      - image: mariadb:10.6
        name: mariadb
        env:
        - name: MYSQL_ROOT_PASSWORD
          # TODO
        - name: MYSQL_DATABASE
          value: wordpress
        - name: MYSQL_USER
          value: wordpress
        - name: MYSQL_PASSWORD
          # TODO
        ports:
        - containerPort: 3306
          name: mysql
        volumeMounts:
        - name: mysql-persistent-storage
          # TODO
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: mysql-persistent-storage
        # TODO
```

Indices : 

- mysql doit avoir son stockage dans `/var/lib/mysql`

### 3.3 Déployer WordPress

Créez le manifest `wordpress.yaml` avec :

- Un PersistentVolumeClaim (10Gi)  
- Un Service de type ClusterIP
- Un Deployment avec l'image `wordpress:6-php8.4` et les variables d'environnement requises

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  # TODO
spec:
  # TODO
---
apiVersion: v1
kind: Service
metadata:
  name: wordpress
  namespace: wordpress
  labels:
    app: wordpress
spec:
  ports:
    - #TODO
  selector:
    # TODO
  type: #TODO
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wordpress
  namespace: wordpress
  labels:
    app: wordpress
spec:
  replicas: 1
  selector:
    matchLabels:
      app: wordpress
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        app: wordpress
    spec:
      containers:
      - image: wordpress:6.3
        name: wordpress
        env:
        - name: WORDPRESS_DB_HOST
          value: #TODO
        - name: WORDPRESS_DB_USER
          value: #TODO
        - name: WORDPRESS_DB_PASSWORD
          # TODO
        - name: WORDPRESS_DB_NAME
          value: wordpress
        ports:
        - containerPort: 80
          name: wordpress
        volumeMounts:
        - name: wordpress-persistent-storage
          # TODO
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: wordpress-persistent-storage
        #TODO
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: wordpress-ingress
  namespace: wordpress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: wordpress.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: wordpress
            port:
              number: 80
```

Indices : 

- wordpress doit avoir son stockage dans `/var/www/html`
- l'image n'est peut être pas la bonne ;-\)

### 3.4 Appliquer les manifests

```bash
# Déployer MariaDB
kubectl apply -f mariadb.yaml

# Attendre que MariaDB soit prêt
kubectl wait --for=condition=ready pod -l app=mariadb -n wordpress --timeout=120s

# Déployer WordPress
kubectl apply -f wordpress.yaml

# Vérifier les deployments
kubectl get all -n wordpress
```

### 3.5 Tester l'accès

```bash
# Redirection de port pour accéder à WordPress
kubectl port-forward service/wordpress 8080:80 -n wordpress

# Dans un navigateur, ouvrir l'URL localhost:8080
# L'installeur de Wordpress devrait apparaitre

# Ou ajouter l'entrée dans /etc/hosts et utiliser l'Ingress
echo "127.0.0.1 wordpress.local" | sudo tee -a /etc/hosts
curl -I http://wordpress.local
```

## Partie 4 : Network Policies avec Cilium

### 4.1 Network Policy par défaut (deny-all)

Créez une Network Policy qui bloque tout le trafic par défaut dans le namespace wordpress :

```yaml
# Votre Network Policy ici
# Elle doit :
# - S'appliquer à tous les pods du namespace wordpress  
# - Bloquer tout le trafic ingress et egress par défaut
```

### 4.2 Network Policy pour MariaDB

Créez une Network Policy qui autorise uniquement WordPress à se connecter à MariaDB :

```yaml
# Network Policy pour MariaDB
# Doit autoriser uniquement :
# - Le trafic depuis les pods avec label app=wordpress
# - Sur le port 3306
```

### 4.3 Network Policy pour WordPress

Créez une Network Policy pour WordPress qui autorise :

- Le trafic HTTP entrant (port 80) pour l'ingress controller
- Le trafic sortant vers MariaDB (port 3306)

### 4.4 Appliquer et tester les Network Policies

```bash
# Appliquer les Network Policies
kubectl apply -f network-policies.yaml

# Tester la connectivité
kubectl exec -it deployment/wordpress -n wordpress -- curl mariadb:3306
# doit renvoyer:
#    curl: (1) Received HTTP/0.9 when not allowed
#    command terminated with exit code 1

# Tester depuis un pod non autorisé
kubectl run test-pod --image=nixery.dev/bash/curl --rm -it -- bash
# Dans le pod : curl mariadb.wordpress.svc.cluster.local:3306
# Ne doit pas rendre la main, contrairement à wordpress
```

## Partie 5 : Observabilité avec Hubble

### 5.1 Activer Hubble

```bash
# Activer Hubble pour l'observabilité réseau
cilium hubble enable --ui

# Vérifier que Hubble est déployé
kubectl get pods -n kube-system | grep hubble
```

### 5.2 Installer le CLI Hubble

```bash
# Télécharger et installer le CLI Hubble
export HUBBLE_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/hubble/master/stable.txt)
curl -L --fail --remote-name-all https://github.com/cilium/hubble/releases/download/$HUBBLE_VERSION/hubble-linux-amd64.tar.gz
tar xzf hubble-linux-amd64.tar.gz
sudo mv hubble /usr/local/bin
```

### 5.3 Observer le trafic réseau

```bash
# Port-forward pour accéder à Hubble Relay
kubectl port-forward -n kube-system svc/hubble-ui 4245:80

# Observer le trafic en temps réel dans un navigateur (localhost:4245)
```

## Partie 6 : Exploration des Custom Resources

### 6.1 Explorer les CRDs de Cilium

```bash
# Lister toutes les Custom Resource Definitions
kubectl get crd | grep cilium

# Examiner une CRD spécifique (par exemple CiliumNetworkPolicy)
kubectl describe crd ciliumnetworkpolicies.cilium.io

# Voir les instances de cette CRD
kubectl get ciliumnetworkpolicies -A
```

### 6.2 Créer une CiliumNetworkPolicy avancée

Supprimer la partie Ingress dans la NetworkPolicy existante.

L'ouverture de la page Wordpress doit répondre 

> 504 Gateway Time-out

La remplacer par une CiliumNetworkPolicy avec des règles L7 pour HTTP, qui n'autorise QUE l'ingress controller à réaliser des requêtes GET / POST / HEAD sur wordpress :

```yaml
apiVersion: "cilium.io/v2"
kind: CiliumNetworkPolicy
metadata:
  name: wordpress-l7-policy
  namespace: wordpress
spec:
  # Votre politique L7 ici
  # Doit autoriser uniquement les requêtes GET, POST et HEAD sur WordPress
```

**Vérification des règles L7 :**

```bash
# Tester une méthode autorisée (GET)
curl -IX GET http://wordpress.local

# Tester une méthode non autorisée (DELETE) - doit être bloquée
curl -IX DELETE http://wordpress.local
```


### 6.3 Explorer d'autres Custom Resources

```bash
# Explorer les Custom Resources du cluster
kubectl api-resources --api-group=cilium.io

# Examiner les CiliumEndpoints
kubectl get ciliumendpoints -n wordpress

# Voir les détails d'un endpoint
kubectl describe ciliumendpoint <nom-endpoint> -n wordpress
```

## Partie 7 : Tests de persistance et nettoyage

### 7.1 Tester la persistance des données

```bash
# Créer du contenu dans WordPress via l'interface web ou CLI
kubectl exec -it deployment/wordpress -n wordpress -- wp-cli.phar post create --post_title="Test Post" --post_content="Contenu persistant" --allow-root

# Supprimer et recréer le pod WordPress
kubectl delete pod -l app=wordpress -n wordpress

# Attendre la recreation et vérifier que les données persistent
kubectl wait --for=condition=ready pod -l app=wordpress -n wordpress --timeout=120s
```

### 7.2 Monitoring des volumes

```bash
# Vérifier l'utilisation des PVCs
kubectl get pvc -n wordpress

# Voir les détails du stockage
kubectl describe pv

# Examiner les montages dans les pods
kubectl exec -it deployment/mariadb -n wordpress -- df -h
```

## Ressources 📚

- [Cilium Documentation](https://docs.cilium.io/)
- [Hubble Observability](https://docs.cilium.io/en/stable/overview/intro/#what-is-hubble)
- [Kind Documentation - extraMounts](https://kind.sigs.k8s.io/docs/user/configuration/#extra-mounts)
- [Kubernetes Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Custom Resource Definitions](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
