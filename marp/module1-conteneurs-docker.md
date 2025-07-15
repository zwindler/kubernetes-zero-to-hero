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

TODO 

![bg fit right:30%](binaries/container.png)

---

## Qu'est-ce qu'un conteneur ?

> C'est une boite 📦

Ensemble de techniques qui vont permettre d'**isoler** un processus des autres processus, du système de fichiers et des ressources de l'hôte.

Il existe plein de technos de containers : Docker est "juste" la plus populaire.

---

## Quelques différences containers vs VMs

- démarrage rapide (par de matériel à émuler / d'OS à démarrer)
- consommation souvent plus faible qu'une VM (ça dépend)
- partage du kernel (problématique pour certaines apps)
- isolation plus faible (sécurité ---)
- **immuabilité**

---

## Cas où la conteneurisation brille ✨

- **Microservices** : meilleure mutualisation des ressources
- Apps **stateless**
- **DevXP** : plus simple de construire un container qu'une VM
- Format *unique*

> *"Build once, run anywhere"* 🚀

![bg fit right:30%](binaries/itworks.jpg)

---

## Docker : démocratiser les containers pour les nuls

2014 : arrivée de ![height:50](binaries/docker.png)

- **Engine** : Runtime de conteneurs (cgroups, namespaces)
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

- **Docker Hub** : Registry public par défaut
- **Registry privé** : Pour vos images internes
- **Push/Pull** : Partage d'images

```bash
# Publier une image
docker push mon-registry/mon-app:v1.0

# Récupérer une image
docker pull nginx:latest
```

![bg fit right:25%](binaries/docker.png)

---

<!-- _class: lead -->

# TP 1 : Votre première image Docker 🛠️

---

## Objectif du TP 🎯

**Créer et publier votre propre image Docker**

### Ce que vous allez faire :
1. 🐍 Écrire un serveur web Python simple 
2. 📝 Créer un Dockerfile
3. 🔨 Construire l'image
4. 📤 La publier sur GitHub Container Registry

### Application à créer :
- Serveur web qui retourne **"from zero to hero"**
- Port 5000
- Framework Flask

---

## Instructions détaillées 📋

### Dossier TP/1/instructions/
- 📖 README complet avec toutes les étapes
- 🔗 Liens vers la documentation GitHub
- 💡 Conseils pour choisir l'image de base
- ✅ Checklist de vérification

### Support :
- Guide pour créer un Personal Access Token GitHub
- Commandes Docker essentielles
- Bonnes pratiques Dockerfile

**➡️ Rendez-vous dans `TP/1/instructions/README.md`**

---

<!-- _class: lead -->

## Questions ? 🤔

*Prêts pour passer à Kubernetes ?*

![bg fit right:40%](binaries/kubernetes_small.png)

---

## Bibliographie

* [Introduction to Docker and Containers](https://qconsf2017intro.container.training/#1)
* [github.com/jpetazzo/container.training](https://github.com/jpetazzo/container.training)