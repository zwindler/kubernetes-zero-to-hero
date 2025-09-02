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

# Module 4 : Gestion du cycle de vie des applications

*Formation Kubernetes - Débutant à Avancé*

---

## Plan du Module 4

**Partie 1**
Health checks, gestion des ressources, types de containers

**Partie 2**
Métriques système, logs, utilisation de Prometheus/Grafana

**Partie 3**
HPA, VPA, outils de scaling avancés

**Partie 4**
Rolling updates, Blue/Green, Canary, Rollback

---

<!-- _class: lead -->

# Partie 1 : apps production-ready
## Préparer vos applications pour la production

---

<!-- _class: lead -->

# startup / liveness / readiness probes

---
## Pourquoi rajouter des sondes ?

**Sans sondes :**
- Le kubelet s'assure que le container est *vivant*, c'est à dire, que son processus principal est *vivant*

Mais *vivant* ne veut pas dire fonctionnel ! Ex :

- processus principal figé mais non fonctionnel
- serveur pas prêt à recevoir du trafic
- processus enfant nécessaire, mais mort


---

## Les différentes Probes de Kubernetes

Kubernetes ajoute un certain nombre de sondes (probes) visant à répondre à des questions diverses :

- **Startup Probe** : le container a-t-il fini de démarrer ?
- **Liveness Probe** : est ce que le container fonctionne réellement ?
- **Readiness Probe** : est ce que le container est prêt à recevoir du trafic ?

Ces startup / readiness / liveness probes sont gérées par **container**.

---

## Les différents types d'actions des **Probes**

