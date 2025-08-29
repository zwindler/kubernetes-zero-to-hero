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
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
  [...]
  containers:
  - name: sec-ctx-demo
    image: busybox:1.28
    command: [ "sh", "-c", "sleep 1h" ]
```

---

## Security Context au niveau du container

Le **Container-level** a la priorité sur Pod-level :

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
      runAsUser: 2000              # Priorité sur Pod-level                         
      allowPrivilegeEscalation: false
```

---

## Concepts clés -  runAsUser et runAsGroup
- **runAsUser**: UID du processus principal
- **runAsGroup**: GID principal du processus
- **fsGroup**: GID propriétaire des volumes

---

### Capabilities
Contrôle fin des privilèges système :

```yaml
securityContext:
  capabilities:
    add: ["NET_ADMIN", "SYS_TIME"]
    drop: ["ALL"]
```

--- 

### Modes privilégiés et restrictions

```yaml
securityContext:
  privileged: false
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  runAsNonRoot: true
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
