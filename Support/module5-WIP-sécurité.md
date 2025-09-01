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

# Module 5 : Sécurité dans Kubernetes

*Formation Kubernetes - Débutant à Avancé*

---

## Plan du Module 5

**Partie 1 : Contrôle d'accès (RBAC)**
- Ressources RBAC
- Tooling d'audit du RBAC

**Partie 2 : Security Context**
- Configuration sécurisée des Pods
- Capabilities, utilisateurs, filesystem

**Partie 3 : Politiques de sécurité**
- Admission control et webhooks
- Politiques Kyverno, détection de menaces

**Partie 4 : Bonnes pratiques**
- Container security, cluster hardening

---

<!-- _class: lead -->

# Partie 1 : Contrôle d'accès (RBAC)

---

## Introduction au RBAC : principes généraux

**Role-Based Access Control** : contrôle d'accès basé sur les rôles

Dans Kubernetes, **tout est API** :
- Créer un Pod → `POST /api/v1/namespaces/default/pods`  
- Lister les Services → `GET /api/v1/services`
- Supprimer un Deployment → `DELETE /apis/apps/v1/deployments/nginx`

**RBAC** définit **qui** peut faire **quoi** sur **quelles ressources**.

---

## Users, Groups, ServiceAccounts

**Users** : Humains (développeurs, ops, admins)
- Gérés **en dehors** de Kubernetes (OIDC, certificats, LDAP...)
- mais pas d'objet `User` dans l'API

**Groups** : Groupes d'utilisateurs (ex. `system:masters`, `developer-team`)

**ServiceAccounts** : Identités pour les applications
- Utilisés par les Pods pour accéder à l'API
- Un par namespace par défaut (`default`)

---

## Roles

**Role** : permissions **dans** un **namespace**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
```

---

## ClusterRoles

**ClusterRole** : permissions à l'échelle du **cluster**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cluster-reader
rules:
- apiGroups: [""]
  resources: ["nodes", "namespaces"]  
  verbs: ["get", "list"]
```

---

## RoleBindings

Lie un Role à des sujets dans un namespace

```yaml
apiVersion: rbac.authorization.k8s.io/v1                                              
kind: RoleBinding
metadata:
  name: developers-pods
  namespace: production
subjects:
- kind: ServiceAccount
  name: deployment-sa
  namespace: production
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

---

## ClusterRoleBinding

Pareil mais pour un ClusterRole

```yaml
apiVersion: rbac.authorization.k8s.io/v1                                                  
kind: ClusterRoleBinding
metadata:
  name: cluster-admins
subjects:
- kind: User
  name: admin
  apiGroup: rbac.authorization.k8s.io
- kind: Group
  name: system:masters
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
```

---

## Tooling d'audit du RBAC

**Vérifier les permissions :**
```bash
# Vérifier si un utilisateur peut faire une action
kubectl auth can-i create pods --as=alice
kubectl auth can-i get secrets --as=system:serviceaccount:default:my-sa

# Lister toutes les permissions d'un utilisateur
kubectl auth can-i --list --as=alice

# Voir les permissions dans un namespace
kubectl auth can-i --list --as=alice -n production
```

---

## Quelques autres outils d'audit

TODO: ajouter des liens vers les tools

- `kubectl who-can` (plugin)
- `rbac-lookup` 
- `kubectl rbac-tool`

---

<!-- _class: lead -->

# Partie 2: Security Context

---

## Security Context : Configuration sécurisée des Pods

Le **Security Context** définit les privilèges et contrôles d'accès pour un Pod ou Container.

Ces Security Contexts peuvent être définis à 2 niveaux :

* pod (pour tous les containers du pod)
* container

---

## Security Context au niveau du Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: security-context-demo
spec:
  securityContext:
    <paramètres de sécurité>
  [...]
  containers:
  - name: sec-ctx-demo
    image: busybox:1.28
    command: [ "sh", "-c", "sleep 1h" ]
```

---

## Security Context au niveau du container

Info : le **Container-level** a la priorité sur **Pod-level** :

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: security-context-demo-2
spec:
  securityContext:
    runAsUser: 1000
  containers:
  - name: sec-ctx-demo-2
    image: busybox:1.28
    command: [ "sh", "-c", "sleep 1h" ]
    securityContext:
      <paramètres de sécurité>      # Priorité sur Pod-level                       
```

---

## Quelques concepts de base

- **runAsUser**: UID du processus principal
- **runAsGroup**: GID principal du processus
- **fsGroup**: GID propriétaire des volumes
- **privileged**: Accès complet au système hôte (dangereux !)
- **allowPrivilegeEscalation**: Permet l'escalade de privilèges
- **readOnlyRootFilesystem**: Système de fichiers racine en lecture seule
- **runAsNonRoot**: Force l'exécution avec un utilisateur non-root

---

### Capabilities
Contrôle fin des privilèges système : les capabilities Linux permettent de donner des permissions spécifiques sans donner tous les droits root.

```yaml
securityContext:
  capabilities:
    add: ["NET_ADMIN", "SYS_TIME"]
    drop: ["ALL"]
```

---

## Security context : exemple avec nginx

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-insecure
spec:
  containers:
  - name: nginx
    image: nginx:1.30
    ports:
    - containerPort: 80
```

---

