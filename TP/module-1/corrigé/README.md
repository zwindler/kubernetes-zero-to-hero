# TP 1 - Corrigé : Création et publication d'une image Docker

## Solutions des exercices

### app.py

```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "from zero to hero"

@app.route('/health')
def health():
    return {"status": "healthy"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

**Points clés** :
- `host='0.0.0.0'` : Nécessaire pour que l'application soit accessible depuis l'extérieur du conteneur
- Route `/health` : Bonus pour les health checks
- `debug=True` : Utile en développement

### requirements.txt

```txt
Flask==2.3.3
```

**Alternative** : Vous pouvez aussi utiliser `Flask>=2.0.0` pour plus de flexibilité.

### Dockerfile

```dockerfile
# Utiliser une image Python officielle slim pour réduire la taille
FROM python:3.11-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier requirements.txt en premier pour optimiser le cache Docker
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY app.py .

# Exposer le port sur lequel l'application va tourner
EXPOSE 5000

# Ajouter un health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Créer un utilisateur non-root pour la sécurité
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Commande pour démarrer l'application
CMD ["python", "app.py"]
```

**Optimisations incluses** :

- Image `slim` pour réduire la taille
- Cache Docker optimisé (requirements.txt copié en premier)
- `--no-cache-dir` pour éviter de stocker le cache pip
- Health check pour la surveillance
- Utilisateur non-root pour la sécurité

## Commandes complètes

### Construction

```bash
# Construire l'image
docker build -t ghcr.io/VOTRE_USERNAME/zero-to-hero:v1.0 .

# Tester localement
docker run -p 5000:5000 ghcr.io/VOTRE_USERNAME/zero-to-hero:v1.0

# Test avec curl
curl http://localhost:5000
# Résultat attendu: "from zero to hero"
```

### Publication sur GHCR

```bash
# Authentification
echo "VOTRE_TOKEN" | docker login ghcr.io -u VOTRE_USERNAME --password-stdin

# Push de l'image
docker push ghcr.io/VOTRE_USERNAME/zero-to-hero:v1.0

# Optionnel: Tagger et pousser comme latest
docker tag ghcr.io/VOTRE_USERNAME/zero-to-hero:v1.0 ghcr.io/VOTRE_USERNAME/zero-to-hero:latest
docker push ghcr.io/VOTRE_USERNAME/zero-to-hero:latest
```

## Quelques réflexions

### 1. Différence entre `v1.0` et `latest`

- `v1.0` : Tag figé, référence une version spécifique
- `latest` : Tag mobile, pointe vers la dernière version publiée
- En production, préférez les tags versionnés pour la reproductibilité

### 2. Pourquoi copier `requirements.txt` avant le reste ?

Docker met en cache chaque couche. Si on copie requirements.txt séparément et qu'on l'installe avant de copier le code, les dépendances ne seront réinstallées que si requirements.txt change, pas à chaque modification du code.

De manière générale, l'ordre des instructions dans une image Docker est très important pour réduire la taille des images sur la registry et les temps de build / pull.

### 3. Importance de `host='0.0.0.0'`

Par défaut, Flask écoute sur `127.0.0.1` (localhost). Dans un conteneur, cela rend l'application inaccessible depuis l'extérieur. `0.0.0.0` écoute sur toutes les interfaces.

### 4. Réduire la taille de l'image

- Utiliser des images `slim` ou `alpine`
- Multi-stage builds
- Supprimer les caches (`--no-cache-dir`)
- Utiliser `.dockerignore`
- Éviter d'installer des packages de développement en production

## Dockerfile alternatif (multi-stage)

Pour aller plus loin, voici une version multi-stage :

```dockerfile
# Stage 1: Build
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY app.py .
EXPOSE 5000
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "app.py"]
```

## Vérification

Votre image devrait :

- ✅ Être visible sur `ghcr.io/VOTRE_USERNAME/zero-to-hero`
- ✅ Répondre "from zero to hero" sur le port 5000
- ✅ Faire moins de 100MB (avec slim)
- ✅ Passer les health checks
- ✅ Fonctionner avec un utilisateur non-root
