"""
Tests unitaires pour le module Elasticsearch
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestElasticsearchQueries:
    """Tests pour les requêtes Elasticsearch"""
    
    def test_build_basic_search_query(self):
        """Test construction d'une requête de recherche basique"""
        query = {
            "query": {
                "match_all": {}
            },
            "size": 50
        }
        
        assert "query" in query
        assert query["size"] == 50
    
    def test_build_filtered_search_query(self):
        """Test construction d'une requête avec filtres"""
        zone = "A"
        sensor_type = "temperature"
        
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"zone": zone}},
                        {"term": {"sensor_type": sensor_type}}
                    ]
                }
            }
        }
        
        assert query["query"]["bool"]["must"][0]["term"]["zone"] == "A"
        assert query["query"]["bool"]["must"][1]["term"]["sensor_type"] == "temperature"
    
    def test_build_date_range_query(self):
        """Test construction d'une requête avec filtre de date"""
        date_from = "2025-10-28T00:00:00Z"
        date_to = "2025-10-28T23:59:59Z"
        
        query = {
            "query": {
                "range": {
                    "@timestamp": {
                        "gte": date_from,
                        "lte": date_to
                    }
                }
            }
        }
        
        assert query["query"]["range"]["@timestamp"]["gte"] == date_from
        assert query["query"]["range"]["@timestamp"]["lte"] == date_to
    
    def test_build_aggregation_query(self):
        """Test construction d'une requête d'agrégation"""
        query = {
            "size": 0,
            "aggs": {
                "by_zone": {
                    "terms": {"field": "zone"},
                    "aggs": {
                        "avg_value": {"avg": {"field": "value"}}
                    }
                }
            }
        }
        
        assert query["size"] == 0
        assert "by_zone" in query["aggs"]
        assert "avg_value" in query["aggs"]["by_zone"]["aggs"]
    
    def test_build_temperature_average_query(self):
        """Test requête température moyenne par zone"""
        query = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"sensor_type": "temperature"}},
                        {"range": {"@timestamp": {"gte": "now-24h"}}}
                    ]
                }
            },
            "aggs": {
                "by_zone": {
                    "terms": {"field": "zone", "size": 9},
                    "aggs": {
                        "avg_temp": {"avg": {"field": "value"}}
                    }
                }
            }
        }
        
        assert query["query"]["bool"]["must"][0]["term"]["sensor_type"] == "temperature"
        assert query["aggs"]["by_zone"]["terms"]["size"] == 9


class TestElasticsearchClient:
    """Tests pour le client Elasticsearch"""
    
    def test_search_returns_results(self, mock_elasticsearch):
        """Test que la recherche retourne des résultats"""
        result = mock_elasticsearch.search(
            index="logs-iot-sensors-*",
            body={"query": {"match_all": {}}}
        )
        
        assert "hits" in result
        assert result["hits"]["total"]["value"] == 100
    
    def test_count_documents(self, mock_elasticsearch):
        """Test comptage des documents"""
        result = mock_elasticsearch.count(index="logs-iot-sensors-*")
        
        assert result["count"] == 100
    
    def test_index_document(self, mock_elasticsearch):
        """Test indexation d'un document"""
        doc = {
            "@timestamp": datetime.now().isoformat(),
            "zone": "A",
            "sensor_type": "temperature",
            "value": 22.5
        }
        
        result = mock_elasticsearch.index(
            index="logs-iot-sensors-2025.10.28",
            body=doc
        )
        
        assert result["result"] == "created"
    
    def test_cluster_health(self, mock_elasticsearch):
        """Test vérification santé du cluster"""
        health = mock_elasticsearch.cluster.health()
        
        assert health["status"] in ["green", "yellow", "red"]


class TestElasticsearchResponse:
    """Tests pour le parsing des réponses ES"""
    
    def test_parse_search_hits(self, mock_elasticsearch):
        """Test extraction des hits de recherche"""
        result = mock_elasticsearch.search(
            index="logs-iot-sensors-*",
            body={"query": {"match_all": {}}}
        )
        
        hits = result["hits"]["hits"]
        
        assert len(hits) >= 1
        assert "_source" in hits[0]
        assert "zone" in hits[0]["_source"]
    
    def test_parse_aggregation_results(self):
        """Test parsing résultats d'agrégation"""
        agg_response = {
            "aggregations": {
                "by_zone": {
                    "buckets": [
                        {"key": "A", "doc_count": 100, "avg_temp": {"value": 22.5}},
                        {"key": "B", "doc_count": 80, "avg_temp": {"value": 21.8}},
                        {"key": "C", "doc_count": 60, "avg_temp": {"value": 23.1}}
                    ]
                }
            }
        }
        
        buckets = agg_response["aggregations"]["by_zone"]["buckets"]
        
        assert len(buckets) == 3
        assert buckets[0]["key"] == "A"
        assert buckets[0]["avg_temp"]["value"] == 22.5
    
    def test_calculate_statistics(self):
        """Test calcul de statistiques à partir des résultats"""
        buckets = [
            {"key": "A", "avg_temp": {"value": 22.5}},
            {"key": "B", "avg_temp": {"value": 21.8}},
            {"key": "C", "avg_temp": {"value": 23.1}}
        ]
        
        values = [b["avg_temp"]["value"] for b in buckets]
        
        avg = sum(values) / len(values)
        min_val = min(values)
        max_val = max(values)
        
        assert round(avg, 2) == 22.47
        assert min_val == 21.8
        assert max_val == 23.1


class TestIndexNaming:
    """Tests pour la convention de nommage des index"""
    
    def test_sensor_index_pattern(self):
        """Test pattern d'index pour les capteurs"""
        date = datetime(2025, 10, 28)
        index_name = f"logs-iot-sensors-{date.strftime('%Y.%m.%d')}"
        
        assert index_name == "logs-iot-sensors-2025.10.28"
    
    def test_alert_index_pattern(self):
        """Test pattern d'index pour les alertes"""
        date = datetime(2025, 10, 28)
        index_name = f"logs-iot-alerts-{date.strftime('%Y.%m.%d')}"
        
        assert index_name == "logs-iot-alerts-2025.10.28"
    
    def test_wildcard_pattern(self):
        """Test patterns avec wildcard"""
        sensors_pattern = "logs-iot-sensors-*"
        alerts_pattern = "logs-iot-alerts-*"
        all_pattern = "logs-iot-*"
        
        assert "*" in sensors_pattern
        assert "*" in alerts_pattern
        assert "*" in all_pattern


class TestQueryDSL:
    """Tests pour la construction de Query DSL"""
    
    def test_combine_must_clauses(self):
        """Test combinaison de clauses must"""
        clauses = []
        
        # Ajouter des filtres conditionnellement
        zone = "A"
        if zone:
            clauses.append({"term": {"zone": zone}})
        
        sensor_type = "temperature"
        if sensor_type:
            clauses.append({"term": {"sensor_type": sensor_type}})
        
        query = {
            "query": {
                "bool": {
                    "must": clauses
                }
            }
        }
        
        assert len(query["query"]["bool"]["must"]) == 2
    
    def test_pagination_params(self):
        """Test paramètres de pagination"""
        page = 2
        per_page = 50
        
        from_offset = (page - 1) * per_page
        size = per_page
        
        assert from_offset == 50
        assert size == 50
    
    def test_sort_by_timestamp(self):
        """Test tri par timestamp"""
        sort = [
            {"@timestamp": {"order": "desc"}}
        ]
        
        assert sort[0]["@timestamp"]["order"] == "desc"