## Security context : exemple **sécurisé**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-secure
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1001
    fsGroup: 1001
  containers:
  - name: nginx
    image: nginx:1.30
    ports:
    - containerPort: 8080  # Port non-privilégié
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]         
```

---

## SELinux

Système de contrôle d'accès obligatoire (MAC) au niveau kernel
```yaml
securityContext:
  seLinuxOptions:
    level: "s0:c123,c456"
    type: "container_t"
    user: "system_u"
    role: "system_r"
```

---


## AppArmor profiles

Système de sécurité par profils pour confiner les applications

```yaml
metadata:
  annotations:
    container.apparmor.security.beta.kubernetes.io/container-name: runtime/default
spec:
  containers:
  - name: container-name
    # ...
```

---

## Paramètres Sysctl

Configuration des paramètres du kernel Linux pour le Pod. Tous les paramètres ne sont pas considérés "safe" :

```yaml
spec:
  securityContext:
    sysctls:
    - name: kernel.shm_rmid_forced # safe
      value: "0"
    - name: net.core.somaxconn # unsafe!
      value: "1024"
```

[Plus d'infos dans la doc officielle kubernetes.io/docs/tasks/administer-cluster/sysctl-cluster](https://kubernetes.io/docs/tasks/administer-cluster/sysctl-cluster/) 

---

## Vérification des UID/GID

```bash
# Dans le container non-sécurisé (nginx-insecure)
kubectl exec -it nginx-insecure -- id
# uid=0(root) gid=0(root) groups=0(root)

kubectl exec -it nginx-insecure -- ps aux
# USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
# root         1  0.0  0.0  11528  7396 ?        Ss   10:30   0:00 nginx: master process

# Dans le container sécurisé (nginx-secure)
kubectl exec -it nginx-secure -- id
# uid=1001 gid=1001 groups=1001

kubectl exec -it nginx-secure -- ps aux
# USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
# 1001         1  0.0  0.0  11528  7396 ?        Ss   10:30   0:00 nginx: master process      
```

---

## Test des capabilities (1/2)

```bash
# Test de ping (nécessite CAP_NET_RAW)
kubectl exec -it nginx-insecure -- ping -c 1 8.8.8.8
# PING 8.8.8.8 (8.8.8.8): 56 data bytes
# 64 bytes from 8.8.8.8: icmp_seq=0 ttl=113 time=15.123 ms ✅

kubectl exec -it nginx-secure -- ping -c 1 8.8.8.8
# ping: socket: Operation not permitted ❌
```

---

## Test des capabilities (2/2)

```bash
# Test lecture seule du filesystem
kubectl exec -it nginx-insecure -- touch /test-file
# (Réussit) ✅

kubectl exec -it nginx-secure -- touch /test-file
# touch: /test-file: Read-only file system ❌

# Test des capabilities disponibles
kubectl exec -it nginx-insecure -- cat /proc/1/status | grep Cap
kubectl exec -it nginx-secure -- cat /proc/1/status | grep Cap
# (Le Pod sécurisé aura beaucoup moins de capabilities)
```

---

TODO ajouter une slide ou deux sur la feature UserNamespace

---

<!-- _class: lead -->

# Partie 3: Admission Control

---

## C'est quoi l'admission control ?

Mécanisme qui intercepte les requêtes à l'API Server après l'authentification et l'autorisation, mais **avant** la persistance des objets.
![center width:1100](binaries/admission_control.jpeg)

*source : [Kubernetes admission controllers in 5 minutes](https://www.sysdig.com/blog/kubernetes-admission-controllers)*

---

## Types d'admission controllers

1. **Validating Admission Controllers** : Valident les requêtes
2. **Mutating Admission Controllers** : Modifient les requêtes
3. **Admission Webhooks** : Controllers personnalisés

---

## Admission Controllers natifs

Exemples d'admission controllers intégrés :
- **NodeRestriction** : Limite les permissions des kubelets
- **ResourceQuota** : Applique les quotas de ressources
- **LimitRanger** : Applique les limites par défaut
- **PodSecurityPolicy** : ⚠️ Déprécié en v1.25

<br/>

[kubernetes.io - liste des controllers disponibles](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)

---

## Etendre les possibilités

Il existe plusieurs façon d'étendre l'admission control dans Kubernetes

* développer soi même un webhook
* utiliser un outil comme Kyverno ou OPA/Gatekeeper
* **CEL** (Common Expression Language)!

---

## CEL : Common Expression Language

**"Nouveauté" Kubernetes native** (alpha 1.26) pour définir des politiques d'admission sans webhook externe !

* **Validating Admission Policy** 🟢 Stable (v1.30)
* **Mutating Admission Policy** 🔶 Beta (v1.34)

**Avantages :**
- Intégré nativement dans Kubernetes
- Pas besoin de webhook externe
- Syntaxe simple

---

## CEL : exemple Validating Admission Policy

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: "require-non-root"
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
    - operations: ["CREATE", "UPDATE"]
      apiGroups: [""]
      apiVersions: ["v1"]
      resources: ["pods"]
  validations:
  - expression: "object.spec.securityContext.runAsNonRoot == true"
    message: "Pod must run as non-root user"
  - expression: "object.spec.containers.all(c, c.securityContext.allowPrivilegeEscalation == false)"
    message: "Containers must not allow privilege escalation"
```

---

## CEL : Binding de la politique

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata:
  name: "require-non-root-binding"
spec:
  policyName: "require-non-root"
  validationActions: [Warn, Audit]  # ou [Deny] pour bloquer
  matchResources:
    namespaceSelector:
      matchLabels:
        environment: "production"
```

Politique réutilisable avec différents bindings selon les namespaces
