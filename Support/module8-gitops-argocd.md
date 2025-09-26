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

# Module 8 : GitOps et ArgoCD
## Déploiement continu déclaratif

*Formation Kubernetes - Débutant à Avancé*

---

## Plan du Module 8 (1/2)

**Introduction : Qu'est-ce que GitOps ?**
- Principes fondamentaux
- Lien avec Helm/Kustomize (Module 7)
- Push vs Pull deployment

**ArgoCD : L'outil de référence**
- Écosystème GitOps
- Architecture et concepts
- Installation et configuration

---

## Plan du Module 8 (2/2)

**Utilisation pratique**
- Applications et projets
- Synchronisation et hooks
- Multi-environnements

**Production et bonnes pratiques**
- Structure des repositories
- Multi-cluster, Troubleshooting, ...

---

<!-- _class: lead -->

# Introduction : Qu'est-ce que GitOps ?

---

## GitOps : Définition et principes

**GitOps = Git + Operations**

> **Git** comme source de vérité unique pour l'infra et les applications

Les 4 principes fondamentaux :

1. **Déclaratif** : Configuration stockée dans Git
2. **Versionné et immutable** : Historique complet dans Git  
3. **Pull automatique** : Agents tirent les changements
4. **Réconciliation continue** : État désiré vs état réel

---

## Helm et Kustomize dans GitOps

```
Git Repository
├── apps/
│   ├── my-app/                 ← Kustomize
│   │   ├── base/
│   │   └── overlays/
│   └── database/               ← Helm
│       ├── Chart.yaml
│       └── values-prod.yaml
└── ArgoCD surveille ce repo et déploie automatiquement
```

<br/>

**GitOps utilise les outils vu précédemment, mais de manière automatisée !**

---

## Push vs Pull

```
CI/CD Pipeline ──push──> Kubernetes Cluster
    │                         │
    ├── Credentials           ├── Sécurité complexe
    ├── Accès cluster         ├── Debugging difficile
    └── État non tracé        └── Drift possible
```

**Approche GitOps (Pull) :**
```
Git Repo ←──pull──── GitOps Agent (dans le cluster)
    │                         │
    ├── Source de vérité      ├── Sécurité renforcée
    ├── Audit complet         ├── Auto-healing
    └── Rollback facile       └── État toujours sync
```

---

## Avantages du GitOps

- **Collaboration** : Pull requests pour les déploiements, revues
- **Reproductibilité** : Environnements identiques, moins d'erreur humaine
- **Debugging** : État désiré toujours visible
- **Traçabilité / compliances** : Qui a changé quoi et quand ? Audit trail
- **Rollback** : `git revert` = rollback applicatif
- **Disaster recovery** : Tout dans Git

---

<!-- _class: lead -->

# ArgoCD : L'outil de référence

---

## Écosystème GitOps

| Outil | Forces | Faiblesses | Adoption |
|-------|---------|------------|----------|
| **ArgoCD** | Interface riche, maturité | Plus lourd | ⭐⭐⭐⭐⭐ |
| **Flux** | Léger, GitOps pur | Interface limitée | ⭐⭐⭐⭐ |
| **Jenkins X** | Intégration CI/CD | Complexité | ⭐⭐ |
| **Tekton + triggers** | Cloud native | Setup complexe | ⭐⭐⭐ |

**ArgoCD = choix de référence pour débuter et scaler**
