"""
Package utils pour IoT Smart Building
Clients pour Elasticsearch, MongoDB et Redis
"""
from .elasticsearch import es_client, ElasticsearchClient
from .mongodb import mongo_client, MongoDBClient
from .redis_client import redis_client, RedisClient, cache_result

__all__ = [
    'es_client',
    'ElasticsearchClient',
    'mongo_client',
    'MongoDBClient',
    'redis_client',
    'RedisClient',
    'cache_result'
]
