---
marp: true
theme: gaia
markdown.marp.enableHtml: true
paginate: true
---

<style>

section {
  background-color: #fefefe;
  color: #333;
}

img[alt~="center"] {
  display: block;
  margin: 0 auto;
}
blockquote {
  background: #ffedcc;
  border-left: 10px solid #d1bf9d;
  margin: 1.5em 10px;
  padding: 0.5em 10px;
}
blockquote:before{
  content: unset;
}
blockquote:after{
  content: unset;
}
</style>

<!-- _class: lead -->

# Module 3 : Ressources de base
## Les objets essentiels de Kubernetes

*Formation Kubernetes - Débutant à Avancé*

---

## Plan du Module 3

**Partie 1 : YAML et kubectl**
- Structure des manifests, métadonnées, namespaces, kubeconfig
- Commandes kubectl et gestion du cluster

**Partie 2 : Les ressources Kubernetes**  
- Namespaces, Pods, Deployments, Services
- ConfigMaps, Secrets, Volumes, Ingress, Jobs

![bg fit right:30%](binaries/kubernetes_small.png)

---

<!-- _class: lead -->

# Partie 1 : YAML et kubectl

---

TODO slide pour donner un peu de contexte sur le format YAML et indiquer qu'on va en faire beaucoup dans Kubernetes

---

## Structure d'un manifest YAML pour K8s

**Tout objet Kubernetes suit la même structure :**

```yaml
apiVersion: v1           # Version de l'API à utiliser
kind: Pod                # Type de ressource Kubernetes
metadata:                # Métadonnées de l'objet
  name: mon-objet
  namespace: default
  # ...
spec:                    # Configuration souhaitée
  # ... configuration spécifique en fonction du type
status:                  # État actuel (géré par Kubernetes)
  # ... état de l'objet (lecture seule)
```

**4 sections obligatoires :** `apiVersion`, `kind`, `metadata`, `spec`

---

## Métadonnées : Organisation et identification

**Les `metadata` contiennent des informations cruciales :**

```yaml
metadata:
  name: nginx-web-server        # Nom unique dans le namespace
  namespace: production         # Isolation logique
  labels:                       # Étiquettes pour sélection/groupement
    app: nginx
    component: web-server
    version: "1.21"
    env: production
    team: frontend
  annotations:                  # Métadonnées non-sélectionnables
    deployment.kubernetes.io/revision: "3"
    description: "Serveur web principal"
```

---

## Focus : labels vs annotations :

- **Labels** : permettent de filtrer les ressources
- **Annotations** : Documentation et métadonnées

**Note** : selon le type de ressource, les labels sont parfois immuables, contrairement aux annotations

---

## Namespaces dans les manifests (1/2)

Certaines ressources peuvent être organisées

```yaml
# Créer un namespace
apiVersion: v1
kind: Namespace
metadata:
  name: development
  labels:
    env: dev
    team: backend
```

---

## Namespaces dans les manifests (2/2)


```yaml
# Utiliser un namespace dans une ressource
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
  namespace: development
  labels:
    app: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.29
```

**Bonne pratique :** toujours spécifier le **namespace** dans vos manifests

---

## le kubeconfig (1/2)

**Le fichier de connexion à Kubernetes**

On peut avoir plusieurs utilisateurs, clusters, etc dans un même fichier

TODO structure logique du fichier kubeconfig

---

## le kubeconfig (2/2)


```yaml
# ~/.kube/config
apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority-data: LS0tLS1CRU...
    server: https://kubernetes.example.com:6443 # URL de l'api-server
  name: prod-cluster
contexts:
- context:
    cluster: prod-cluster
    user: admin
    namespace: webapp # Namespace par défaut de ce contexte
  name: prod-admin
current-context: prod-admin
users:
- name: admin
  user:
    client-certificate-data: LS0tLS1CRU...
    client-key-data: LS0tLS1CRU...
```

---

## kubectl : état du cluster

**Maintenant que nous comprenons les manifests, manipulons-les :**

```bash
# Informations sur le cluster
kubectl version                    # Versions client/serveur
kubectl cluster-info              # Infos du cluster

# Explorer les APIs disponibles
kubectl api-resources             # Toutes les ressources
kubectl api-versions              # Versions d'API disponibles
```

---

## kubectl : commandes génériques sur les diverses ressources

```bash
# Commandes génériques (fonctionne avec toute ressource)
kubectl get <type>                # Lister des ressources
kubectl describe <type> <nom>     # Détails d'une ressource
kubectl create -f <fichier>       # Créer depuis un fichier
kubectl apply -f <fichier>        # Appliquer (recommandé)
kubectl delete <type> <nom>       # Supprimer une ressource
```

