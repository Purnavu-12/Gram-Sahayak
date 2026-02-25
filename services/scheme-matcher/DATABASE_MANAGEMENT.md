# Scheme Database Management

This document describes the database management features implemented for the Gram Sahayak Scheme Matcher service, validating Requirement 3.4.

## Overview

The scheme database management system provides three key capabilities:

1. **Real-time Scheme Updates** - Update scheme information dynamically
2. **External API Integration** - Sync with myScheme API and e-Shram platform
3. **Data Freshness Monitoring** - Monitor data staleness and generate alerts

## Components

### 1. Real-time Scheme Updates

The `SchemeMatcherService` provides methods to update scheme information in real-time:

```python
from scheme_matcher_service import SchemeMatcherService

service = SchemeMatcherService()

# Update existing scheme
await service.update_scheme_database([
    {
        "scheme_id": "PM-KISAN",
        "changes": {
            "benefit_amount": 7000,
            "description": "Updated description"
        }
    }
])

# Add new scheme
await service.update_scheme_database([
    {
        "scheme_id": "NEW-SCHEME",
        "changes": {
            "name": "New Scheme Name",
            "benefit_amount": 5000,
            "eligibility": {
                "occupation": ["farmer"]
            }
        }
    }
])

# Check update status
status = service.get_scheme_update_status()
print(f"Total schemes: {status['total_schemes']}")
print(f"Recent updates: {status['recent_updates']}")
```

### 2. External API Integration

The `ExternalAPIIntegration` class provides integration with government scheme APIs:

#### myScheme API Integration

```python
from external_api_integration import ExternalAPIIntegration

api = ExternalAPIIntegration(
    myscheme_api_url="https://api.myscheme.gov.in/v1",
    api_key="your_api_key"
)

# Fetch schemes from myScheme
schemes = await api.fetch_schemes_from_myscheme(
    filters={"category": "agriculture", "state": "UP"}
)

# Fetch recent updates
updates = await api.fetch_scheme_updates(
    since=datetime.now() - timedelta(hours=24)
)

await api.close()
```

#### e-Shram API Integration

```python
# Fetch worker-specific schemes from e-Shram
worker_schemes = await api.fetch_worker_schemes_from_eshram(
    occupation_type="construction_worker"
)
```

#### Automatic Sync

The `SchemeMatcherService` provides a convenient method to sync with both APIs:

```python
# Sync with external APIs
result = await service.sync_with_external_apis()

if result["success"]:
    print(f"Synced {result['schemes_updated']} schemes")
    print(f"Sources: {result['sources']}")
else:
    print(f"Sync failed: {result['message']}")
```

### 3. Data Freshness Monitoring

The `DataFreshnessMonitor` tracks scheme data freshness and generates alerts:

#### Freshness Status Levels

- **FRESH**: Updated within 24 hours
- **STALE**: Updated more than 24 hours ago
- **CRITICAL**: Updated more than 48 hours ago
- **UNKNOWN**: No update timestamp available

#### Using the Monitor

```python
from data_freshness_monitor import DataFreshnessMonitor

monitor = DataFreshnessMonitor(
    freshness_threshold_hours=24,
    critical_threshold_hours=48
)

# Check database freshness
freshness = monitor.check_database_freshness(schemes)

print(f"Status: {freshness['status']}")
print(f"Fresh: {freshness['fresh_count']} ({freshness['fresh_percentage']:.1f}%)")
print(f"Stale: {freshness['stale_count']} ({freshness['stale_percentage']:.1f}%)")
print(f"Critical: {freshness['critical_count']} ({freshness['critical_percentage']:.1f}%)")

# Get stale schemes that need updating
stale_schemes = monitor.get_stale_schemes(schemes)
for scheme in stale_schemes:
    print(f"Scheme {scheme['scheme_id']} needs update: {scheme['freshness_status']}")
```

#### Alert Callbacks

Register callbacks to be notified when freshness alerts are generated:

```python
def handle_alert(alert):
    if alert.severity == "error":
        # Send notification, trigger sync, etc.
        print(f"CRITICAL: {alert.message}")
    elif alert.severity == "warning":
        print(f"WARNING: {alert.message}")

monitor.register_alert_callback(handle_alert)

# Alerts will be triggered automatically during freshness checks
freshness = monitor.check_database_freshness(schemes)
```

#### Integrated Monitoring

The `SchemeMatcherService` includes integrated freshness monitoring:

```python
# Check data freshness
freshness = service.check_data_freshness()
print(f"Database status: {freshness['status']}")

# Get stale schemes
stale = service.get_stale_schemes()
print(f"Found {len(stale)} stale schemes")

# Get recent alerts
alerts = service.get_freshness_alerts(hours=24)
for alert in alerts:
    print(f"{alert['severity']}: {alert['message']}")
```

## Complete Workflow Example

Here's a complete example of using all database management features:

