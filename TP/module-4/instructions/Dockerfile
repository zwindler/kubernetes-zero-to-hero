# Image Python production-ready pour le TP Module 4
FROM python:3.11-alpine

# Créer un utilisateur non-root
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

# Répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apk add --no-cache curl

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY app.py .

# Changer le propriétaire des fichiers
RUN chown -R appuser:appgroup /app
USER appuser

# Exposition du port
EXPOSE 3000

# Variables d'environnement par défaut
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=3000

# Health check Docker
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Commande de démarrage
CMD ["python", "app.py"]
