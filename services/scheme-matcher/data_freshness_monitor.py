"""
Data Freshness Monitoring and Alerts
Validates: Requirement 3.4 - Data freshness monitoring and alerts

This module monitors scheme database freshness and triggers alerts
when data becomes stale (>24 hours old).
"""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FreshnessStatus(Enum):
    """Enum for data freshness status"""
    FRESH = "fresh"  # Updated within 24 hours
    STALE = "stale"  # Updated more than 24 hours ago
    CRITICAL = "critical"  # Updated more than 48 hours ago
    UNKNOWN = "unknown"  # No update timestamp available


@dataclass
class FreshnessAlert:
    """Data class for freshness alerts"""
    alert_id: str
    timestamp: datetime
    status: FreshnessStatus
    scheme_id: Optional[str]
    message: str
    severity: str  # "info", "warning", "error"
    metadata: Dict[str, Any]


class DataFreshnessMonitor:
    """
    Monitor scheme database freshness and generate alerts
    Validates: Requirement 3.4
    """

    def __init__(
        self,
        freshness_threshold_hours: int = 24,
        critical_threshold_hours: int = 48
    ):
        self.freshness_threshold = timedelta(hours=freshness_threshold_hours)
        self.critical_threshold = timedelta(hours=critical_threshold_hours)
        self.alerts: List[FreshnessAlert] = []
        self.alert_callbacks: List[Callable[[FreshnessAlert], None]] = []

    def register_alert_callback(self, callback: Callable[[FreshnessAlert], None]):
        """
        Register a callback function to be called when alerts are generated
        
        Args:
            callback: Function that takes a FreshnessAlert as parameter
        """
        self.alert_callbacks.append(callback)

    def check_scheme_freshness(
        self,
        scheme: Dict[str, Any]
    ) -> FreshnessStatus:
        """
        Check freshness status of a single scheme
        
        Args:
            scheme: Scheme dictionary with last_updated field
            
        Returns:
            FreshnessStatus enum value
        """
        last_updated_str = scheme.get("last_updated")
        
        if not last_updated_str:
            return FreshnessStatus.UNKNOWN
        
        try:
            last_updated = datetime.fromisoformat(last_updated_str)
            age = datetime.now() - last_updated
            
            if age > self.critical_threshold:
                return FreshnessStatus.CRITICAL
            elif age > self.freshness_threshold:
                return FreshnessStatus.STALE
            else:
                return FreshnessStatus.FRESH
                
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing last_updated timestamp: {e}")
            return FreshnessStatus.UNKNOWN

    def check_database_freshness(
        self,
        schemes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check freshness of entire scheme database
        
        Args:
            schemes: List of all schemes in database
            
        Returns:
            Dictionary with freshness statistics and alerts
        """
        if not schemes:
            return {
                "status": "empty",
                "total_schemes": 0,
                "fresh_count": 0,
                "stale_count": 0,
                "critical_count": 0,
                "unknown_count": 0,
                "alerts": []
            }
        
        status_counts = {
            FreshnessStatus.FRESH: 0,
            FreshnessStatus.STALE: 0,
            FreshnessStatus.CRITICAL: 0,
            FreshnessStatus.UNKNOWN: 0
        }
        
        stale_schemes = []
        critical_schemes = []
        
        for scheme in schemes:
            status = self.check_scheme_freshness(scheme)
            status_counts[status] += 1
            
            if status == FreshnessStatus.STALE:
                stale_schemes.append(scheme)
            elif status == FreshnessStatus.CRITICAL:
                critical_schemes.append(scheme)
        
        # Generate alerts for stale and critical schemes
        new_alerts = []
        
        for scheme in critical_schemes:
            alert = self._create_alert(
                scheme_id=scheme.get("scheme_id"),
                status=FreshnessStatus.CRITICAL,
                message=f"Scheme {scheme.get('name', scheme.get('scheme_id'))} data is critically stale (>48 hours)",
                severity="error",
                metadata={
                    "last_updated": scheme.get("last_updated"),
                    "scheme_name": scheme.get("name")
                }
            )
            new_alerts.append(alert)
            self._trigger_alert(alert)
        
        for scheme in stale_schemes:
            alert = self._create_alert(
                scheme_id=scheme.get("scheme_id"),
                status=FreshnessStatus.STALE,
                message=f"Scheme {scheme.get('name', scheme.get('scheme_id'))} data is stale (>24 hours)",
                severity="warning",
                metadata={
                    "last_updated": scheme.get("last_updated"),
                    "scheme_name": scheme.get("name")
                }
            )
            new_alerts.append(alert)
            self._trigger_alert(alert)
        
        # Overall database status
        total = len(schemes)
        critical_pct = (status_counts[FreshnessStatus.CRITICAL] / total) * 100
        stale_pct = (status_counts[FreshnessStatus.STALE] / total) * 100
        
        if critical_pct > 10:  # More than 10% critical
            overall_status = "critical"
        elif stale_pct > 25:  # More than 25% stale
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "total_schemes": total,
            "fresh_count": status_counts[FreshnessStatus.FRESH],
            "stale_count": status_counts[FreshnessStatus.STALE],
            "critical_count": status_counts[FreshnessStatus.CRITICAL],
            "unknown_count": status_counts[FreshnessStatus.UNKNOWN],
            "fresh_percentage": (status_counts[FreshnessStatus.FRESH] / total) * 100,
            "stale_percentage": stale_pct,
            "critical_percentage": critical_pct,
            "alerts": [self._alert_to_dict(a) for a in new_alerts],
            "timestamp": datetime.now().isoformat()
        }

    def get_stale_schemes(
        self,
        schemes: List[Dict[str, Any]],
        include_critical: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get list of schemes that need updating
        
        Args:
            schemes: List of all schemes
            include_critical: Whether to include critical schemes
            
        Returns:
            List of schemes that are stale or critical
        """
        stale_schemes = []
        
        for scheme in schemes:
            status = self.check_scheme_freshness(scheme)
            
            if status == FreshnessStatus.STALE:
                stale_schemes.append({
                    **scheme,
                    "freshness_status": "stale"
                })
            elif status == FreshnessStatus.CRITICAL and include_critical:
                stale_schemes.append({
                    **scheme,
                    "freshness_status": "critical"
                })
        
        return stale_schemes

    def get_recent_alerts(
        self,
        hours: int = 24,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent alerts within specified time window
        
        Args:
            hours: Number of hours to look back
            severity: Filter by severity ("info", "warning", "error")
            
        Returns:
            List of recent alerts
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [
            alert for alert in self.alerts
            if alert.timestamp >= cutoff
        ]
        
        if severity:
            recent = [a for a in recent if a.severity == severity]
        
        return [self._alert_to_dict(a) for a in recent]

    def clear_old_alerts(self, days: int = 7):
        """
        Clear alerts older than specified days
        
        Args:
            days: Number of days to retain alerts
        """
        cutoff = datetime.now() - timedelta(days=days)
        self.alerts = [
            alert for alert in self.alerts
            if alert.timestamp >= cutoff
        ]
        logger.info(f"Cleared alerts older than {days} days")

    def _create_alert(
        self,
        scheme_id: Optional[str],
        status: FreshnessStatus,
        message: str,
        severity: str,
        metadata: Dict[str, Any]
    ) -> FreshnessAlert:
        """Create a new freshness alert"""
        alert = FreshnessAlert(
            alert_id=f"alert_{datetime.now().timestamp()}_{scheme_id or 'system'}",
            timestamp=datetime.now(),
            status=status,
            scheme_id=scheme_id,
            message=message,
            severity=severity,
            metadata=metadata
        )
        self.alerts.append(alert)
        return alert

    def _trigger_alert(self, alert: FreshnessAlert):
        """Trigger all registered alert callbacks"""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

    def _alert_to_dict(self, alert: FreshnessAlert) -> Dict[str, Any]:
        """Convert FreshnessAlert to dictionary"""
        return {
            "alert_id": alert.alert_id,
            "timestamp": alert.timestamp.isoformat(),
            "status": alert.status.value,
            "scheme_id": alert.scheme_id,
            "message": alert.message,
            "severity": alert.severity,
            "metadata": alert.metadata
        }

    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get summary of monitoring status"""
        total_alerts = len(self.alerts)
        recent_alerts = len(self.get_recent_alerts(hours=24))
        
        severity_counts = {
            "info": 0,
            "warning": 0,
            "error": 0
        }
        
        for alert in self.alerts:
            severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1
        
        return {
            "total_alerts": total_alerts,
            "recent_alerts_24h": recent_alerts,
            "severity_counts": severity_counts,
            "freshness_threshold_hours": self.freshness_threshold.total_seconds() / 3600,
            "critical_threshold_hours": self.critical_threshold.total_seconds() / 3600,
            "registered_callbacks": len(self.alert_callbacks),
            "timestamp": datetime.now().isoformat()
        }