---

## Gestion des contextes et namespaces

**Naviguer entre différents environnements :**

```bash
# Gestion des contextes
kubectl config get-contexts                    # Liste tous les contextes
kubectl config current-context               # Contexte actuel
kubectl config use-context prod-admin        # Changer de contexte

# Gestion des namespaces
kubectl get namespaces                        # Lister tous les namespaces
kubectl config set-context --current --namespace=production

# Ou spécifier pour une commande
kubectl get pods --namespace production      # ou -n production
kubectl get pods --all-namespaces           # ou -A
```

**Astuce :** Utiliser des outils comme `kubectx` et `kubens` pour faciliter le changement de contexte/namespace.

---

## Sélecteurs et labels avec kubectl

**Maintenant que nous comprenons les labels dans les manifests :**

```bash
# Utiliser les labels pour filtrer
kubectl get pods -l app=nginx                 # Pods avec label app=nginx
kubectl get pods -l app=nginx,env=production  # ET logique
kubectl get pods -l 'env in (dev,staging)'    # OU logique
kubectl get pods -l app!=nginx                # Négation

# Afficher les labels
kubectl get pods --show-labels                # Voir tous les labels
kubectl get pods -L app,env                   # Colonnes spécifiques

# Modifier les labels
kubectl label pods mon-pod version=v2         # Ajouter/modifier
kubectl label pods mon-pod version-           # Supprimer
```

---

## Formats de sortie et débogage

```bash
# Formats d'affichage
kubectl get pods -o wide                      # Plus de détails
kubectl get pods -o yaml                      # Format YAML complet
kubectl get pods -o json                      # Format JSON
kubectl get pods -o jsonpath='{.items[0].metadata.name}'

# Suivi en temps réel
kubectl get pods --watch                      # ou -w
kubectl logs -f mon-pod                       # Logs en temps réel

# Débogage
kubectl describe pod mon-pod                  # Événements et détails
kubectl logs mon-pod                          # Logs du conteneur
kubectl exec -it mon-pod -- /bin/bash         # Shell interactif
```

---

## Astuces kubectl (1/2)

**Commandes utiles pour toute ressource :**

```bash
# Générer du YAML
kubectl create <type> <nom> --dry-run=client -o yaml

# Éditer en direct
kubectl edit <type> <nom>

# Récupérer la configuration
kubectl get <type> <nom> -o yaml > backup.yaml
```

---

## Astuces kubectl (2/2)

```bash
# Surveiller les événements
kubectl get events --watch
kubectl get events --sort-by='.lastTimestamp'

# Aide contextuelle
kubectl explain <type>              # Documentation du type
kubectl explain <type>.spec         # Documentation d'une section
```

---

## Première exploration du cluster (cf module 2)

```bash
# Quels types de ressources sont disponibles ?
kubectl api-resources

# Qu'est-ce qui tourne dans le cluster ?
kubectl get all -A

# Les namespaces système
kubectl get namespaces

# Les nœuds du cluster
kubectl get nodes -o wide
```

> Maintenant que nous maîtrisons l'outil, explorons les ressources !

---

<!-- _class: lead -->

# Partie 2 : Les ressources Kubernetes
## Les objets logiques pour construire nos applications

---

## Namespaces : Isolation et organisation

TODO rework

**Cas d'usage courants :**
- **Environnements** : `development`, `staging`, `production`
- **Équipes** : `team-frontend`, `team-backend`, `team-data`  
- **Applications** : `wordpress`, `monitoring`, `logging`
- **Clients** : `client-a`, `client-b` (multi-tenant)

**Isolation fournie :**
- **Noms** : Deux pods peuvent avoir le même nom dans des namespaces différents
- **Réseau** : Politiques réseau par namespace (optionnel)
- **Quotas** : Limites CPU/RAM/stockage par namespace
- **RBAC** : Permissions d'accès par namespace

---

## Commandes pour les namespaces

```bash
# Créer un namespace
kubectl create namespace production
kubectl apply -f namespace.yaml

# Utiliser un namespace spécifique
kubectl get pods -n development
kubectl apply -f app.yaml -n development

# Définir un namespace par défaut
kubectl config set-context --current --namespace=development
```

---

## Pods

TODO

---

## Pods : exemple de manifest

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
spec:
  containers:
  - name: nginx
    image: nginx:1.21
    ports:
    - containerPort: 80
