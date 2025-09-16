# TP Module 6 - Corrigé : CNI avec Cilium et stockage persistant

## Commandes complètes et manifests

### Partie 1 : Déployer un cluster kind avec Cilium

#### 1.1 Configuration du cluster avec extraMounts

Fichier `kind-config.yaml` disponible à l'emplacement `TP/module-6/corrigé/kind-config.yaml`

#### 1.2 Créer le cluster

```bash
# Créer les répertoires de stockage local
mkdir -p /tmp/kind-data/{mysql,wordpress}

# Créer le cluster avec la configuration
kind create cluster --config=kind-config.yaml --name=cilium-lab

# Vérifier que les nodes sont en NotReady (CNI manquant)
kubectl --context kind-cilium-lab get nodes
NAME                       STATUS     ROLES           AGE     VERSION
cilium-lab-control-plane   NotReady   control-plane   2m14s   v1.33.1
cilium-lab-worker          NotReady   <none>          2m      v1.33.1
cilium-lab-worker2         NotReady   <none>          2m      v1.33.1
```

#### 1.3 Installer Cilium

```bash
# Télécharger le CLI Cilium (version Linux AMD64)
CILIUM_CLI_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt)
curl -L --fail --remote-name-all https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-amd64.tar.gz{,.sha256sum}
sha256sum --check cilium-linux-amd64.tar.gz.sha256sum
sudo tar xzvfC cilium-linux-amd64.tar.gz /usr/local/bin
rm cilium-linux-amd64.tar.gz{,.sha256sum}

# Installer Cilium dans le cluster kind
cilium install --set kubeProxyReplacement=true

# Vérifier l'installation
cilium status --wait

# Vérifier que les nodes sont maintenant Ready
kubectl --context kind-cilium-lab get nodes     
NAME                       STATUS   ROLES           AGE     VERSION
cilium-lab-control-plane   Ready    control-plane   9m4s    v1.33.1
cilium-lab-worker          Ready    <none>          8m50s   v1.33.1
cilium-lab-worker2         Ready    <none>          8m50s   v1.33.1

# Voir les pods Cilium
kubectl get pods -n kube-system | grep cilium
```

#### 1.4 Déployer l'ingress controller nginx

```bash
# Installer l'Ingress Controller NGINX pour kind
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Attendre que le déploiement soit prêt
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s

# Patcher le service pour fixer les ports NodePort
kubectl patch service ingress-nginx-controller -n ingress-nginx --type='json' \
  -p='[
    {"op": "replace", "path": "/spec/ports/0/nodePort", "value": 30080},
    {"op": "replace", "path": "/spec/ports/1/nodePort", "value": 30443}
  ]'

# Vérifier la configuration
kubectl get service ingress-nginx-controller -n ingress-nginx
```

**Résultat attendu :**
```
NAME                       TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)                      AGE
ingress-nginx-controller   LoadBalancer   10.xx.xx.xx     <pending>     80:30080/TCP,443:30443/TCP   38s
```

### Partie 2 : Configuration du stockage persistant

#### 2.1 & 2.2 Créer la StorageClass et les PersistentVolumes

Fichier `storage-config.yaml` disponible à l'emplacement `TP/module-6/corrigé/storage-config.yaml`

#### 2.3 Appliquer les manifests de stockage

```bash
# Appliquer la StorageClass et les PVs
kubectl apply -f storage-config.yaml

# Vérifier la storage class
kubectl get storageclass
NAME                 PROVISIONER                    RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
local-storage        kubernetes.io/no-provisioner   Retain          WaitForFirstConsumer   false                  45s
standard (default)   rancher.io/local-path          Delete          WaitForFirstConsumer   false                  10m


# Vérifier les PVs
kubectl get pv
NAME           CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM   STORAGECLASS    VOLUMEATTRIBUTESCLASS   REASON   AGE
mysql-pv       5Gi        RWO            Retain           Available           local-storage   <unset>                          45s
wordpress-pv   10Gi       RWO            Retain           Available           local-storage   <unset>                          45s


```

### Partie 3 : Déploiement de WordPress et MariaDB

#### 3.1 Créer le namespace et les secrets

```bash
# Créer le namespace
kubectl create namespace wordpress

# Créer le secret pour les mots de passe MySQL
kubectl create secret generic mysql-pass \
  --from-literal=password=verySecurePassword! \
  -n wordpress

# Vérifier la création du secret
kubectl get secret mysql-pass -n wordpress
```

#### 3.2 Déployer MariaDB

Fichier `mariadb.yaml` disponible à l'emplacement `TP/module-6/corrigé/mariadb.yaml`

