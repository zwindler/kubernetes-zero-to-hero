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

table {
  font-size: 30px;
}

ul {
  margin-top: 17px;
  margin-bottom: 17px;
}
</style>

<!-- _class: lead -->

# Module 7 : Helm et Kustomize
## Industrialisation des déploiements

*Formation Kubernetes - Débutant à Avancé*

---

## Plan du Module 7

**Introduction**
- Pourquoi industrialiser les déploiements ?
- Vue d'ensemble Helm vs Kustomize

**Partie 1 : Helm - Package Manager**
- Concepts et architecture (Helm 3 et Helm 4)
- Utilisation des charts existants
- Création de charts custom
- Gestion des releases et sécurité

---

## Plan du Module 7 (suite)

**Partie 2 : Kustomize - Customisation native**
- Philosophie et principes
- Structure et overlays
- Patches et transformations
- Générateurs

**Conclusion**

---

<!-- _class: lead -->

# Introduction

---

## Pourquoi industrialiser les déploiements ?

**Problèmes avec le YAML "brut" :**
- **Duplication** : Même configuration dans plusieurs environnements
- **Maintenance** : Changements difficiles à propager sans erreur
- **Erreurs** : Copier-coller et modifications manuelles
- **Versioning** : Pas de gestion des versions des déploiements native
- **Rollback** : Difficile de revenir en arrière

> Il faut des outils pour **packager**, **versionner** et **customiser** nos applications

---

## Vue d'ensemble Helm vs Kustomize

| Aspect | Helm | Kustomize |
|--------|------|-----------|
| **Approche** | Template + Values | Application de patches sur une base de code YAML |
| **Complexité** | Réputé plus complexe | Réputé plus simple |
| **Écosystème** | Charts publics riches | Intégré à kubectl |
| **Templating** | Go templates | Pas de templating |
| **Versionning** | Releases versionnées | Pas natif, via git/tags |

---

<!-- _class: lead -->

# Partie 1 : Helm - Package Manager

---

## Helm : Concepts

**Helm = "Package Manager" pour Kubernetes**

- **Chart** : Package d'une application (templates + métadonnées)
- **Release** : Instance déployée d'un chart
- **Repository** : Stockage de charts versionnés
- **Values** : Configuration personnalisée

```bash
# Exemple d'utilisation basique
helm install my-nginx nginx --set service.type=LoadBalancer
```

![bg fit right:25%](binaries/helm.svg)

---

## Évolution : Helm 3 et Helm 4

