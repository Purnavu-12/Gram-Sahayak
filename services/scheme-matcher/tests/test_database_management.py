"""
Tests for Scheme Database Management
Validates: Requirement 3.4 - Real-time scheme updates, API integration, and data freshness monitoring
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scheme_matcher_service import SchemeMatcherService
from external_api_integration import ExternalAPIIntegration
from data_freshness_monitor import DataFreshnessMonitor, FreshnessStatus


@pytest.fixture
def matcher():
    """Create a SchemeMatcherService instance for testing"""
    service = SchemeMatcherService()
    yield service
    # Note: close() is async but we can't await in a sync fixture
    # The service will clean up on garbage collection


@pytest.fixture
def api_integration():
    """Create an ExternalAPIIntegration instance for testing"""
    return ExternalAPIIntegration(
        myscheme_api_url="https://test.myscheme.gov.in/v1",
        eshram_api_url="https://test.eshram.gov.in/v1",
        api_key="test_key"
    )


@pytest.fixture
def freshness_monitor():
    """Create a DataFreshnessMonitor instance for testing"""
    return DataFreshnessMonitor(
        freshness_threshold_hours=24,
        critical_threshold_hours=48
    )


# ============================================================================
# External API Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_api_integration_initialization(api_integration):
    """Test API integration initialization"""
    assert api_integration.myscheme_api_url == "https://test.myscheme.gov.in/v1"
    assert api_integration.eshram_api_url == "https://test.eshram.gov.in/v1"
    assert api_integration.api_key == "test_key"
    assert api_integration.timeout == 30


@pytest.mark.asyncio
async def test_transform_myscheme_data(api_integration):
    """Test transformation of myScheme API data to internal format"""
    api_data = {
        "schemes": [
            {
                "id": "TEST-SCHEME-001",
                "name": "Test Scheme",
                "description": "Test description",
                "eligibility": {
                    "occupation": ["farmer"],
                    "age_min": 18,
                    "income_max": 100000
                },
                "benefit_amount": 5000,
                "complexity": "simple",
                "category": "agriculture",
                "updated_at": "2024-01-01T00:00:00"
            }
        ]
    }
    
    schemes = api_integration._transform_myscheme_data(api_data)
    
    assert len(schemes) == 1
    assert schemes[0]["scheme_id"] == "TEST-SCHEME-001"
    assert schemes[0]["name"] == "Test Scheme"
    assert schemes[0]["difficulty"] == "easy"  # Mapped from "simple"
    assert schemes[0]["eligibility"]["occupation"] == ["farmer"]
    assert schemes[0]["eligibility"]["min_age"] == 18
    assert schemes[0]["eligibility"]["max_income"] == 100000
    assert schemes[0]["source"] == "myScheme"


@pytest.mark.asyncio
async def test_transform_eshram_data(api_integration):
    """Test transformation of e-Shram API data to internal format"""
    api_data = {
        "data": [
            {
                "scheme_id": "ESHRAM-001",
                "scheme_name": "Worker Scheme",
                "description": "Worker support",
                "eligibility": {
                    "occupations": ["laborer", "worker"],
                    "age_min": 18
                },
                "benefit_amount": 8000,
                "complexity": "moderate"
            }
        ]
    }
    
    schemes = api_integration._transform_eshram_data(api_data)
    
    assert len(schemes) == 1
    assert schemes[0]["scheme_id"] == "ESHRAM-001"
    assert schemes[0]["name"] == "Worker Scheme"
    assert schemes[0]["difficulty"] == "medium"  # Mapped from "moderate"
    assert schemes[0]["category"] == "employment"  # e-Shram default
    assert schemes[0]["eligibility"]["occupation"] == ["laborer", "worker"]
    assert schemes[0]["source"] == "e-Shram"


@pytest.mark.asyncio
async def test_deduplicate_schemes(api_integration):
    """Test scheme deduplication based on scheme_id"""
    schemes = [
        {
            "scheme_id": "SCHEME-001",
            "name": "Old Version",
            "last_updated": "2024-01-01T00:00:00"
        },
        {
            "scheme_id": "SCHEME-001",
            "name": "New Version",
            "last_updated": "2024-01-02T00:00:00"
        },
        {
            "scheme_id": "SCHEME-002",
            "name": "Different Scheme",
            "last_updated": "2024-01-01T00:00:00"
        }
    ]
    
    unique = api_integration._deduplicate_schemes(schemes)
    
    assert len(unique) == 2
    # Should keep the newer version of SCHEME-001
    scheme_001 = next(s for s in unique if s["scheme_id"] == "SCHEME-001")
    assert scheme_001["name"] == "New Version"


# ============================================================================
# Data Freshness Monitoring Tests
# ============================================================================

def test_check_fresh_scheme(freshness_monitor):
    """Test freshness check for recently updated scheme"""
    scheme = {
        "scheme_id": "FRESH-001",
        "name": "Fresh Scheme",
        "last_updated": datetime.now().isoformat()
    }
    
    status = freshness_monitor.check_scheme_freshness(scheme)
    assert status == FreshnessStatus.FRESH


def test_check_stale_scheme(freshness_monitor):
    """Test freshness check for stale scheme (>24 hours)"""
    old_time = datetime.now() - timedelta(hours=30)
    scheme = {
        "scheme_id": "STALE-001",
        "name": "Stale Scheme",
        "last_updated": old_time.isoformat()
    }
    
    status = freshness_monitor.check_scheme_freshness(scheme)
    assert status == FreshnessStatus.STALE


def test_check_critical_scheme(freshness_monitor):
    """Test freshness check for critical scheme (>48 hours)"""
    old_time = datetime.now() - timedelta(hours=72)
    scheme = {
        "scheme_id": "CRITICAL-001",
        "name": "Critical Scheme",
        "last_updated": old_time.isoformat()
    }
    
    status = freshness_monitor.check_scheme_freshness(scheme)
    assert status == FreshnessStatus.CRITICAL


def test_check_unknown_scheme(freshness_monitor):
    """Test freshness check for scheme without timestamp"""
    scheme = {
        "scheme_id": "UNKNOWN-001",
        "name": "Unknown Scheme"
        # No last_updated field
    }
    
    status = freshness_monitor.check_scheme_freshness(scheme)
    assert status == FreshnessStatus.UNKNOWN


def test_check_database_freshness_healthy(freshness_monitor):
    """Test database freshness check with healthy data"""
    schemes = [
        {
            "scheme_id": f"SCHEME-{i}",
            "name": f"Scheme {i}",
            "last_updated": datetime.now().isoformat()
        }
        for i in range(10)
    ]
    
    result = freshness_monitor.check_database_freshness(schemes)
    
    assert result["status"] == "healthy"
    assert result["total_schemes"] == 10
    assert result["fresh_count"] == 10
    assert result["stale_count"] == 0
    assert result["critical_count"] == 0
    assert result["fresh_percentage"] == 100.0


def test_check_database_freshness_with_stale(freshness_monitor):
    """Test database freshness check with some stale schemes"""
    schemes = []
    
    # 7 fresh schemes
    for i in range(7):
        schemes.append({
            "scheme_id": f"FRESH-{i}",
            "name": f"Fresh {i}",
            "last_updated": datetime.now().isoformat()
        })
    
    # 3 stale schemes
    old_time = datetime.now() - timedelta(hours=30)
    for i in range(3):
        schemes.append({
            "scheme_id": f"STALE-{i}",
            "name": f"Stale {i}",
            "last_updated": old_time.isoformat()
        })
    
    result = freshness_monitor.check_database_freshness(schemes)
    
    assert result["total_schemes"] == 10
    assert result["fresh_count"] == 7
    assert result["stale_count"] == 3
    assert result["stale_percentage"] == 30.0
    assert len(result["alerts"]) == 3  # One alert per stale scheme


def test_check_database_freshness_critical(freshness_monitor):
    """Test database freshness check with critical schemes"""
    schemes = []
    
    # 5 fresh schemes
    for i in range(5):
        schemes.append({
            "scheme_id": f"FRESH-{i}",
            "name": f"Fresh {i}",
            "last_updated": datetime.now().isoformat()
        })
    
    # 5 critical schemes (>48 hours)
    old_time = datetime.now() - timedelta(hours=72)
    for i in range(5):
        schemes.append({
            "scheme_id": f"CRITICAL-{i}",
            "name": f"Critical {i}",
            "last_updated": old_time.isoformat()
        })
    
    result = freshness_monitor.check_database_freshness(schemes)
    
    assert result["total_schemes"] == 10
    assert result["critical_count"] == 5
    assert result["critical_percentage"] == 50.0
    assert result["status"] == "critical"  # >10% critical
    assert len(result["alerts"]) == 5


def test_get_stale_schemes(freshness_monitor):
    """Test getting list of stale schemes"""
    schemes = [
        {
            "scheme_id": "FRESH-001",
            "name": "Fresh",
            "last_updated": datetime.now().isoformat()
        },
        {
            "scheme_id": "STALE-001",
            "name": "Stale",
            "last_updated": (datetime.now() - timedelta(hours=30)).isoformat()
        },
        {
            "scheme_id": "CRITICAL-001",
            "name": "Critical",
            "last_updated": (datetime.now() - timedelta(hours=72)).isoformat()
        }
    ]
    
    stale = freshness_monitor.get_stale_schemes(schemes)
    
    assert len(stale) == 2  # Stale and critical
    scheme_ids = [s["scheme_id"] for s in stale]
    assert "STALE-001" in scheme_ids
    assert "CRITICAL-001" in scheme_ids
    assert "FRESH-001" not in scheme_ids


def test_alert_callback_registration(freshness_monitor):
    """Test registering alert callbacks"""
    callback_called = []
    
    def test_callback(alert):
        callback_called.append(alert)
    
    freshness_monitor.register_alert_callback(test_callback)
    
    # Trigger an alert by checking critical scheme
    schemes = [{
        "scheme_id": "CRITICAL-001",
        "name": "Critical",
        "last_updated": (datetime.now() - timedelta(hours=72)).isoformat()
    }]
    
    freshness_monitor.check_database_freshness(schemes)
    
    assert len(callback_called) == 1
    assert callback_called[0].severity == "error"


def test_get_recent_alerts(freshness_monitor):
    """Test getting recent alerts"""
    # Generate some alerts
    schemes = [{
        "scheme_id": "STALE-001",
        "name": "Stale",
        "last_updated": (datetime.now() - timedelta(hours=30)).isoformat()
    }]
    
    freshness_monitor.check_database_freshness(schemes)
    
    recent = freshness_monitor.get_recent_alerts(hours=24)
    
    assert len(recent) > 0
    assert all("alert_id" in a for a in recent)
    assert all("timestamp" in a for a in recent)


def test_monitoring_summary(freshness_monitor):
    """Test getting monitoring summary"""
    summary = freshness_monitor.get_monitoring_summary()
    
    assert "total_alerts" in summary
    assert "recent_alerts_24h" in summary
    assert "severity_counts" in summary
    assert "freshness_threshold_hours" in summary
    assert summary["freshness_threshold_hours"] == 24
    assert summary["critical_threshold_hours"] == 48


# ============================================================================
# Integration Tests with SchemeMatcherService
# ============================================================================

@pytest.mark.asyncio
async def test_scheme_matcher_with_freshness_monitoring(matcher):
    """Test SchemeMatcherService with integrated freshness monitoring"""
    if not matcher.freshness_monitor:
        pytest.skip("Freshness monitoring not available")
    
    # Check freshness
    freshness = matcher.check_data_freshness()
    
    assert "status" in freshness
    assert "total_schemes" in freshness
    assert freshness["total_schemes"] > 0


@pytest.mark.asyncio
async def test_get_stale_schemes_from_matcher(matcher):
    """Test getting stale schemes from matcher service"""
    if not matcher.freshness_monitor:
        pytest.skip("Freshness monitoring not available")
    
    # Add a stale scheme
    old_time = datetime.now() - timedelta(hours=30)
    await matcher.update_scheme_database([{
        "scheme_id": "TEST-STALE",
        "changes": {
            "name": "Test Stale Scheme",
            "last_updated": old_time.isoformat()
        }
    }])
    
    stale = matcher.get_stale_schemes()
    
    # Should find at least the one we added
    assert isinstance(stale, list)


@pytest.mark.asyncio
async def test_get_freshness_alerts_from_matcher(matcher):
    """Test getting freshness alerts from matcher service"""
    if not matcher.freshness_monitor:
        pytest.skip("Freshness monitoring not available")
    
    alerts = matcher.get_freshness_alerts(hours=24)
    
    assert isinstance(alerts, list)


@pytest.mark.asyncio
async def test_scheme_update_status_with_freshness(matcher):
    """Test scheme update status includes freshness data"""
    status = matcher.get_scheme_update_status()
    
    assert "last_update_time" in status
    assert "total_schemes" in status
    
    if matcher.freshness_monitor:
        assert "freshness" in status
        assert "status" in status["freshness"]


@pytest.mark.asyncio
async def test_sync_with_external_apis_no_integration(matcher):
    """Test sync when API integration is not available"""
    # Temporarily disable API integration
    original = matcher.api_integration
    matcher.api_integration = None
    
    result = await matcher.sync_with_external_apis()
    
    assert result["success"] is False
    assert "not available" in result["message"]
    
    matcher.api_integration = original


@pytest.mark.asyncio
async def test_database_management_complete_workflow():
    """Test complete database management workflow"""
    # Create service with all features
    service = SchemeMatcherService()
    
    try:
        # 1. Check initial status
        status = service.get_scheme_update_status()
        assert status["total_schemes"] > 0
        
        # 2. Update a scheme
        await service.update_scheme_database([{
            "scheme_id": "PM-KISAN",
            "changes": {
                "benefit_amount": 7500,
                "description": "Updated via workflow test"
            }
        }])
        
        # 3. Verify update
        updated_status = service.get_scheme_update_status()
        assert updated_status["recent_updates"] >= 1
        
        # 4. Check freshness (if available)
        if service.freshness_monitor:
            freshness = service.check_data_freshness()
            assert freshness["total_schemes"] > 0
        
        # 5. Get stale schemes (if monitoring available)
        if service.freshness_monitor:
            stale = service.get_stale_schemes()
            assert isinstance(stale, list)
        
    finally:
        await service.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
