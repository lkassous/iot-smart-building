# Kibana avec dashboards IoT Smart Building préconfigurés
FROM docker.elastic.co/kibana/kibana:8.11.0

LABEL maintainer="lkassous <lkassous17@gmail.com>"
LABEL description="Kibana avec dashboards IoT préconfigurés"
LABEL version="1.0.0"

# Copier les exports de dashboards
COPY exports/ /usr/share/kibana/config/exports/

# Configuration par défaut
ENV ELASTICSEARCH_HOSTS=http://elasticsearch:9200
ENV xpack.security.enabled=false

# Exposer le port
EXPOSE 5601

# Commande par défaut
CMD ["kibana"]