#### 3.3 Déployer WordPress

Fichier `wordpress.yaml` disponible à l'emplacement `TP/module-6/corrigé/wordpress.yaml`

#### 3.4 Appliquer les manifests

```bash
# Déployer MariaDB
kubectl apply -f mariadb.yaml

# Attendre que MariaDB soit prêt
kubectl wait --for=condition=ready pod -l app=mariadb -n wordpress --timeout=120s

# Déployer WordPress
kubectl apply -f wordpress.yaml

# Vérifier les deployments
kubectl get all -n wordpress
kubectl get pvc -n wordpress
```

#### 3.5 Tester l'accès

```bash
# Redirection de port pour accéder à WordPress
kubectl port-forward service/wordpress 8080:80 -n wordpress &

# Dans un autre terminal, tester l'accès
curl -I http://localhost:8080

# Ou ajouter l'entrée dans /etc/hosts et utiliser l'Ingress
echo "127.0.0.1 wordpress.local" | sudo tee -a /etc/hosts
curl -I http://wordpress.local
```

### Partie 4 : Network Policies avec Cilium

#### 4.1, 4.2, 4.3 Network Policies complètes

Fichier `network-policies.yaml` disponible à l'emplacement `TP/module-6/corrigé/network-policies.yaml`

#### 4.4 Appliquer et tester les Network Policies

```bash
# Appliquer les Network Policies
kubectl apply -f network-policies.yaml

# Vérifier les Network Policies
kubectl get networkpolicy -n wordpress

# Tester la connectivité depuis WordPress vers MariaDB (doit marcher)
kubectl exec -it deployment/wordpress -n wordpress -- nc -zv mariadb 3306

# Tester depuis un pod non autorisé (doit échouer)
kubectl run test-pod --image=alpine --rm -it -n wordpress -- sh
# Dans le pod : nc -zv mariadb 3306
# Should timeout/fail

# Tester l'accès externe à WordPress (doit marcher)
curl -I http://localhost:8080
```

### Partie 5 : Observabilité avec Hubble

#### 5.1 Activer Hubble

```bash
# Activer Hubble pour l'observabilité réseau
cilium hubble enable --ui

# Vérifier que Hubble est déployé
kubectl get pods -n kube-system | grep hubble

# Attendre que tous les pods Hubble soient prêts
kubectl wait --for=condition=ready pod -l k8s-app=hubble-relay -n kube-system --timeout=120s
kubectl wait --for=condition=ready pod -l k8s-app=hubble-ui -n kube-system --timeout=120s
```

#### 5.2 Installer le CLI Hubble

```bash
# Télécharger et installer le CLI Hubble
export HUBBLE_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/hubble/master/stable.txt)
curl -L --fail --remote-name-all https://github.com/cilium/hubble/releases/download/$HUBBLE_VERSION/hubble-linux-amd64.tar.gz{,.sha256sum}
sha256sum --check hubble-linux-amd64.tar.gz.sha256sum
sudo tar xzf hubble-linux-amd64.tar.gz -C /usr/local/bin
rm hubble-linux-amd64.tar.gz{,.sha256sum}

# Vérifier l'installation
hubble version
```

#### 5.3 Observer le trafic réseau

Rien de particulier, on doit pouvoir visualiser les calls 80/443 vers world qui sont bloqués, ingress -> wordpress autorisé, wordpress -> mariadb autorisé.

### Partie 6 : Exploration des Custom Resources

#### 6.1 Explorer les CRDs de Cilium

```bash
# Lister toutes les Custom Resource Definitions de Cilium
kubectl get crd | grep cilium

# Examiner une CRD spécifique (CiliumNetworkPolicy)
kubectl describe crd ciliumnetworkpolicies.cilium.io

# Voir les instances de cette CRD
kubectl get ciliumnetworkpolicies -A

# Examiner une CiliumNetworkPolicy en détail
kubectl get ciliumnetworkpolicies -n wordpress -o yaml
```

#### 6.2 Créer une CiliumNetworkPolicy avancée

Fichier `cilium-l7-policy.yaml` disponible à l'emplacement `TP/module-6/corrigé/cilium-l7-policy.yaml`

**Objectif** : Remplacer la Network Policy standard par une CiliumNetworkPolicy avec des règles L7 pour l'accès Ingress Controller → WordPress.

Premièrement, supprimer la partie Ingress de la NetworkPolicy existante pour WordPress :

```bash
# Éditer la NetworkPolicy wordpress-ingress pour supprimer la partie ingress
kubectl patch networkpolicy wordpress-ingress -n wordpress --type='json' \
  -p='[{"op": "remove", "path": "/spec/ingress"}]'

# Ou recréer la NetworkPolicy sans la partie ingress
```