**Helm 3 (version stable actuelle) :**
- Suppression de Tiller (composant "serveur dans Helm 2)
- Stockage des releases dans Kubernetes
- Support natif des CRDs
- Hooks de cycle de vie

**Helm 4 (en développement) :**
- Meilleur support OCI (registries)
- Simplification de l'API

---

## Architecture Helm 3

```
┌─────────────────┐    ┌─────────────────┐
│   Helm Client   │───>│  Kubernetes API │
│     (CLI)       │    │     Server      │
└─────────────────┘    └─────────────────┘
         │                      │
         ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│   Chart Repo    │    │   Release Data  │
│ (artifacthub.io)│    │     (Secret)    │
└─────────────────┘    └─────────────────┘
```

---

## Utilisation de `helm`

```bash
# Ajouter un repository
helm repo add traefik https://traefik.github.io/charts
helm repo update

# Installer une application
helm install traefik traefik/traefik

# via OCI
helm install traefik oci://ghcr.io/traefik/helm/traefik

# Lister les releases
helm list
```

---

## Exemple : Installer Traefik

```bash
# Voir les valeurs configurables
helm show values traefik/traefik

# Installer avec configuration custom
helm install traefik traefik/traefik \
  --set service.type=LoadBalancer \
  --set deployment.replicas=2 \
  --create-namespace --namespace traefik

# Vérifier le déploiement
helm status traefik -n traefik
kubectl get pods -n traefik
```

---

## Structure d'un chart

```
my-app/
├── Chart.yaml          # Métadonnées du chart
├── values.yaml         # Valeurs par défaut
├── templates/          # Templates Kubernetes
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── _helpers.tpl    # Fonctions helper
│   └── NOTES.txt       # Instructions post-install
└── charts/             # Dépendances (optionnel)
```

```bash
# Créer un nouveau chart
helm create my-app
```

---

## Chart.yaml : Métadonnées

```yaml
apiVersion: v2
name: my-webapp
description: A Helm chart for my web application
type: application
version: 0.1.0          # Version du chart
appVersion: "1.0.0"     # Version de l'application sous-jacente                    

dependencies:
- name: x509-certificate-exporter
  version: "3.19.1"
  repository: https://charts.enix.io
  condition: x509.enabled

maintainers:
- name: Denis Germain
  email: denis@example.com
```

---

## Extrait d'un fichier values.yaml

```yaml
deployment:
  enabled: true
  kind: Deployment
  replicas: 3
  terminationGracePeriodSeconds: 60
  minReadySeconds: 0
```

---

## Templates : xxx.yaml

Les manifests YAML *templatisés*

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "my-webapp.fullname" . }}
  labels:
    {{- include "my-webapp.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "my-webapp.selectorLabels" . | nindent 6 }}
...
```

---

## Templates : _helpers.tpl

Des fonctions utiles pour factoriser du code courant (labels, noms...)

```yaml
{{/* Expand the name of the chart. */}}
{{- define "my-webapp.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Common labels */}}
{{- define "my-webapp.labels" -}}
helm.sh/chart: {{ include "my-webapp.chart" . }}
{{ include "my-webapp.selectorLabels" . }}
app.kubernetes.io/version: {{ .Values.image.tag | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
```

---

## Helm : gestion des releases

```bash
helm install my-release ./my-app
helm upgrade my-release ./my-app --set replicaCount=3

helm history my-release
helm rollback my-release 1

helm uninstall my-release
```

<br/>
<br/>

**Note :** chaque opération (sauf uninstall) crée une nouvelle révision versionnée

---

## Sécurité avec Helm

**Bonnes pratiques :**

```bash
# Valider avant déploiement
helm lint ./my-chart
helm template my-release ./my-chart --debug

# Utiliser des namespaces dédiés
helm install my-app ./my-chart --namespace production --create-namespace

# Il est possible de signer les charts avec une clé PGP
helm package --sign --key mykey ./my-chart
helm verify my-chart-0.1.0.tgz
```

---

## Test via `helm test my-release`

```bash
# Templates dans templates/tests/
# test-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: "{{ include "my-webapp.fullname" . }}-test"
  annotations:
    "helm.sh/hook": test
spec:
  restartPolicy: Never
  containers:
  - name: wget
    image: busybox
    command: ['wget']
    args: ['{{ include "my-webapp.fullname" . }}:{{ .Values.service.port }}']
```

---

<!-- _class: lead -->

# Partie 2 : Kustomize - Customisation native

---

## Kustomize : Philosophie et principes

**"Configuration Management without Templates"**

- **Base** : Configuration de référence (YAML brut)
- **Overlays** : Personnalisations par environnement
- **Patches** : Modifications ciblées
- **Pas de templating** : Juste du YAML valide

> Intégré nativement dans kubectl depuis la v1.14

```bash
kubectl apply -k ./my-app/overlays/production
```

---

## Avantages de Kustomize

**Simplicité :**
- Pas de nouveau langage de templating à apprendre
- YAML reste toujours valide et testable
- Composition par patches plutôt que par templates

**Intégration :**
- Natif dans kubectl (`-k` flag)
- Support GitOps excellent (ArgoCD, Flux, cf module 8)
- Debugging plus simple (voir le YAML final)

---

## Structure d'un projet Kustomize typique

```
my-app/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   └── kustomization.yaml
└── overlays/
    ├── development/
    │   ├── kustomization.yaml                                                       
    │   └── patches/
    ├── staging/
    │   ├── kustomization.yaml
    │   └── replica-patch.yaml
    └── production/
        ├── kustomization.yaml
        ├── ingress.yaml
        └── patches/
```

---

## Base : Configuration de référence

```yaml
# base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: app
        image: nginx:1.29
        ports:
        - containerPort: 80
```

---

## Base : kustomization.yaml

```yaml
# base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1                                                  
kind: Kustomization

metadata:
  name: my-app-base

resources:
- deployment.yaml
- service.yaml
- configmap.yaml

commonLabels:
  app: my-app
  version: v1.0.0

commonAnnotations:
  managed-by: kustomize
```

---

## Overlay : Environnement de production

```yaml
# overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1                                               
kind: Kustomization
metadata:
  name: my-app-production
resources:
- ../../base
- ingress.yaml
namePrefix: prod-
nameSuffix: -v1
replicas:
- name: my-app
  count: 3
images:
- name: nginx
  newTag: 1.29-alpine
patches:
- replica-patch.yaml
```

---

## Patches : **Strategic Merge Patch**
```yaml
# overlays/production/replica-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 5
  template:
    spec:
      containers:
      - name: app
        resources:
          limits:
            cpu: 500m
            memory: 512Mi
```

---

## Patches : **JSON 6902**

```yaml
# overlays/production/kustomization.yaml                                              
patchesJson6902:
- target:
    version: v1
    kind: Deployment
    name: my-app
  path: cpu-limit-patch.yaml
```

```yaml
# cpu-limit-patch.yaml
- op: replace
  path: /spec/template/spec/containers/0/resources/limits/cpu                              
  value: 1000m
- op: add
  path: /spec/template/spec/containers/0/env
  value:
  - name: ENV
    value: production
```

---

## Générateurs : ConfigMaps et Secrets

```yaml
# kustomization.yaml
configMapGenerator:
- name: app-config
  files:
  - config.properties
  - database.conf
- name: app-env
  literals:
  - DATABASE_URL=postgres://prod-db:5432/myapp                                                         
secretGenerator:
- name: app-secrets
  files:
  - secret.key
  - .env
- name: db-secret
  literals:
  - password=secretpassword
```

Noms automatiquement hashés pour forcer les redéploiements

---

## Transformers Kustomize

Facilite la réalisation d'actions plus complexes

**Transformers courants :**
- **PrefixSuffixTransformer** : Ajouter préfixes/suffixes aux noms
- **NamespaceTransformer** : Changer le namespace des ressources
- **LabelTransformer** : Ajouter des labels à toutes les ressources
- **AnnotationTransformer** : Ajouter des annotations
- **ImageTransformer** : Modifier les images des conteneurs

[Documentation complète des transformers](https://kubectl.docs.kubernetes.io/references/kustomize/builtins/)

---

## Exemple de transformers

```yaml
# kustomization.yaml
transformers:
- |-
  apiVersion: builtin
  kind: PrefixSuffixTransformer
  metadata:
    name: myPrefixSuffix
  prefix: dev-
  suffix: -v2
  
- |-
  apiVersion: builtin
  kind: NamespaceTransformer
  metadata:
    name: myNamespace
  namespace: my-namespace                                                        
```

---

## Utilisation avec kubectl

```bash
# Voir le YAML généré
kubectl kustomize overlays/production

# Appliquer directement
kubectl apply -k overlays/production

# Différences
kubectl diff -k overlays/production

# Supprimer
kubectl delete -k overlays/production
```

**Le flag `-k` active Kustomize dans kubectl**

---

<!-- _class: lead -->

# Conclusion

---

## Helm vs Kustomize : Forces et faiblesses

| Critère | Helm ✅❌ | Kustomize ✅❌ |
|---------|-----------|----------------|
| **Écosystème** | ✅ Charts publics riches | ❌ Pas de repository central |
| **Courbe apprentissage** | ❌ Go templates complexes | ✅ Juste du YAML |
| **Templating** | ✅ Très flexible | ❌ Limité aux patches |
| **Versioning** | ✅ Releases versionnées | ❌ Dépend de Git |
| **Rollback** | ✅ Natif et simple | ❌ Manual via Git |
| **Debugging** | ❌ Templates difficiles | ✅ YAML toujours valide |


---

## Bonnes pratiques communes

**Peu importe l'outil choisi :**

- **Versioning** : Git tags + versions sémantiques
- **Structure** : Séparer base/environnements
- **Tests** : Validation des manifests générés
- **Documentation** : README avec exemples d'usage
- **Sécurité** : Secrets externalisés, pas de credentials en dur
- **CI/CD** : Pipeline automatisé de validation/déploiement

---

<!-- _class: lead -->

# TP 7 : Déployer une application avec Helm et Kustomize

---

## Objectif du TP : comparer les deux approches

**Partie 1 : Helm**
- Créer un chart custom pour notre application
- Gérer les releases et faire un rollback

**Partie 2 : Kustomize**
- Créer une structure base + overlays
- Utiliser les générateurs et patches
- Déployer sur différents environnements

*Instructions détaillées dans TP/module-7/*

---

<!-- _class: lead -->

## Questions ?

*Prêts pour GitOps et Argo CD ?*

![bg fit right:40%](binaries/kubernetes_small.png)

---

## Bibliographie (1/2)

**Documentation officielle :**
- [Helm Documentation](https://helm.sh/docs/)
- [Kustomize Documentation](https://kustomize.io/)
- [Kubectl Kustomize](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/)

**Charts et repositories :**
- [Artifact Hub](https://artifacthub.io/)
- [Kubernetes Charts](https://github.com/kubernetes/charts)
- [Prometheus Community Charts](https://github.com/prometheus-community/helm-charts)

---

## Bibliographie (2/2)

**Bonnes pratiques :**
- [Helm Best Practices](https://helm.sh/docs/chart_best_practices/)
- [Kustomize Best Practices](https://kubectl.docs.kubernetes.io/guides/config_management/introduction/)
- [GitOps Principles](https://opengitops.dev/)

**Outils complémentaires :**
- [Helmfile](https://github.com/helmfile/helmfile) : Helm + GitOps
- [Skaffold](https://skaffold.dev/) : Workflow de développement
- [Tilt](https://tilt.dev/) : Environnement de développement local