[Probe (v1 core)](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.33/#probe-v1-core) est une des API de Kubernetes

Il existe 4 grands types de probes aujourd'hui :

- **HTTP** - la plus courante, effectue un call sur un serveur HTTP
- **TCP** - dans le cas où un call HTTP n'est pas possible
- **gRPC** - pour les serveurs gRPC
- **exec** - exécute une commande arbitraire sur le container quand celui ci ne contient pas de serveur

---

## Startup Probe : gérer les démarrages lents

Inhibe les autres sondes du container, jusqu'à ce que l'application soit démarrée.

**Cas d'usage :** apps avec un temps de démarrage long **et** variable.

Trivia : arrivées un peu après les autres (API `beta` en 1.18 / 2020)

---

## Startup Probe : exemple de manifest

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-startup
spec:
  containers:
  - name: slow-app
    image: myapp:1.0
    ports:
    - containerPort: 8080
    startupProbe:
      httpGet:
        path: /startup
        port: 8080
      periodSeconds: 10
      failureThreshold: 30  #<===== 30 * 10s = 5 minutes max                              
```

---

## Liveness Probe

Redémarre le conteneur si la sonde échoue

```yaml
  [...]
  containers:
  - name: web-app
    livenessProbe:
      httpGet:
        path: /health
        port: 80
      initialDelaySeconds: 30
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
```

---

## Readiness Probe

Retire le Pod du Service si la sonde échoue (sans le redémarrer)

```yaml
  [...]
  containers:
  - name: web-app
    image: myapp:1.0
    ports:
    - containerPort: 8080
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      periodSeconds: 5
      failureThreshold: 3
```

---

## Configuration des sondes : paramètres

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30    # Délai avant la première vérification
  periodSeconds: 10          # Fréquence des vérifications
  timeoutSeconds: 5          # Timeout par requête
  successThreshold: 1        # Succès consécutifs pour considérer OK
  failureThreshold: 3        # Échecs consécutifs pour considérer KO
```

---

## Exemple Python/Flask

```python
@app.route('/health')
def health():
    # Vérifications basiques (pas de dépendances externes)
    return {'status': 'healthy'}, 200

@app.route('/ready')
def ready():
    # Vérification 
    if database.pool_is_available:
        return {'status': 'ready'}, 200
    else:
        return {'status': 'not ready'}, 503

@app.route('/startup')
def startup():
    # Vérifications de démarrage (migrations, init)                                                    
    if app.is_initialized():
        return {'status': 'started'}, 200
    else:
        return {'status': 'starting'}, 503
```

---

## Types de probes : autre exemples

```yaml
# Probe TCP - ex: pour bases de données
# Probe gRPC (Kubernetes 1.23+)
livenessProbe:
  tcpSocket: #remplacer `tcpSocket:` par `grpc:` si on souhaite une sonde grpc        
    port: 5432
  initialDelaySeconds: 30
  periodSeconds: 10

# Probe exec - commande personnalisée
livenessProbe:
  exec:
    command:
    - /bin/sh
    - -c
    - "pg_isready -U postgres"
  initialDelaySeconds: 30
  periodSeconds: 10
```

---

<!-- _class: lead -->

# Gestion des ressources

---

## Requests et Limits

k8s est un orchestrateur de containers, **mais il a besoin d'aide** !

Dans nos manifests YAML, on va définir les besoins (requests) et les limites (limits) de nos containers.

```yaml
  [...]
  containers:
  - name: container1
    resources:
      requests:        # Ressources demandées (au scheduling)
        memory: "256Mi"
        cpu: "250m"
      limits:          # Limites maximales (imposées au runtime)                        
        memory: "512Mi"
        cpu: "500m"
```

---

## Unités des ressources (1/2)

**CPU (`cpu:`) :**
- `1` ou `1000m` = 1 coeur de CPU 
- `100m` = 1 dixième de coeur de CPU

**Mémoire (`memory:` ou `hugepages-<size>:`) :**
- `128Mi` = 128 * 1024 * 1024 bytes
- `128M` = 128 * 1000 * 1000 bytes

---

## Unités de ressources (2/2)

Plus anecdotique, la taille allouée aux modifications éphémères sur le FS du container `ephemeral-storage:` :

**Stockage éphémère :**
- `2Gi` = 2 * 1024³ bytes
- `1500M` = 1500 * 1000² bytes

---

## Quality of Service (QoS) (1/2)

Kubernetes classe les Pods selon leurs ressources CPU et mémoire.

En cas de pression sur la mémoire sur un Node, la QoS détermine dans quel ordre les Pods seront évincés du Node.

**Pods prioritaires pour QoS Guaranteed :**
- Applications critiques (bases de données, API principales)
- Services système essentiels (DNS, ingress controllers)
- Workloads sensibles aux variations de performance

---

## Quality of Service (QoS) (2/2)

**Guaranteed**
- **Tous** les conteneurs ont des requests et limits. Requests = limits.

**Burstable**
- Au moins un des conteneur a requests ou limits. Requests ≠ limits.

**BestEffort**
- Aucun requests ni limits défini

---

<!-- _class: lead -->

# Différents types de containers

---

## Init Containers

Conteneurs qui s'exécutent **avant** les conteneurs principaux.

Peuvent être utiles dans les cas où il est nécessaire de préparer l'environnement pour l'application : 

- changement des permissions sur un volume
- initialisation d'une base de données
- téléchargement de ressources externes
- ...

---

## Init containers : exemple de manifest

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-init
spec:
  initContainers:
  - name: config-setup
    image: busybox:1.37
    command: ['sh', '-c', 'cp /config-templates/* /shared-config/']                                         
    volumeMounts:
    - name: shared-config
      mountPath: /shared-config
  containers:
  - name: web-app
    image: myapp:1.0
    volumeMounts:
    - name: shared-config
      mountPath: /app/config
  volumes:
  - name: shared-config
    emptyDir: {}
```

---

## Sidecar Containers

Fonctionnalité "relativement récente" (`alpha` en 1.28, `stable` depuis Kubernetes v1.33) :
- init containers *spécial*, `restartPolicy: Always` qui subsistent après le démarrage du container principal.

Utiles pour certains proxy de DB externes (la connexion doit être disponible au boot de l'application principale).

⚠️ Ne pas confondre avec le *pattern* sidecar container (container qui étend les fonctionnalités d'un Pod pour du logging, monitoring...)

---


## Sidecar Containers : exemple de manifests

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: sidecar-cronjob
spec:
  schedule: "* * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: sidecar-user
            image: zwindler/sidecar-user
          initContainers:
          - name: slow-sidecar
            image: zwindler/slow-sidecar                                                                    
            restartPolicy: Always
          restartPolicy: Never
```

[blog.zwindler.fr - Kubernetes 1.29 - sidecar container](https://blog.zwindler.fr/2024/07/19/kubernetes-1-29-sidecar-containers/)

---

## Bonnes pratiques pour la production (1/2)

**Probes :**

- ✅ Toujours implémenter liveness ET readiness probes
- ✅ Endpoints légers et rapides (< 1s)
- ✅ Différencier `/health` (basique) et `/ready` (complet)
- ❌ Ne jamais vérifier les dépendances externes dans liveness (incidents en casquade)

---

## Bonnes pratiques pour la production (2/2)

**Limits et requests :**

- ✅ Toujours définir `requests` cpu et mémoire
  - cible = consommation moyenne / habituelle
- ✅ Toujours définir `limits` pour la **mémoire**
  - prévoir assez de marge pour les "bursts"
- ❌ Jamais de `limits` **cpu** pour les applications sensibles à la latence (cf [Stop Using CPU Limits on Kubernetes](https://home.robusta.dev/blog/stop-using-cpu-limits))
- QoS `Guaranteed` seulement pour les applications **très** critiques

---

<!-- _class: lead -->

# Partie 2 : Observabilité
## Surveiller et diagnostiquer vos applications

---

## Les 3 piliers de l'observabilité

L'observabilité moderne repose sur 3 types de télémétrie complémentaires :

- **📊 Métriques** : Données numériques agrégées dans le temps (CPU, RAM, compteurs...)
- **📝 Logs** : Messages textuels horodatés des applications et systèmes
- **🔍 Traces** : Suivi des requêtes à travers les microservices

---

## Métriques système avec metrics-server

Composant optionnel (mais courant) qui collecte les *métriques* de base CPU/Mémoire des Nodes et Pods

```bash
# Installation (si pas déjà présent)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Vérifier l'installation
kubectl get deployment metrics-server -n kube-system

# Voir les métriques des nœuds
kubectl top nodes

# Voir les métriques des pods
kubectl top pods
kubectl top pods --containers  # Par conteneur
kubectl top pods --sort-by=cpu
```

---

## Prometheus : collecteur de métriques

Historiquement les outils de collecte de *métriques* se répartissent entre 2 philosophies, **Push** (passif) vs **Pull** (actif)

Prometheus utilise majoritairement l'architecture **Pull** :

- **Service Discovery** automatique des ressources Kubernetes
- **Scraping** des métriques des applications
- **Stockage** local en time-series database
<br/>

**Alternatives :** [Thanos](https://thanos.io/), [Mimir](https://grafana.com/oss/mimir/), [VictoriaMetrics](https://victoriametrics.com/)

---

## Exporters

Pour collecter des métriques k8s, Prometheus utilise des **exporters**. Voici quelques exemples utiles :

- **[cadvisor](https://github.com/google/cadvisor)** : métriques des containers (CPU/RAM/réseau) - *intégré dans kubelet*
- **[kube-state-metrics](https://github.com/kubernetes/kube-state-metrics)** : état des objets K8s (pods, deployments...) 
- **[node-exporter](https://github.com/prometheus/node_exporter)** : métriques système des Nodes (disque, réseau, OS)
- **[enix/x509-certificate-exporter](https://github.com/enix/x509-certificate-exporter)** : exporter permettant de surveiller divers types de certificats dans le cluster

---

## Quelques métriques Kubernetes utiles dans Prometheus

- `up` : services qui répondent
- `kube_pod_status_phase` : états des pods
- `kube_deployment_status_replicas` : réplicas des deployments
- `container_memory_usage_bytes` : utilisation mémoire par container
- `container_cpu_usage_seconds_total` : utilisation CPU par container

---

## PromQL dans Prometheus (1/2)

On peut exécuter des requêtes PromQL directement depuis l'interface de Prometheus

```promql
# Pods en cours d'exécution
sum by (namespace) (kube_pod_status_phase{phase="Running"})

# Top 10 des pods qui consomment le plus de CPU
topk(10, rate(container_cpu_usage_seconds_total[5m]))

# Utilisation mémoire par namespace
sum by (namespace) (container_memory_usage_bytes{container!="POD"})

# Pods qui redémarrent
increase(kube_pod_container_status_restarts_total[1h]) > 0
```

---

## PromQL dans Prometheus (2/2)

TODO capture d'écran d'exemple

---

## Requêtes dans Grafana

TODO capture d'écran d'exemple bis

---

## Collecte de logs dans Kubernetes

Solutions d'agrégation de *logs* :

- **[Grafana Loki](https://grafana.com/oss/loki/)** : "Prometheus pour les logs"
- **[Elastic Stack](https://www.elastic.co/elastic-stack)** : Elasticsearch + Logstash + Kibana
- **[VictoriaLogs](https://docs.victoriametrics.com/victorialogs/)** : Performance optimisée
- **[Quickwit](https://quickwit.io/)** : Search engine moderne pour logs


**Pattern commun :** un agent sur chaque nœud collecte puis envoi vers stockage central → Interface de recherche

---

## Backends pour les traces distribuées


Suivre une requête utilisateur à travers tous les microservices (et les fonctions d'un même microservice) pour identifier les goulots d'étranglement.

Solutions de collecte de *traces* :

- **[Jaeger](https://www.jaegertracing.io/)** : CNCF graduated
- **[Zipkin](https://zipkin.io/)** : Historique, compatible avec Jaeger
- **[Tempo](https://grafana.com/oss/tempo/)** : Backend Grafana Labs pour les traces


---

## OpenTelemetry : le standard unifié

**OpenTelemetry** unifie la collecte des 3 types de télémétrie :

TODO je vais faire un schéma pour expliquer tout ça

Otel (abréviation usuelle) est le standard de facto, permet d'avoir SDK unique dans le code tout en offrant la flexibilité des backends de stockage.

Plus d'infos : [opentelemetry.io](https://opentelemetry.io/)

---

<!-- _class: lead -->

# Partie 3 : Scaling et optimisation
## Adapter automatiquement vos ressources

---

## Horizontal Pod Autoscaler (HPA)

Mise à l'échelle automatique du nombre de pods selon les métriques de base (consommation CPU / RAM des replicas)

Prérequis :
- **metrics-server** installé
- un Deployment avec `resources.requests` définis

---

## HPA : exemple de manifest

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: webapp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: webapp
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70                                                               
```

---

## HPA avec métriques *custom*

Au-delà des indicateurs basiques  CPU/RAM, HPA peut (en théorie) scaler sur **n'importe quelle métrique**, notamment Prometheus.

En pratique, ça demande un peu de configuration et un composant additionnel appelé [Prometheus Adapter](https://github.com/kubernetes-sigs/prometheus-adapter) et pas mal de configuration

<br/>

- [deezer.io - Optimizing Kubernetes resources with Horizontal Pod Autoscaling via Custom Metrics and the Prometheus Adapter](https://deezer.io/optimizing-kubernetes-resources-with-horizontal-pod-autoscaling-via-custom-metrics-and-the-a76c1a66ff1c)
- [blog.zwindler.fr - le même article, mais en français ;-P](https://blog.zwindler.fr/2024/10/11/optimisation-ressources-kubernetes-autoscaling-horizontal-custom-metrics-prometheus-adapter/)


---

## Vertical Pod Autoscaler (VPA)

Ajuste automatiquement et à la volée les requests/limits des conteneurs

Le VPA est disponibles dans plusieurs **Modes** :
- **Off** : Analyse uniquement, pas de modification
- **Recreation** : Supprime et recrée les pods avec nouvelles ressources
- **Auto** : Met à jour automatiquement (si possible sans interruption)

---

## VPA : exemple de manifest

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: webapp-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: webapp
  updatePolicy:
    updateMode: "Auto"        # Auto, Recreation, Off
  resourcePolicy:
    containerPolicies:
    - containerName: webapp
      maxAllowed:
        cpu: 1
        memory: 2Gi
      minAllowed:
        cpu: 100m
        memory: 128Mi
```

---

## HPA vs VPA : quand utiliser quoi ?

Horizontal Pod Autoscaler (HPA) :

- Applications stateless, avec charge variable dans le temps
- Peut scaler rapidement, mais pas de "scale-to-zero"

Vertical Pod Autoscaler (VPA) :

- Utile pour optimiser l'utilisation des ressources
- Peut nécessiter des redémarrages

**Dans la plupart des cas, on utilisera pas le VPA**

---

## Bonnes pratiques HPA / VPA

**HPA :**

- Éviter les oscillations : utiliser `scaleUpPolicy`/`ScaleDownPolicy`
- Utilisez des métriques custom (ex: requêtes/sec, taille des queues)
- ⚠️ Attention aux cold starts : `initialDelaySeconds` sur les probes

**VPA :**

- Mode `Off` d'abord pour analyser sans risque
- Définir `minAllowed`/`maxAllowed` pour éviter les extrêmes
- ❌ Ne **jamais** utiliser HPA + VPA sur la même ressource

---

## Outils de scaling avancés

**[KEDA](https://keda.sh/)** (Kubernetes Event-driven Autoscaling) :
- HPA améliorés : scale sur n'importe quelle métrique facilement
- Connecteurs pour Kafka, Redis, PostgreSQL, AWS SQS...
- Scale-to-zero pour économiser les ressources

**[KNative](https://knative.dev/)** (Kubernetes Native Serverless) :
- Platform serverless sur Kubernetes
- Auto-scaling agressif avec scale-to-zero
- *Request-driven scaling*

---

## Outils d'optimisation des ressources (1/2)

Les limits / requests sont dures à estimer à l'échelle. Pour éviter les crashs et les gaspillages : utiliser des outils du marché !

**[Goldilocks](https://goldilocks.docs.fairwinds.com/)** :
- Utilise les VPA pour faire des recommendations après une phase d'apprentissage, dans une interface web

---

## Outils d'optimisation des ressources (2/2)

**[KRR](https://github.com/robusta-dev/krr)** (Kubernetes Resource Recommender) :
- CLI pour analyser l'utilisation des ressources dans le temps
- Recommandations basées sur des métriques Prometheus


**[Kubecost](https://www.kubecost.com/)** :
- Analyse des coûts par namespace, workload, équipe
- Optimisation financière des ressources

---

<!-- _class: lead -->

# Partie 4 : Stratégies de mise à jour
## Déployer et mettre à jour en production

---

## Stratégies de déploiement Kubernetes

Plusieurs "pattern" usuels pour mettre à jour des apps dans k8s. 

Certains sont présents par défaut dans les Deployments, d'autres non.

- **RollingUpdate** : mise à jour progressive, sans interruption
- **Recreate** : arrêt complet puis redémarrage avec la nouvelle version
- **Blue/Green** : bascule complète entre deux environnements déployés en parallèle
- **Canary** : Test progressif sur un sous-ensemble de requêtes

---

## `RollingUpdate` : mise à jour progressive (1/2)

**Stratégie par défaut** des Deployments.

Remplace progressivement les anciens pods par les nouveaux.

Une fois que les nouveaux Pods sont ready, on passe aux suivants.

TODO ajouter un schéma

---

## `RollingUpdate` : mise à jour progressive (2/2)

maxUnavailable :
- Nombre/pourcentage de pods qui peuvent être indisponibles
- Plus élevé = mise à jour plus rapide, mais impact plus fort sur l'application

maxSurge :
- Nombre/pourcentage de pods supplémentaires autorisés
- Plus élevé = mise à jour plus rapide, mais plus de ressources

---

## `RollingUpdate` : exemple de manifest

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: "20%"    # Peut être un nombre ou un pourcentage
    maxSurge: "30%"          # Idem
```

Exemple avec 10 replicas => maxUnavailable=20%, maxSurge=30% :

- Minimum 8 pods disponibles (10 - 2 = 8)
- Maximum 13 pods au total (10 + 3 = 13)

---

## Stratégie `Recreate`

⚠️ **Interruption de service** mais évite les conflits de volumes RWO (ReadWriteOnce)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
spec:
  strategy:
    type: Recreate  # Pas de RollingUpdate possible dans ce cas                           
  template:
    spec:
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: webapp-data  # RWO volume
```


---

## Rappel : rollback et historique

Vu dans le module 3 - quelques commandes essentielles :

```bash
# Voir l'historique des déploiements
kubectl rollout history deployment/webapp

# Rollback vers la version précédente
kubectl rollout undo deployment/webapp

# Rollback vers une version spécifique
kubectl rollout undo deployment/webapp --to-revision=2
```

---

## Blue/Green Deployment

Ce pattern n'existe pas nativement dans Kubernetes.

Déploiement en parallèle de la version initiale (blue) une nouvelle version (green). Quand l'application (green) est prête, on bascule tout le trafic.

**Avantages :** bascule instantanée, rollback rapide  
**Inconvénients :** double consommation de ressources, manuel (sauf outil tiers)

---

## Blue/Green Deployment : exemple

```bash
# Déployer la nouvelle version Green en parallèle de Blue
kubectl apply -f webapp-green.yaml

# Modifier le service pour pointer vers Green
kubectl patch service webapp-service -p '{"spec":{"selector":{"version":"green"}}}'

# Supprimer l'ancienne version Blue
kubectl delete deployment webapp-blue
```

---

## Canary Deployment

Ce pattern n'existe pas nativement dans Kubernetes.

Déploiement progressif de la nouvelle version sur un sous-ensemble d'utilisateurs toujours plus grand.

**Avantages :** Réduction des risques, validation progressive  
**Inconvénients :** nécessite monitoring fiable, manuel (sauf outil tiers)

---

## Canary Deployment : exemple

```bash
# Déployer la nouvelle version "canary", sur le même Service
kubectl apply -f webapp-canary.yaml

# Augmenter progressivement le nombre de replicas "canary"
kubectl scale deployment webapp-canary --replicas=2
kubectl scale deployment webapp-stable --replicas=8

# Continuer la migration si les métriques sont OK
kubectl scale deployment webapp-canary --replicas=5
kubectl scale deployment webapp-stable --replicas=5

# Finaliser : version canary devient la version stable
kubectl delete deployment webapp-stable
```

---

## Outils avancés pour Canary

[Flagger](https://flagger.app/) (avec service mesh tiers) :
- Canary automatique basé sur des métriques
- Rollback automatique en cas d'anomalie
- Intégration avec service mesh

[Argo Rollouts](https://argoproj.github.io/argo-rollouts/) :
- CRD pour des stratégies de déploiement avancées
- Analysis basée sur Prometheus
- Intégration avec ingress controllers

---

<!-- _class: lead -->

# TP 4 : Déployer, surveiller et mettre à jour une application

---

## Objectif du TP : un app prête pour la production !

- Configurer health checks et ressources pour la production
- Mettre en place un HPA et tester le scaling
- Implémenter différentes stratégies de mise à jour
- Surveiller et déboguer les déploiements

*Instructions détaillées dans TP/module-4/*

---

<!-- _class: lead -->

## Questions ?

*Prêts pour la sécurité dans Kubernetes ?*

![bg fit right:40%](binaries/kubernetes_small.png)

---

## Bibliographie (1/3)

**Documentation officielle :**
- [Kubernetes Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [HPA Walkthrough](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/)
- [Deployment Rolling Updates](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-update-deployment)

---

## Bibliographie (2/3)

**Articles techniques :**
- [Prometheus Adapter - Deezer](https://deezer.io/optimizing-kubernetes-resources-with-horizontal-pod-autoscaling-via-custom-metrics-and-the-a76c1a66ff1c)
- [Sidecar Containers - blog.zwindler.fr](https://blog.zwindler.fr/2024/07/19/kubernetes-1-29-sidecar-containers/)
- [CPU Limits - Robusta](https://home.robusta.dev/blog/stop-using-cpu-limits)

---

## Bibliographie (3/3)

**Outils mentionnés :**
- [OpenTelemetry](https://opentelemetry.io/), [Prometheus](https://prometheus.io/), [Grafana](https://grafana.com/)
- [KEDA](https://keda.sh/), [KNative](https://knative.dev/), [Flagger](https://flagger.app/), [Argo Rollouts](https://argoproj.github.io/argo-rollouts/)