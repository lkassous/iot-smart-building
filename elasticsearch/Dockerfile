# Elasticsearch avec mappings IoT Smart Building préconfigurés
FROM docker.elastic.co/elasticsearch/elasticsearch:8.11.0

LABEL maintainer="lkassous <lkassous17@gmail.com>"
LABEL description="Elasticsearch avec templates d'index IoT préconfigurés"
LABEL version="1.0.0"

# Copier les templates d'index
COPY mappings/ /usr/share/elasticsearch/config/mappings/

# Configuration par défaut pour mode single-node
ENV discovery.type=single-node
ENV xpack.security.enabled=false
ENV xpack.security.http.ssl.enabled=false
ENV ES_JAVA_OPTS="-Xms512m -Xmx512m"

# Exposer les ports
EXPOSE 9200 9300

# Commande par défaut
CMD ["elasticsearch"]
