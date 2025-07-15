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

# Module 1 : Les Fondamentaux ![height:60](binaries/docker.png)
## Les Conteneurs et Docker

*Formation Kubernetes - Débutant à Avancé*

---

## Sommaire du Module 1

- Qu'est-ce qu'un conteneur ?
- Conteneurs vs Machines Virtuelles
- Cas d'usage de la conteneurisation
- Docker : démocratiser les containers
- Dockerfile : écrire des recettes
- Commandes Docker essentielles
- Docker Registry : stockage d'images
- **TP pratique** : Créer et publier votre image

![bg fit right:30%](binaries/container.png)

---

## Qu'est-ce qu'un conteneur ?

> C'est une boite 📦

Ensemble de techniques qui vont permettre d'**isoler** un processus des autres processus, du système de fichiers et des ressources de l'hôte.

Il existe plein de technos de containers : Docker est "juste" l'outil que les a popularisé.

* voir aussi : [jail BSD](https://docs.freebsd.org/en/books/handbook/jails/), [zone Solaris](https://docs.oracle.com/cd/E19253-01/820-2318/zones.intro-1/index.html), [openVZ](https://openvz.org/), [LXC](https://linuxcontainers.org/), ...

---

## Quelques différences containers vs VMs

- ➕ démarrage rapide (pas de matériel à émuler / d'OS à démarrer)
- ➕ consommation souvent plus faible qu'une VM (ça dépend)
- ➖ partage du kernel (problématique pour certaines apps)
- ➖ isolation plus faible (sécurité ---)
- ⚖️ **immuabilité**

Note : Il existe des solution de type microVMs qui peuvent être un entre deux intéressant (ex : [Firecracker](https://firecracker-microvm.github.io/))

---

## Cas où la conteneurisation brille ✨

- **Microservices** : mutualisation des ressources d'un hôte
- Apps **stateless** (mise à l'échelle simple)
- **DevXP** : plus simple de construire un container qu'une VM
- Package *unique* censé fonctionner "partout"

> *"Build once, run anywhere"* 🚀

![bg fit right:27%](binaries/itworks.jpg)

---

## Docker : démocratise les containers linux

* [dotScale 2013 - Solomon Hykes - Why we built Docker](https://www.youtube.com/watch?v=3N3n9FzebAA)

- **Engine** : Runtime de conteneurs ([cgroups, namespaces](https://www.youtube.com/watch?v=sK5i-N34im8))
- **Images** : Templates pour les conteneurs
- **Registry** : Stockage d'images (Docker Hub)
- **Compose** : Orchestration simple
- **Desktop** : Interface graphique

---

## Dockerfile : La recette 📝

- Write an install.sh script that works for you
- Turn this file into a Dockerfile, test it on your machine
- If the Dockerfile builds on your machine, it will build anywhere



```dockerfile
FROM node:24-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

---

## Commandes Docker essentielles

```bash
# Construire une image
docker build -t mon-app:v1.0 .

# Lancer un conteneur
docker run -d -p 8080:3000 mon-app:v1.0

# Voir les logs
docker logs <container-id>

# Accéder au conteneur
docker exec -it <container-id> /bin/bash
```

---

## Plus de commandes Docker

```bash
# Lister les conteneurs en cours (ajouter -a pour voir ceux arrêtés)
docker ps

# Lister les images locales
docker images

# Arrêter un conteneur
docker stop <container-id>

# Supprimer un conteneur
docker rm <container-id>

# Supprimer une image
docker rmi <image-id>
```

---

## Docker Registry : Le magasin d'images

- **[Docker Hub](https://hub.docker.com/)** : Registry public par défaut (payant sauf pour les individus et certains projets OSS)
- **Registry privé** : Pour vos images internes
- **Push/Pull** : Partage d'images

```bash
# Publier une image
docker push mon-registry/mon-app:v1.0

# Récupérer une image
docker pull nginx:latest
```

---

<!-- _class: lead -->

# TP 1 : Votre première image Docker

---

## Objectif du TP : créer et publier votre propre image Docker

A partir d'un serveur web Python simple :

1. Créer un Dockerfile
2. Construire l'image
3. La lancer en local
4. La publier sur GitHub Container Registry

Allez dans le dossier `TP/1/instructions/`

---

## Desktop, Compose, Swarm

Quelques outils supplémentaires développé par Docker Inc.

- [**Docker Desktop** - Interface graphique pour développeurs (Windows/Mac)](https://www.docker.com/products/docker-desktop/)
- [**Compose : multi-conteneurs avec YAML** - `docker-compose up`](https://docs.docker.com/compose/)
- [**Swarm : mlustering natif Docker** - Alternative basique à Kubernetes](https://docs.docker.com/engine/swarm/)

> K8s reste **le** standard pour l'orchestration de containers

---

<!-- _class: lead -->

## Questions ? 🤔

*Prêts pour passer à Kubernetes ?*

![bg fit right:40%](binaries/kubernetes_small.png)

---

## Bibliographie

- [dotScale 2013 - Solomon Hykes - Why we built Docker](https://www.youtube.com/watch?v=3N3n9FzebAA)
- [DockerCon EU 2021 - Jérôme Petazzoni - Cgroups, namespaces, and beyond: what are containers made from?](https://www.youtube.com/watch?v=sK5i-N34im8)
- [Introduction to Docker and Containers](https://qconsf2017intro.container.training/#1)
- [github.com/jpetazzo/container.training](https://github.com/jpetazzo/container.training)