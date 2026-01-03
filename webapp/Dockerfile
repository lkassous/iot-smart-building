FROM python:3.11-slim

# Métadonnées
LABEL maintainer="IoT Smart Building Team"
LABEL description="Flask webapp for IoT sensor monitoring"

# Variables d'environnement Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Répertoire de travail
WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code de l'application
COPY . .

# Création du répertoire uploads
RUN mkdir -p /app/uploads

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD curl -f http://localhost:8000/health || exit 1

# Exposition du port
EXPOSE 8000

# Utilisateur non-root pour la sécurité (optionnel en dev)
# RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
# USER appuser

# Commande de démarrage avec worker threading pour meilleure compatibilité
# Support long polling + threads pour Socket.IO
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "10", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
