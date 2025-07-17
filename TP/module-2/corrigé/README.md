# TP 2 - Corrigé : Installer Kubernetes en local

## Commandes complètes d'installation et test

### Installation kind + kubectl (macOS avec Homebrew)
```bash
# Installation des outils
brew install kind kubectl

# Vérification des versions
kind version
kubectl version --client
```

### Création et test du cluster
```bash
# Créer le cluster
kind create cluster --name tp-kubernetes

# Vérifier la création
kind get clusters
kubectl cluster-info --context kind-tp-kubernetes

# Test des nœuds
kubectl get nodes

# Test avec un pod nginx
kubectl run nginx-test --image=nginx:latest --port=80
kubectl get pods
kubectl logs nginx-test

# Nettoyage du test
kubectl delete pod nginx-test
```

### Sortie attendue

#### Création du cluster
```
Creating cluster "tp-kubernetes" ...
 ✓ Ensuring node image (kindest/node:v1.32.2) 🖼 
 ✓ Preparing nodes 📦  
 ✓ Writing configuration 📜 
 ✓ Starting control-plane 🕹️ 
 ✓ Installing CNI 🔌 
 ✓ Installing StorageClass 💾 
Set kubectl context to "kind-tp-kubernetes"
You can now use your cluster with:

kubectl cluster-info --context kind-tp-kubernetes

Thanks for using kind! 😊
```

#### Informations du cluster
```bash
$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:55199
CoreDNS is running at https://127.0.0.1:55199/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
```

#### Liste des nœuds
```bash
$ kubectl get nodes
NAME                          STATUS   ROLES           AGE     VERSION
tp-kubernetes-control-plane   Ready    control-plane   9m52s   v1.32.2
```

#### Pods système
```bash
$ kubectl get pods -A
NAMESPACE            NAME                                                  READY   STATUS    RESTARTS   AGE
kube-system          coredns-668d6bf9bc-4bj6v                              1/1     Running   0          6m12s
kube-system          coredns-668d6bf9bc-d74lk                              1/1     Running   0          6m12s
kube-system          etcd-tp-kubernetes-control-plane                      1/1     Running   0          6m19s
kube-system          kindnet-lfrql                                         1/1     Running   0          6m12s
kube-system          kube-apiserver-tp-kubernetes-control-plane            1/1     Running   0          6m19s
kube-system          kube-controller-manager-tp-kubernetes-control-plane   1/1     Running   0          6m19s
kube-system          kube-proxy-r8pvr                                      1/1     Running   0          6m12s
kube-system          kube-scheduler-tp-kubernetes-control-plane            1/1     Running   0          6m19s
local-path-storage   local-path-provisioner-7dc846544d-mh54k               1/1     Running   0          6m12s

```

### Configuration de l'autocomplétion
```bash
# macOS avec zsh (exemple)
echo 'source <(kubectl completion zsh)' >>~/.zshrc
source ~/.zshrc

# Test de l'autocomplétion
kubectl get po<TAB>  # Doit compléter "pods"
```

## Vérifications de sécurité

```bash
# S'assurer qu'on est sur le bon contexte
kubectl config current-context

# Vérifier qu'on ne peut pas accéder aux ressources sensibles
kubectl get secrets -A  # Doit lister seulement les secrets système
```

## Ressources consommées

- **RAM** : ~1 Go pour le cluster kind
- **CPU** : ~0.5 core en idle
- **Disque** : ~500 Mo pour l'image kindest/node
- **Réseau** : Port local aléatoire (ex: 64832)

## Configuration avancée

### Cluster multi-nœuds (recommandé)
```yaml
# kind-config-multi-node.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
```

```bash
# Supprimer l'ancien cluster
kind delete cluster --name tp-kubernetes

# Créer avec la config multi-nœuds
kind create cluster --name tp-kubernetes --config kind-config-multi-node.yaml

# Vérifier les nœuds
kubectl get nodes
```

**Sortie attendue :**
```bash
$ kubectl get nodes
NAME                          STATUS   ROLES           AGE   VERSION
tp-kubernetes-control-plane   Ready    control-plane   26s   v1.32.2
tp-kubernetes-worker          Ready    <none>          16s   v1.32.2
tp-kubernetes-worker2         Ready    <none>          17s   v1.32.2
```