Vérifier que WordPress n'est plus accessible :

```bash
# Test d'accès - doit retourner 504 Gateway Time-out
curl -I http://wordpress.local
```

**Résultat attendu :**
```
HTTP/1.1 504 Gateway Time-out
```

Maintenant, créer la CiliumNetworkPolicy avec des règles L7 :

```yaml
# cilium-l7-policy.yaml
apiVersion: "cilium.io/v2"
kind: CiliumNetworkPolicy
metadata:
  name: wordpress-l7-policy
  namespace: wordpress
spec:
  endpointSelector:
    matchLabels:
      app: wordpress
  ingress:
  - fromEndpoints:
    - matchLabels:
        app.kubernetes.io/name: ingress-nginx
        app.kubernetes.io/component: controller
      matchExpressions:
      - key: k8s:io.kubernetes.pod.namespace
        operator: In
        values:
        - ingress-nginx
    toPorts:
    - ports:
      - port: "80"
        protocol: TCP
      rules:
        http:
        - method: "GET"
        - method: "POST"
        - method: "HEAD"
```

```bash
# Appliquer la CiliumNetworkPolicy
kubectl apply -f cilium-l7-policy.yaml

# Vérifier que la politique est bien créée
kubectl get ciliumnetworkpolicies -n wordpress

# Tester l'accès - doit maintenant fonctionner
curl -I http://wordpress.local
```

**Résultat attendu :**
```
HTTP/1.1 302 Found
...
x-redirect-by: WordPress
location: http://wordpress.local/wp-admin/install.php
...
```

**Vérification des règles L7 :**

```bash
# Tester une méthode autorisée (GET)
curl -IX GET http://wordpress.local
# HTTP/1.1 302 Found

# Tester une méthode non autorisée (DELETE) - doit être bloquée
curl -IX DELETE http://wordpress.local
# HTTP/1.1 403 Forbidden
```

Cette CiliumNetworkPolicy offre un contrôle plus granulaire que les Network Policies standard en permettant l'inspection au niveau L7 (HTTP) plutôt que seulement L3/L4.

#### 6.3 Explorer d'autres Custom Resources

```bash
# Explorer toutes les API resources de Cilium
kubectl api-resources --api-group=cilium.io

# Examiner les CiliumEndpoints (représentation des pods dans Cilium)
kubectl get ciliumendpoints -n wordpress

# Voir les détails d'un endpoint
ENDPOINT_NAME=$(kubectl get ciliumendpoints -n wordpress -o jsonpath='{.items[0].metadata.name}')
kubectl describe ciliumendpoint $ENDPOINT_NAME -n wordpress

# Explorer les CiliumNodes
kubectl get ciliumnodes

# Examiner la configuration réseau d'un node
kubectl describe ciliumnode cilium-lab-worker
```

### Partie 7 : Tests de persistance et nettoyage

#### 7.1 Tester la persistance des données

```bash
# Installer WP-CLI dans le pod WordPress pour créer du contenu
kubectl exec -it deployment/wordpress -n wordpress -- bash

# Dans le pod WordPress, installer wp-cli et créer du contenu
curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
chmod +x wp-cli.phar

# Créer un post (après avoir configuré WordPress via l'interface web)
./wp-cli.phar post create --post_title="Test Persistence" --post_content="Ce contenu doit persister après redémarrage" --allow-root --path=/var/www/html

# Sortir du pod
exit

# Supprimer et recréer le pod WordPress
kubectl delete pod -l app=wordpress -n wordpress

# Attendre la recreation
kubectl wait --for=condition=ready pod -l app=wordpress -n wordpress --timeout=120s

# Vérifier que les données persistent
kubectl port-forward service/wordpress 8080:80 -n wordpress &
curl http://localhost:8080 | grep "Test Persistence"
```

#### 7.2 Monitoring des volumes

```bash
# Vérifier l'utilisation des PVCs
kubectl get pvc -n wordpress

# Voir les détails du stockage
kubectl describe pv mysql-pv
kubectl describe pv wordpress-pv

# Examiner les montages dans les pods
kubectl exec -it deployment/mariadb -n wordpress -- df -h /var/lib/mysql
kubectl exec -it deployment/wordpress -n wordpress -- df -h /var/www/html

# Vérifier les données sur le node kind
docker exec -it cilium-lab-worker ls -la /mnt/data/mysql
docker exec -it cilium-lab-worker ls -la /mnt/data/wordpress
```