```

**Note** : on créera rarement "directement" des Pods sur un cluster Kubernetes. Il existe d'autres ressources de plus haut niveau.

---

## Cycle de vie d'un Pod

**États d'un Pod :**

- **Pending** : En attente de placement sur un Node
- **Running** : Au moins un conteneur s'exécute
- **Succeeded** : Tous les conteneurs se sont terminés avec succès
- **Failed** : Au moins un conteneur a échoué
- **Unknown** : État du Pod indéterminable

**Commandes pour les Pods :**

```bash
# Voir l'état des Pods
kubectl get pods
kubectl get pods -o wide  # Plus de détails
kubectl describe pod nginx-pod

# Logs et debug
kubectl logs nginx-pod
kubectl logs nginx-pod -f    # En temps réel
kubectl exec -it nginx-pod -- bash  # Se connecter au Pod
```

---

## Deployments : Gérer les Pods

**Contrôleur qui gère des groupes de Pods identiques**

- **Réplicas** : Maintient un nombre défini de Pods
- **Rolling updates** : Mises à jour sans interruption
- **Rollback** : Retour à une version précédente
- **Scaling** : Augmentation/diminution du nombre de réplicas

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
        ports:
        - containerPort: 80
```

---

## Deployments : Opérations courantes

**Commandes pour gérer les Deployments :**

```bash
# Créer un deployment
kubectl create deployment nginx --image=nginx:1.21

# Scaler un deployment
kubectl scale deployment nginx --replicas=5

# Mettre à jour l'image
kubectl set image deployment/nginx nginx=nginx:1.22

# Voir l'historique des déploiements
kubectl rollout history deployment/nginx

# Rollback vers la version précédente
kubectl rollout undo deployment/nginx

# Voir le statut du rollout
kubectl rollout status deployment/nginx
```

---

## Services : Exposer les applications

**Abstraction qui expose un ensemble de Pods**

- **Load balancing** : Répartit le trafic entre les Pods
- **Service discovery** : Nom DNS stable pour l'application
- **Sélection par labels** : Trouve automatiquement les Pods cibles

**Types de Services :**
- **ClusterIP** : Accès interne uniquement (défaut)
- **NodePort** : Expose sur un port de chaque Node
- **LoadBalancer** : Crée un load balancer externe (cloud)
- **ExternalName** : Alias DNS vers un service externe

---

## Services : Exemples pratiques

```yaml
# Service ClusterIP (interne)
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  selector:
    app: nginx
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

```yaml
# Service NodePort (exposé)
apiVersion: v1
kind: Service
metadata:
  name: nginx-nodeport
spec:
  selector:
    app: nginx
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080
  type: NodePort
```

---

## Services : Découverte et résolution DNS

**Kubernetes fournit un DNS interne automatique :**

```bash
# Dans le même namespace
curl http://nginx-service

# Dans un autre namespace
curl http://nginx-service.production.svc.cluster.local

# Variables d'environnement automatiques
echo $NGINX_SERVICE_SERVICE_HOST
echo $NGINX_SERVICE_SERVICE_PORT
```

**Commandes pour les Services :**
```bash
kubectl get services                 # Lister les services
kubectl get endpoints nginx-service # Voir les IPs des Pods
kubectl describe service nginx-service # Détails du service
```

---

## Pratique : Déployer une application complète

**Exercice : Créer un déploiement complet avec les 4 ressources**

```bash
# 1. Créer le namespace
kubectl create namespace demo

# 2. Déployer nginx
kubectl create deployment nginx --image=nginx:1.21 -n demo

# 3. Scaler à 3 réplicas
kubectl scale deployment nginx --replicas=3 -n demo

# 4. Exposer avec un service
kubectl expose deployment nginx --port=80 --type=NodePort -n demo

# 5. Vérifier que tout fonctionne
kubectl get all -n demo
kubectl get pods -n demo -o wide
kubectl describe service nginx -n demo
```

---

## Ingress : Exposition HTTP/HTTPS

**Routage HTTP(S) intelligent vers les Services**

- **Domaines** : Routage basé sur le nom d'hôte
- **Chemins** : Routage basé sur l'URL
- **TLS** : Terminaison SSL/TLS
- **Load balancing** : Répartition du trafic

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nginx-ingress
spec:
  rules:
  - host: nginx.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: nginx-service
            port:
              number: 80
```

> **Important :** Nécessite un Ingress Controller (nginx, traefik, etc.)

---

## Volumes : Stockage persistant

**Types de volumes courants :**

