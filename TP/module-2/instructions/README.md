# TP 2 : Installer Kubernetes en local

## Objectif

Installer un cluster Kubernetes local pour pouvoir tester les concepts du cours et réaliser les exercices pratiques des modules suivants.

## Prérequis

- Docker (ou podman) installé et fonctionnel (voir TP 1)
- 4 Go de RAM disponibles minimum
- Connexion internet

## Solution recommandée : kind (Kubernetes in Docker)

**kind** est l'outil officiel Kubernetes pour créer des clusters de test locaux dans Docker. Il est :
- **Multi-plateforme** (Linux, macOS, Windows)
- **Léger et rapide** 
- **Officiel** (maintenu par l'équipe Kubernetes)
- **Gratuit** et open source

## Étape 1 : Installation de kind

### Linux
```bash
# Via curl
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.29.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Vérification
kind version
```

### macOS
```bash
# Via Homebrew (recommandé)
brew install kind

# ou via curl
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.29.0/kind-darwin-arm64 #ou amd64 si Intel
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Vérification
kind version
```

### Windows
```powershell
# Via Chocolatey
choco install kind

# Via curl (PowerShell)
curl.exe -Lo kind-windows-amd64.exe https://kind.sigs.k8s.io/dl/v0.29.0/kind-windows-amd64
Move-Item .\kind-windows-amd64.exe c:\some-dir-in-your-PATH\kind.exe

# Vérification
kind version
```

## Étape 2 : Installation de kubectl

**kubectl** est la CLI officielle pour interagir avec Kubernetes.

### Linux
```bash
ARCH=amd64

# Via curl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/${ARCH}/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Vérification
kubectl version --client
```

### macOS
```bash
# Via Homebrew (recommandé)
brew install kubectl

# Ou via curl
ARCH=arm64 #ou amd64 si Mac Intel
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/${ARCH}/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Vérification
kubectl version --client
```

### Windows
```powershell
# Via Chocolatey
choco install kubernetes-cli

# Via curl (PowerShell)
curl.exe -LO "https://dl.k8s.io/release/v1.33.3/bin/windows/amd64/kubectl.exe"
# Déplacer kubectl.exe dans votre PATH

# Vérification
kubectl version --client
```

## Étape 3 : Créer votre premier cluster Kubernetes

```bash
# Créer un cluster nommé "tp-kubernetes"
kind create cluster --name tp-kubernetes

# Vérifier que le cluster est créé
kind get clusters

# Configurer kubectl pour utiliser le cluster
kubectl cluster-info --context kind-tp-kubernetes
```

**Sortie attendue :**
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

## Étape 4 : Configuration de l'autocomplétion

L'autocomplétion kubectl vous fera gagner beaucoup de temps :

### bash
```bash
# Installer bash-completion si nécessaire sur MacOS
brew install bash-completion

# Ajouter à ~/.bashrc ou ~/.bash_profile
echo 'source <(kubectl completion bash)' >>~/.bashrc
source ~/.bashrc
```

### zsh
```bash
# Ajouter à ~/.zshrc
echo 'source <(kubectl completion zsh)' >>~/.zshrc
source ~/.zshrc
```

### Windows (PowerShell)
```powershell
kubectl completion powershell | Out-String | Invoke-Expression
```

## Étape 5 : Vérifications essentielles

### Vérifier l'état du cluster
```bash
# Informations générales du cluster
kubectl cluster-info

# Lister les nœuds
kubectl get nodes

# Vérifier les pods système
kubectl get pods -A
```

### Test rapide : déployer nginx
```bash
# Créer un pod nginx de test
kubectl run nginx-test --image=nginx:latest --port=80

# Vérifier que le pod démarre
kubectl get pods

# Vérifier les logs
kubectl logs nginx-test

# Nettoyer
kubectl delete pod nginx-test
```

## Étape 6 : Explorer les composants (optionnel)

```bash
# Voir les composants du control plane
kubectl get pods -n kube-system

# Examiner un pod en détail
kubectl describe pod -n kube-system $(kubectl get pods -n kube-system -o name | head -1)

# Voir les services système
kubectl get services -A
```

## Étape 7 : Cluster multi-nœuds (optionnel mais recommandé)

Pour une expérience plus proche de la production, créez un cluster avec plusieurs nœuds :

1. Supprimer le cluster actuel : `kind delete cluster --name tp-kubernetes`
2. Suivre le guide officiel : [Multi-node clusters avec kind](https://kind.sigs.k8s.io/docs/user/quick-start/#multi-node-clusters)
3. Vérifier avec `kubectl get nodes` que vous avez maintenant plusieurs nœuds

Cela vous permettra de mieux comprendre les concepts de scheduling et de répartition des charges.

## Alternatives selon votre environnement

### Docker Desktop (Windows/macOS)
Si vous préférez une solution avec interface graphique :
1. Installer [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Aller dans Settings → Kubernetes → Enable Kubernetes
3. Attendre que le statut devienne vert

### k3d (alternative légère)
```bash
# Installation
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash

# Créer un cluster
k3d cluster create mon-cluster

# Utilisation normale avec kubectl
kubectl get nodes
```

### Colima (macOS uniquement)
Alternative à Docker Desktop sur macOS :
```bash
# Installation
brew install colima

# Démarrer avec Kubernetes
colima start --kubernetes

# Utilisation normale avec kubectl
kubectl get nodes
```

## Résultat attendu

À la fin de ce TP, vous devez avoir :
- **kind** et **kubectl** installés
- Un cluster Kubernetes local fonctionnel
- La capacité de créer et supprimer des pods
- Une compréhension des composants de base

## Problèmes courants

### "Cannot connect to the Docker daemon"
- Vérifiez que Docker est démarré
- Sur Linux, ajoutez votre utilisateur au groupe `docker`

### "kubectl: command not found"
- Vérifiez que kubectl est dans votre PATH
- Relancez votre terminal après installation

### Cluster ne démarre pas
- Vérifiez que vous avez au moins 4 Go de RAM disponibles
- Redémarrez Docker si nécessaire

## Pour aller plus loin

- [Documentation officielle kind](https://kind.sigs.k8s.io/docs/)
- [Documentation officielle kubectl](https://kubernetes.io/docs/reference/kubectl/)
- **Module 3** : Nous utiliserons ce cluster pour découvrir les ressources Kubernetes !

---

**Bravo !** Vous avez maintenant votre propre cluster Kubernetes

Vous êtes prêts pour explorer les ressources de base dans le Module 3 !
