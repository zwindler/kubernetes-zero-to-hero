# TP 1 : Création et publication d'une image Docker

## Objectifs 🎯

- Créer un serveur web Python simple
- Écrire un Dockerfile pour containeriser l'application
- Construire l'image Docker
- Publier l'image sur GitHub Container Registry (GHCR)

## Prérequis ✅

- Docker installé et fonctionnel
- Compte GitHub
- Personal Access Token GitHub avec les permissions `packages:write` et `packages:read`

## Étape 1 : Créer l'application Python

Créez un fichier `app.py` qui contient un serveur web simple retournant "from zero to hero" :

```python
# Votre code ici
# Utilisez Flask ou une autre bibliothèque web Python
# Le serveur doit écouter sur le port 5000
# Route principale "/" doit retourner "from zero to hero"
```

**Indice** : Vous pouvez utiliser Flask avec quelque chose comme :
```python
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return "from zero to hero"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

Créez également un fichier `requirements.txt` pour spécifier les dépendances Python.

## Étape 2 : Choisir l'image de base

Pour une application Python, plusieurs options s'offrent à vous :

- `python:3.11` - Image officielle Python complète
- `python:3.11-slim` - Version allégée
- `python:3.11-alpine` - Version ultra-légère basée sur Alpine Linux

Question ouverte : quelle image avez vous choisie et pourquoi ? (Il n'y a pas de mauvaise réponse).

## Étape 3 : Écrire le Dockerfile 📝

Créez un `Dockerfile` qui :

1. Part d'une image Python appropriée
2. Définit un répertoire de travail
3. Copie le fichier `requirements.txt`
4. Installe les dépendances Python
5. Copie le code de l'application
6. Expose le port 5000
7. Définit la commande de démarrage

**Structure suggérée** :
```dockerfile
FROM ...
WORKDIR ...
COPY ...
RUN ...
COPY ...
EXPOSE ...
CMD ...
```

## Étape 4 : Construire l'image

Construisez votre image avec un tag approprié pour GitHub Container Registry.

**Commandes à utiliser** :
- `docker build` avec les bonnes options de tag
- `docker run` pour tester localement

**Indices** :
- Le tag doit suivre le format `ghcr.io/VOTRE_USERNAME/nom-image:version`
- N'oubliez pas de mapper le port 5000
- Testez avec `curl http://localhost:5000`

## Étape 5 : Configurer l'authentification GitHub

### Créer un Personal Access Token

1. Allez sur GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Générez un nouveau token avec les permissions :
   - `read:packages`
   - `write:packages`
   - `delete:packages` (optionnel)

### S'authentifier avec Docker

**Commande à utiliser** : `docker login`

**Indices** :
- Registry : `ghcr.io`
- Utilisez votre username GitHub
- Le token s'utilise comme mot de passe
- Option `--password-stdin` pour lire depuis l'entrée standard

**Documentation complète** : [Working with the Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry#authenticating-with-a-personal-access-token-classic)

## Étape 6 : Publier l'image

**Commande à utiliser** : `docker push`

**Indice** : Utilisez le même tag que celui utilisé pour la construction.

## Étape 7 : Vérification

1. Allez sur votre profil GitHub → Packages
2. Vérifiez que votre package `zero-to-hero` apparaît
3. Testez le téléchargement en supprimant l'image locale puis en la téléchargeant à nouveau

**Commandes à utiliser** :
- `docker rmi` pour supprimer l'image locale
- `docker pull` pour télécharger depuis le registry
- `docker run` pour tester à nouveau

## Bonus

- Ajoutez un tag `latest` en plus de `v1.0` (utilisez `docker tag`)
- Optimisez votre Dockerfile (multi-stage build, .dockerignore)
- Ajoutez des health checks
- Configurez la visibilité du package (public/private)

## Quelques réflexions 🤔

1. Quelle est la différence entre les tags `v1.0` et `latest` ?
2. Pourquoi utilise-t-on `COPY requirements.txt` avant `COPY . .` ?
3. Que se passe-t-il si vous ne spécifiez pas `host='0.0.0.0'` dans Flask ?
4. Comment pourriez-vous réduire la taille de votre image ?

## Ressources 📚

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [GitHub Container Registry Documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Python Docker Images](https://hub.docker.com/_/python)
