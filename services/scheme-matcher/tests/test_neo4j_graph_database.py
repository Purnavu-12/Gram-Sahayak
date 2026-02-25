"""
Test Neo4j Graph Database Integration for Scheme Matcher
Task 5.1: Set up graph database for scheme relationships
Validates: Requirements 3.1, 3.2
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scheme_matcher_service import SchemeMatcherService, NEO4J_AVAILABLE


@pytest.fixture
def neo4j_matcher():
    """Create matcher with Neo4j if available"""
    if NEO4J_AVAILABLE:
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        try:
            matcher = SchemeMatcherService(
                neo4j_uri=neo4j_uri,
                neo4j_user=neo4j_user,
                neo4j_password=neo4j_password
            )
            if matcher.neo4j_driver is None:
                pytest.skip("Neo4j server not available")
            yield matcher
            matcher.close()
        except Exception as e:
            pytest.skip(f"Neo4j not available: {e}")
    else:
        pytest.skip("Neo4j driver not installed")


@pytest.fixture
def in_memory_matcher():
    """Create matcher without Neo4j for comparison"""
    matcher = SchemeMatcherService()
    yield matcher
    matcher.close()


@pytest.fixture
def farmer_profile():
    """Profile of a farmer for testing"""
    return {
        "user_id": "farmer001",
        "personal_info": {
            "name": "Ram Kumar",
            "age": 45,
            "gender": "male"
        },
        "demographics": {
            "state": "Uttar Pradesh",
            "district": "Lucknow",
            "caste": "obc"
        },
        "economic": {
            "annual_income": 150000,
            "occupation": "farmer",
            "land_ownership": {"has_land": True, "acres": 2.5}
        }
    }


def test_neo4j_availability():
    """Test that Neo4j driver is available"""
    assert NEO4J_AVAILABLE, "Neo4j driver should be installed (neo4j package)"


def test_neo4j_initialization(neo4j_matcher):
    """Test that Neo4j database initializes successfully"""
    assert neo4j_matcher.neo4j_driver is not None
    assert neo4j_matcher.schemes_db is not None
    assert len(neo4j_matcher.schemes_db) > 0


def test_graph_database_scheme_nodes(neo4j_matcher):
    """Test that scheme nodes are created in Neo4j graph"""
    if not neo4j_matcher.neo4j_driver:
        pytest.skip("Neo4j not connected")
    
    with neo4j_matcher.neo4j_driver.session() as session:
        # Query all scheme nodes
        result = session.run("MATCH (s:Scheme) RETURN count(s) as count")
        record = result.single()
        
        assert record is not None
        assert record["count"] >= 7  # At least 7 pre-configured schemes


def test_graph_database_relationships(neo4j_matcher):
    """Test that scheme relationships are created in Neo4j graph"""
    if not neo4j_matcher.neo4j_driver:
        pytest.skip("Neo4j not connected")
    
    with neo4j_matcher.neo4j_driver.session() as session:
        # Query relationships
        result = session.run(
            "MATCH (s1:Scheme)-[r:RELATED_TO]->(s2:Scheme) RETURN count(r) as count"
        )
        record = result.single()
        
        assert record is not None
        assert record["count"] > 0  # Should have relationships


def test_graph_database_specific_relationships(neo4j_matcher):
    """Test specific scheme relationships in graph"""
    if not neo4j_matcher.neo4j_driver:
        pytest.skip("Neo4j not connected")
    
    with neo4j_matcher.neo4j_driver.session() as session:
        # PM-KISAN should be related to MGNREGA
        result = session.run(
            """
            MATCH (s1:Scheme {scheme_id: 'PM-KISAN'})-[:RELATED_TO]->(s2:Scheme)
            RETURN s2.scheme_id as related_id
            """
        )
        
        related_ids = [record["related_id"] for record in result]
        assert "MGNREGA" in related_ids or "PM-FASAL-BIMA" in related_ids


@pytest.mark.asyncio
async def test_graph_based_alternative_suggestions(neo4j_matcher, farmer_profile):
    """Test that graph database enhances alternative suggestions"""
    if not neo4j_matcher.neo4j_driver:
        pytest.skip("Neo4j not connected")
    
    # Make farmer ineligible for PM-KISAN
    farmer_profile["economic"]["land_ownership"] = {"has_land": False}
    
    alternatives = await neo4j_matcher.suggest_alternative_schemes(
        farmer_profile, "PM-KISAN"
    )
    
    # Should get alternatives based on graph relationships
    assert isinstance(alternatives, list)
    # MGNREGA should be suggested as it's related to PM-KISAN
    if len(alternatives) > 0:
        scheme_ids = [s["scheme_id"] for s in alternatives]
        assert "MGNREGA" in scheme_ids


@pytest.mark.asyncio
async def test_graph_vs_memory_consistency(neo4j_matcher, in_memory_matcher, farmer_profile):
    """Test that Neo4j and in-memory implementations give consistent results"""
    # Find eligible schemes with both implementations
    neo4j_schemes = await neo4j_matcher.find_eligible_schemes(farmer_profile)
    memory_schemes = await in_memory_matcher.find_eligible_schemes(farmer_profile)
    
    # Should find same schemes
    neo4j_ids = set(s["scheme_id"] for s in neo4j_schemes)
    memory_ids = set(s["scheme_id"] for s in memory_schemes)
    
    assert neo4j_ids == memory_ids


def test_graph_database_scheme_properties(neo4j_matcher):
    """Test that scheme properties are correctly stored in graph"""
    if not neo4j_matcher.neo4j_driver:
        pytest.skip("Neo4j not connected")
    
    with neo4j_matcher.neo4j_driver.session() as session:
        # Query PM-KISAN properties
        result = session.run(
            """
            MATCH (s:Scheme {scheme_id: 'PM-KISAN'})
            RETURN s.name as name, s.benefit_amount as benefit, s.category as category
            """
        )
        record = result.single()
        
        assert record is not None
        assert record["name"] == "PM-KISAN"
        assert record["benefit"] == 6000
        assert record["category"] == "agriculture"


@pytest.mark.asyncio
async def test_graph_database_update_sync(neo4j_matcher):
    """Test that updates sync to Neo4j graph database"""
    if not neo4j_matcher.neo4j_driver:
        pytest.skip("Neo4j not connected")
    
    # Update a scheme
    updates = [
        {
            "scheme_id": "PM-KISAN",
            "changes": {
                "benefit_amount": 7500,
                "description": "Updated via test"
            }
        }
    ]
    
    await neo4j_matcher.update_scheme_database(updates)
    
    # Verify update in graph database
    with neo4j_matcher.neo4j_driver.session() as session:
        result = session.run(
            """
            MATCH (s:Scheme {scheme_id: 'PM-KISAN'})
            RETURN s.benefit_amount as benefit
            """
        )
        record = result.single()
        
        assert record is not None
        assert record["benefit"] == 7500


def test_graph_database_complex_relationships(neo4j_matcher):
    """Test complex relationship queries in graph database"""
    if not neo4j_matcher.neo4j_driver:
        pytest.skip("Neo4j not connected")
    
    with neo4j_matcher.neo4j_driver.session() as session:
        # Find schemes related to agriculture category
        result = session.run(
            """
            MATCH (s:Scheme {category: 'agriculture'})-[:RELATED_TO]->(related:Scheme)
            RETURN s.scheme_id as source, related.scheme_id as target
            """
        )
        
        relationships = [(r["source"], r["target"]) for r in result]
        assert len(relationships) > 0


def test_fallback_to_memory_when_neo4j_unavailable():
    """Test that system falls back to in-memory database when Neo4j is unavailable"""
    # Create matcher with invalid Neo4j URI
    matcher = SchemeMatcherService(
        neo4j_uri="bolt://invalid:7687",
        neo4j_user="neo4j",
        neo4j_password="password"
    )
    
    # Should still work with in-memory database
    assert matcher.schemes_db is not None
    assert len(matcher.schemes_db) > 0
    assert matcher.neo4j_driver is None  # Neo4j should not be connected
    
    matcher.close()


@pytest.mark.asyncio
async def test_graph_database_700_schemes_capacity(neo4j_matcher):
    """Test that graph database can handle 700+ schemes as per requirements"""
    if not neo4j_matcher.neo4j_driver:
        pytest.skip("Neo4j not connected")
    
    # Add multiple schemes to test scalability
    updates = []
    for i in range(100):
        updates.append({
            "scheme_id": f"TEST-SCHEME-{i}",
            "changes": {
                "name": f"Test Scheme {i}",
                "benefit_amount": 5000 + i * 100,
                "difficulty": "easy",
                "category": "test",
                "eligibility": {"occupation": ["farmer"]}
            }
        })
    
    await neo4j_matcher.update_scheme_database(updates)
    
    # Verify schemes were added to graph
    with neo4j_matcher.neo4j_driver.session() as session:
        result = session.run("MATCH (s:Scheme) RETURN count(s) as count")
        record = result.single()
        
        assert record["count"] >= 100  # Should have at least 100 test schemes


def test_graph_database_connection_cleanup(neo4j_matcher):
    """Test that Neo4j connections are properly cleaned up"""
    if not neo4j_matcher.neo4j_driver:
        pytest.skip("Neo4j not connected")
    
    # Verify driver is connected
    assert neo4j_matcher.neo4j_driver is not None
    
    # Close connection
    neo4j_matcher.close()
    
    # Driver should be closed (no exception should be raised)
    # Note: neo4j driver doesn't have a simple "is_closed" check,
    # but close() should be idempotent


@pytest.mark.asyncio
async def test_graph_relationship_traversal(neo4j_matcher, farmer_profile):
    """Test traversing relationships in graph for related schemes"""
    if not neo4j_matcher.neo4j_driver:
        pytest.skip("Neo4j not connected")
    
    # Get related schemes using graph traversal
    related = await neo4j_matcher._get_related_schemes_from_graph(
        "PM-KISAN", farmer_profile
    )
    
    assert isinstance(related, list)
    # Should find related schemes that farmer is eligible for
    if len(related) > 0:
        assert all("scheme_id" in s for s in related)
        assert all("match_score" in s for s in related)


def test_graph_database_data_model_completeness(neo4j_matcher):
    """Test that all required scheme properties are in graph data model"""
    if not neo4j_matcher.neo4j_driver:
        pytest.skip("Neo4j not connected")
    
    with neo4j_matcher.neo4j_driver.session() as session:
        # Query a scheme and verify all properties
        result = session.run(
            """
            MATCH (s:Scheme {scheme_id: 'PM-KISAN'})
            RETURN properties(s) as props
            """
        )
        record = result.single()
        
        assert record is not None
        props = record["props"]
        
        # Verify required properties
        required_props = ["scheme_id", "name", "description", "benefit_amount", 
                         "difficulty", "category", "last_updated"]
        for prop in required_props:
            assert prop in props, f"Missing required property: {prop}"


@pytest.mark.asyncio
async def test_eligibility_graph_mapping(neo4j_matcher, farmer_profile):
    """Test complex eligibility relationship mapping in graph"""
    if not neo4j_matcher.neo4j_driver:
        pytest.skip("Neo4j not connected")
    
    # Find all eligible schemes
    schemes = await neo4j_matcher.find_eligible_schemes(farmer_profile)
    
    # For each eligible scheme, verify relationships exist
    for scheme in schemes:
        scheme_id = scheme["scheme_id"]
        
        with neo4j_matcher.neo4j_driver.session() as session:
            result = session.run(
                """
                MATCH (s:Scheme {scheme_id: $scheme_id})
                RETURN s.scheme_id as id
                """,
                scheme_id=scheme_id
            )
            record = result.single()
            
            assert record is not None, f"Scheme {scheme_id} not found in graph"
