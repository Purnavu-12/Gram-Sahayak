"""
Tests for privacy management and data deletion.
"""

import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from models import (
    DeletionStatus,
    PrivacyConsent
)
from privacy_manager import PrivacyManager


@pytest.fixture
def temp_storage():
    """Create a temporary storage directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def privacy_manager(temp_storage):
    """Create a privacy manager with temporary storage."""
    return PrivacyManager(storage_path=temp_storage)


def test_schedule_deletion(privacy_manager):
    """Test scheduling a data deletion."""
    user_id = "test-user-123"
    reason = "User requested account closure"
    
    record = privacy_manager.schedule_deletion(user_id, reason)
    
    assert record.userId == user_id
    assert record.reason == reason
    assert record.status == DeletionStatus.SCHEDULED
    assert record.scheduledDeletionDate > datetime.utcnow()
    assert (record.scheduledDeletionDate - record.requestedAt).days == 30


def test_get_deletion_status(privacy_manager):
    """Test retrieving deletion status."""
    user_id = "test-user-456"
    
    # Schedule deletion
    record = privacy_manager.schedule_deletion(user_id)
    
    # Retrieve status
    status = privacy_manager.get_deletion_status(user_id)
    
    assert status is not None
    assert status.userId == user_id
    assert status.deletionId == record.deletionId


def test_get_deletion_status_not_found(privacy_manager):
    """Test retrieving deletion status for non-existent user."""
    status = privacy_manager.get_deletion_status("non-existent-user")
    assert status is None


def test_cancel_deletion(privacy_manager):
    """Test cancelling a scheduled deletion."""
    user_id = "test-user-789"
    
    # Schedule deletion
    record = privacy_manager.schedule_deletion(user_id)
    
    # Cancel deletion
    success = privacy_manager.cancel_deletion(record.deletionId)
    
    assert success is True
    
    # Verify status is cancelled
    cancelled_record = privacy_manager._load_deletion_record(record.deletionId)
    assert cancelled_record.status == DeletionStatus.CANCELLED


def test_cancel_deletion_not_found(privacy_manager):
    """Test cancelling a non-existent deletion."""
    success = privacy_manager.cancel_deletion("non-existent-id")
    assert success is False


def test_get_pending_deletions(privacy_manager):
    """Test retrieving pending deletions."""
    # Schedule deletions with past dates
    user_id_1 = "user-1"
    user_id_2 = "user-2"
    
    record_1 = privacy_manager.schedule_deletion(user_id_1)
    record_2 = privacy_manager.schedule_deletion(user_id_2)
    
    # Manually set scheduled dates to past
    record_1.scheduledDeletionDate = datetime.utcnow() - timedelta(days=1)
    record_2.scheduledDeletionDate = datetime.utcnow() - timedelta(days=2)
    privacy_manager._save_deletion_record(record_1)
    privacy_manager._save_deletion_record(record_2)
    
    # Get pending deletions
    pending = privacy_manager.get_pending_deletions()
    
    assert len(pending) == 2
    assert any(r.userId == user_id_1 for r in pending)
    assert any(r.userId == user_id_2 for r in pending)


def test_get_pending_deletions_excludes_future(privacy_manager):
    """Test that pending deletions excludes future scheduled deletions."""
    user_id = "future-user"
    
    # Schedule deletion (30 days in future by default)
    privacy_manager.schedule_deletion(user_id)
    
    # Get pending deletions
    pending = privacy_manager.get_pending_deletions()
    
    # Should be empty since deletion is in future
    assert len(pending) == 0


def test_mark_deletion_completed(privacy_manager):
    """Test marking a deletion as completed."""
    user_id = "completed-user"
    
    record = privacy_manager.schedule_deletion(user_id)
    
    success = privacy_manager.mark_deletion_completed(record.deletionId)
    
    assert success is True
    
    # Verify status
    completed_record = privacy_manager._load_deletion_record(record.deletionId)
    assert completed_record.status == DeletionStatus.COMPLETED
    assert completed_record.completedAt is not None


def test_log_data_access(privacy_manager):
    """Test logging data access."""
    user_id = "access-user"
    accessed_by = "admin-123"
    access_type = "read"
    data_fields = ["name", "age", "phoneNumber"]
    purpose = "Profile review"
    ip_address = "192.168.1.1"
    
    log = privacy_manager.log_data_access(
        user_id=user_id,
        accessed_by=accessed_by,
        access_type=access_type,
        data_fields=data_fields,
        purpose=purpose,
        ip_address=ip_address
    )
    
    assert log.userId == user_id
    assert log.accessedBy == accessed_by
    assert log.accessType == access_type
    assert log.dataFields == data_fields
    assert log.purpose == purpose
    assert log.ipAddress == ip_address
    assert log.timestamp is not None


def test_get_access_logs(privacy_manager):
    """Test retrieving access logs for a user."""
    user_id = "log-user"
    
    # Create multiple access logs
    for i in range(5):
        privacy_manager.log_data_access(
            user_id=user_id,
            accessed_by=f"accessor-{i}",
            access_type="read",
            data_fields=["field1"],
            purpose=f"Purpose {i}"
        )
    
    # Retrieve logs
    logs = privacy_manager.get_access_logs(user_id)
    
    assert len(logs) == 5


def test_get_access_logs_with_limit(privacy_manager):
    """Test retrieving access logs with limit."""
    user_id = "limited-log-user"
    
    # Create 10 access logs
    for i in range(10):
        privacy_manager.log_data_access(
            user_id=user_id,
            accessed_by=f"accessor-{i}",
            access_type="read",
            data_fields=["field1"],
            purpose=f"Purpose {i}"
        )
    
    # Retrieve with limit
    logs = privacy_manager.get_access_logs(user_id, limit=5)
    
    assert len(logs) == 5


def test_get_access_logs_empty(privacy_manager):
    """Test retrieving access logs for user with no logs."""
    logs = privacy_manager.get_access_logs("no-logs-user")
    assert len(logs) == 0


def test_get_privacy_settings_default(privacy_manager):
    """Test getting default privacy settings."""
    user_id = "new-user"
    
    settings = privacy_manager.get_privacy_settings(user_id)
    
    assert settings.userId == user_id
    assert settings.dataRetentionDays == 365
    assert settings.allowFamilyAccess is True
    assert settings.allowDataExport is True
    assert len(settings.consents) == 0


def test_update_privacy_settings(privacy_manager):
    """Test updating privacy settings."""
    user_id = "settings-user"
    
    # Get default settings
    settings = privacy_manager.get_privacy_settings(user_id)
    
    # Update settings
    settings.dataRetentionDays = 180
    settings.allowFamilyAccess = False
    
    updated = privacy_manager.update_privacy_settings(settings)
    
    assert updated.dataRetentionDays == 180
    assert updated.allowFamilyAccess is False


def test_update_consent(privacy_manager):
    """Test updating user consent."""
    user_id = "consent-user"
    
    # Update consent
    settings = privacy_manager.update_consent(
        user_id=user_id,
        consent_type=PrivacyConsent.DATA_COLLECTION,
        granted=True,
        version="1.0"
    )
    
    assert len(settings.consents) == 1
    assert settings.consents[0].consentType == PrivacyConsent.DATA_COLLECTION
    assert settings.consents[0].granted is True
    assert settings.consents[0].version == "1.0"


def test_update_consent_replaces_existing(privacy_manager):
    """Test that updating consent replaces existing consent of same type."""
    user_id = "replace-consent-user"
    
    # Add initial consent
    privacy_manager.update_consent(
        user_id=user_id,
        consent_type=PrivacyConsent.DATA_SHARING,
        granted=True
    )
    
    # Update same consent type
    settings = privacy_manager.update_consent(
        user_id=user_id,
        consent_type=PrivacyConsent.DATA_SHARING,
        granted=False
    )
    
    # Should only have one consent of this type
    data_sharing_consents = [c for c in settings.consents if c.consentType == PrivacyConsent.DATA_SHARING]
    assert len(data_sharing_consents) == 1
    assert data_sharing_consents[0].granted is False


def test_multiple_consent_types(privacy_manager):
    """Test managing multiple consent types."""
    user_id = "multi-consent-user"
    
    # Add different consent types
    privacy_manager.update_consent(user_id, PrivacyConsent.DATA_COLLECTION, True)
    privacy_manager.update_consent(user_id, PrivacyConsent.DATA_SHARING, False)
    privacy_manager.update_consent(user_id, PrivacyConsent.MARKETING, True)
    
    settings = privacy_manager.get_privacy_settings(user_id)
    
    assert len(settings.consents) == 3
    
    # Verify each consent
    consent_map = {c.consentType: c.granted for c in settings.consents}
    assert consent_map[PrivacyConsent.DATA_COLLECTION] is True
    assert consent_map[PrivacyConsent.DATA_SHARING] is False
    assert consent_map[PrivacyConsent.MARKETING] is True


def test_deletion_30_day_compliance(privacy_manager):
    """Test that deletion is scheduled exactly 30 days in future."""
    user_id = "compliance-user"
    
    before = datetime.utcnow()
    record = privacy_manager.schedule_deletion(user_id)
    after = datetime.utcnow()
    
    # Calculate expected date range
    expected_min = before + timedelta(days=30)
    expected_max = after + timedelta(days=30)
    
    assert expected_min <= record.scheduledDeletionDate <= expected_max
