# Logstash avec pipelines IoT Smart Building préconfigurés
FROM docker.elastic.co/logstash/logstash:8.11.0

LABEL maintainer="lkassous <lkassous17@gmail.com>"
LABEL description="Logstash avec pipelines IoT pour capteurs CSV et alertes JSON"
LABEL version="1.0.0"

# Copier les fichiers de configuration
COPY config/logstash.yml /usr/share/logstash/config/logstash.yml

# Copier les pipelines d'ingestion
COPY pipeline/ /usr/share/logstash/pipeline/

# Créer le répertoire pour les uploads
RUN mkdir -p /usr/share/logstash/uploads

# Exposer les ports
EXPOSE 5000 9600

# Commande par défaut
CMD ["logstash"]