```python
from scheme_matcher_service import SchemeMatcherService
from datetime import datetime, timedelta

async def manage_scheme_database():
    # Initialize service
    service = SchemeMatcherService(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password"
    )
    
    try:
        # 1. Check current status
        status = service.get_scheme_update_status()
        print(f"Current database: {status['total_schemes']} schemes")
        
        # 2. Check data freshness
        freshness = service.check_data_freshness()
        print(f"Freshness status: {freshness['status']}")
        
        if freshness['stale_count'] > 0:
            print(f"Warning: {freshness['stale_count']} stale schemes")
        
        # 3. Sync with external APIs if needed
        if freshness['status'] in ['warning', 'critical']:
            print("Syncing with external APIs...")
            result = await service.sync_with_external_apis()
            
            if result['success']:
                print(f"Successfully updated {result['schemes_updated']} schemes")
            else:
                print(f"Sync failed: {result['message']}")
        
        # 4. Manual update if needed
        await service.update_scheme_database([
            {
                "scheme_id": "PM-KISAN",
                "changes": {
                    "benefit_amount": 7000,
                    "last_updated": datetime.now().isoformat()
                }
            }
        ])
        
        # 5. Verify updates
        final_status = service.get_scheme_update_status()
        print(f"Final status: {final_status['recent_updates']} recent updates")
        
        # 6. Check for alerts
        alerts = service.get_freshness_alerts(hours=1)
        if alerts:
            print(f"Generated {len(alerts)} alerts")
            for alert in alerts:
                print(f"  - {alert['severity']}: {alert['message']}")
    
    finally:
        await service.close()

# Run the workflow
import asyncio
asyncio.run(manage_scheme_database())
```

## Configuration

### Environment Variables

You can configure the database management system using environment variables:

```bash
# myScheme API
MYSCHEME_API_URL=https://api.myscheme.gov.in/v1
MYSCHEME_API_KEY=your_api_key

# e-Shram API
ESHRAM_API_URL=https://api.eshram.gov.in/v1
ESHRAM_API_KEY=your_api_key

# Freshness thresholds
FRESHNESS_THRESHOLD_HOURS=24
CRITICAL_THRESHOLD_HOURS=48

# Neo4j (optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### Programmatic Configuration

```python
from external_api_integration import ExternalAPIIntegration
from data_freshness_monitor import DataFreshnessMonitor

# Configure API integration
api = ExternalAPIIntegration(
    myscheme_api_url="https://api.myscheme.gov.in/v1",
    eshram_api_url="https://api.eshram.gov.in/v1",
    api_key="your_api_key",
    timeout=30  # seconds
)

# Configure freshness monitoring
monitor = DataFreshnessMonitor(
    freshness_threshold_hours=24,
    critical_threshold_hours=48
)
```

## Testing

Run the database management tests:

```bash
cd services/scheme-matcher
python -m pytest tests/test_database_management.py -v
```

Test coverage includes:
- External API integration and data transformation
- Data freshness monitoring and alerts
- Integration with SchemeMatcherService
- Complete workflow testing

## API Endpoints

If using the FastAPI service, the following endpoints are available:

```
GET  /api/schemes/status          - Get scheme database status
POST /api/schemes/sync            - Sync with external APIs
GET  /api/schemes/freshness       - Check data freshness
GET  /api/schemes/stale           - Get list of stale schemes
GET  /api/schemes/alerts          - Get freshness alerts
```

## Monitoring and Alerts

### Alert Severity Levels

- **info**: Informational messages
- **warning**: Stale data (>24 hours)
- **error**: Critical data staleness (>48 hours)

### Alert Structure

```json
{
  "alert_id": "alert_1234567890_SCHEME-001",
  "timestamp": "2024-01-15T10:30:00",
  "status": "stale",
  "scheme_id": "SCHEME-001",
  "message": "Scheme PM-KISAN data is stale (>24 hours)",
  "severity": "warning",
  "metadata": {
    "last_updated": "2024-01-14T08:00:00",
    "scheme_name": "PM-KISAN"
  }
}
```

## Best Practices

1. **Regular Syncing**: Schedule regular syncs with external APIs (e.g., every 12 hours)
2. **Monitor Alerts**: Set up alert callbacks to notify administrators of stale data
3. **Graceful Degradation**: Handle API failures gracefully and use cached data
4. **Update Logging**: Keep track of all updates for audit purposes
5. **Freshness Checks**: Run freshness checks before critical operations

## Troubleshooting

### API Connection Issues

If external API integration fails:
- Check network connectivity
- Verify API credentials
- Check API rate limits
- Review API endpoint URLs

The service will fall back to in-memory database if APIs are unavailable.

### Freshness Monitoring Not Working

If freshness monitoring is not available:
- Ensure `data_freshness_monitor.py` is in the Python path
- Check that schemes have `last_updated` timestamps
- Verify monitoring is initialized in SchemeMatcherService

### Neo4j Connection Issues

If Neo4j connection fails:
- Verify Neo4j is running
- Check connection credentials
- Ensure Neo4j URI is correct

The service will fall back to in-memory database if Neo4j is unavailable.

## Requirements Validation

This implementation validates **Requirement 3.4**:

> WHEN scheme criteria change, THE Knowledge_Base SHALL update eligibility rules within 24 hours

The implementation provides:
- ✅ Real-time scheme update system
- ✅ Integration with myScheme API and e-Shram platform
- ✅ Data freshness monitoring with 24-hour threshold
- ✅ Automatic alerts for stale data
- ✅ Comprehensive testing coverage