- **emptyDir** : Volume temporaire (durée de vie du Pod)
- **hostPath** : Dossier de l'hôte (dangereux en production)
- **persistentVolumeClaim** : Stockage persistant
- **configMap/secret** : Configuration et secrets
- **nfs, cifs** : Stockage réseau

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-volume
spec:
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: html-volume
      mountPath: /usr/share/nginx/html
  volumes:
  - name: html-volume
    emptyDir: {}
```

---

## PersistentVolumes et PersistentVolumeClaims

**Séparation entre stockage et consommation :**

```yaml
# PersistentVolumeClaim (demande de stockage)
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nginx-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: fast-ssd
```

```yaml
# Utilisation dans un Pod
spec:
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: storage
      mountPath: /usr/share/nginx/html
  volumes:
  - name: storage
    persistentVolumeClaim:
      claimName: nginx-pvc
```

---

## ConfigMaps : Configuration externalisée

**Stockage de configuration sous forme de clé-valeur :**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database_url: "postgresql://db:5432/myapp"
  log_level: "info"
  config.yaml: |
    server:
      port: 8080
      host: 0.0.0.0
    database:
      driver: postgres
```

```yaml
# Utilisation en variables d'environnement
spec:
  containers:
  - name: app
    image: myapp:latest
    envFrom:
    - configMapRef:
        name: app-config
```

---

## Secrets : Données sensibles

**Stockage sécurisé de mots de passe, clés, certificats :**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  database_password: cGFzc3dvcmQ=  # base64 de "password"
  api_key: YWJjZGVmZ2g=           # base64 de "abcdefgh"
```

```bash
# Créer un secret depuis la ligne de commande
kubectl create secret generic app-secrets \
  --from-literal=database_password=password \
  --from-literal=api_key=abcdefgh

# Utilisation dans un Pod
spec:
  containers:
  - name: app
    image: myapp:latest
    env:
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: database_password
```

---

## Jobs : Tâches ponctuelles

**Exécution de tâches qui se terminent :**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: data-migration
spec:
  template:
    spec:
      containers:
      - name: migration
        image: migrate:latest
        command: ["./migrate", "up"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
      restartPolicy: Never
  backoffLimit: 3
```

**Cas d'usage :** Migrations de base de données, traitement batch, backups

---

## CronJobs : Tâches programmées

**Exécution de tâches sur une planification cron :**

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-db
spec:
  schedule: "0 2 * * *"  # Tous les jours à 2h du matin
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:13
            command:
            - /bin/bash
            - -c
            - pg_dump $DATABASE_URL > /backup/dump_$(date +%Y%m%d).sql
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: url
          restartPolicy: OnFailure
```

---

## Relations entre les ressources

**Architecture d'une application complète :**

```
Namespace
├── Deployment
│   └── ReplicaSet
│       └── Pods
├── Service (→ Pods via labels)
├── Ingress (→ Service)
├── ConfigMap (→ Pods)
├── Secret (→ Pods)
└── PVC (→ Pods)
    └── PV
```

> **Conseil :** Commencez simple puis ajoutez les ressources avancées

---

## Exemple d'application complète

**Déploiement WordPress avec MySQL :**

```bash
# 1. Namespace
kubectl create namespace wordpress

# 2. Secrets pour MySQL
kubectl create secret generic mysql-secret \
  --from-literal=password=motdepasse \
  -n wordpress

# 3. Déployer MySQL avec PVC
kubectl apply -f mysql-deployment.yaml -n wordpress

# 4. Déployer WordPress
kubectl apply -f wordpress-deployment.yaml -n wordpress

# 5. Exposer avec Ingress
kubectl apply -f wordpress-ingress.yaml -n wordpress
```

---


<!-- _class: lead -->

# TP 3 : Une application dans mon cluster

---

### Objectif du TP : Déployer une application web complète

**Objectif :** Mettre en pratique toutes les ressources vues
- Namespace, ConfigMap, Secret, PVC
- Deployments Redis et API 
- Services ClusterIP
- Ingress avec nom de domaine
- Job de test et CronJob de sauvegarde

Instructions détaillées dans `TP/module-3/instructions`

---

<!-- _class: lead -->

## Questions ?

*Prêts pour la gestion et les opérations ?*

![bg fit right:40%](binaries/kubernetes_small.png)

---

## Bibliographie

- [Kubernetes Official Documentation](https://kubernetes.io/docs/)
- [Kubernetes Patterns - Bilgin Ibryam & Roland Huß](https://www.redhat.com/en/engage/kubernetes-containers-architecture-s-201910240918)