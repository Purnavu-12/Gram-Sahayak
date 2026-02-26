"""
Tests for data retention policy enforcement.
"""

import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from models import DeletionStatus
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


def test_enforce_retention_policy_basic(privacy_manager):
    """Test basic retention policy enforcement."""
    user_id = "retention-user"
    
    # Create privacy settings with 30-day retention
    settings = privacy_manager.get_privacy_settings(user_id)
    settings.dataRetentionDays = 30
    privacy_manager.update_privacy_settings(settings)
    
    # Enforce retention policy
    cleanup_stats = privacy_manager.enforce_retention_policy(user_id)
    
    assert "accessLogsDeleted" in cleanup_stats
    assert "oldDeletionRecordsRemoved" in cleanup_stats


def test_enforce_retention_policy_deletes_old_logs(privacy_manager):
    """Test that retention policy deletes old access logs."""
    user_id = "old-logs-user"
    
    # Set retention to 30 days
    settings = privacy_manager.get_privacy_settings(user_id)
    settings.dataRetentionDays = 30
    privacy_manager.update_privacy_settings(settings)
    
    # Create old access logs
    for i in range(5):
        log = privacy_manager.log_data_access(
            user_id=user_id,
            accessed_by=f"accessor-{i}",
            access_type="read",
            data_fields=["profile"],
            purpose="Old access"
        )
        
        # Manually set timestamp to 60 days ago
        log.timestamp = datetime.utcnow() - timedelta(days=60)
        privacy_manager._save_access_log(log)
    
    # Create recent access logs
    for i in range(3):
        privacy_manager.log_data_access(
            user_id=user_id,
            accessed_by=f"recent-{i}",
            access_type="read",
            data_fields=["profile"],
            purpose="Recent access"
        )
    
    # Enforce retention policy
    cleanup_stats = privacy_manager.enforce_retention_policy(user_id)
    
    # Should delete 5 old logs
    assert cleanup_stats["accessLogsDeleted"] == 5
    
    # Verify recent logs still exist
    remaining_logs = privacy_manager.get_access_logs(user_id)
    assert len(remaining_logs) == 3


def test_enforce_retention_policy_keeps_recent_logs(privacy_manager):
    """Test that retention policy keeps recent access logs."""
    user_id = "recent-logs-user"
    
    # Set retention to 30 days
    settings = privacy_manager.get_privacy_settings(user_id)
    settings.dataRetentionDays = 30
    privacy_manager.update_privacy_settings(settings)
    
    # Create recent access logs (within retention period)
    for i in range(5):
        privacy_manager.log_data_access(
            user_id=user_id,
            accessed_by=f"accessor-{i}",
            access_type="read",
            data_fields=["profile"],
            purpose="Recent access"
        )
    
    # Enforce retention policy
    cleanup_stats = privacy_manager.enforce_retention_policy(user_id)
    
    # Should not delete any logs
    assert cleanup_stats["accessLogsDeleted"] == 0
    
    # Verify all logs still exist
    remaining_logs = privacy_manager.get_access_logs(user_id)
    assert len(remaining_logs) == 5


def test_enforce_retention_policy_deletes_old_deletion_records(privacy_manager):
    """Test that retention policy deletes old completed deletion records."""
    user_id = "old-deletion-user"
    
    # Set retention to 30 days
    settings = privacy_manager.get_privacy_settings(user_id)
    settings.dataRetentionDays = 30
    privacy_manager.update_privacy_settings(settings)
    
    # Create old completed deletion record
    record = privacy_manager.schedule_deletion(user_id)
    record.status = DeletionStatus.COMPLETED
    record.completedAt = datetime.utcnow() - timedelta(days=60)
    privacy_manager._save_deletion_record(record)
    
    # Enforce retention policy
    cleanup_stats = privacy_manager.enforce_retention_policy(user_id)
    
    # Should delete old deletion record
    assert cleanup_stats["oldDeletionRecordsRemoved"] == 1


def test_enforce_retention_policy_keeps_recent_deletion_records(privacy_manager):
    """Test that retention policy keeps recent deletion records."""
    user_id = "recent-deletion-user"
    
    # Set retention to 30 days
    settings = privacy_manager.get_privacy_settings(user_id)
    settings.dataRetentionDays = 30
    privacy_manager.update_privacy_settings(settings)
    
    # Create recent completed deletion record
    record = privacy_manager.schedule_deletion(user_id)
    record.status = DeletionStatus.COMPLETED
    record.completedAt = datetime.utcnow() - timedelta(days=10)
    privacy_manager._save_deletion_record(record)
    
    # Enforce retention policy
    cleanup_stats = privacy_manager.enforce_retention_policy(user_id)
    
    # Should not delete recent deletion record
    assert cleanup_stats["oldDeletionRecordsRemoved"] == 0


def test_enforce_retention_policy_keeps_scheduled_deletions(privacy_manager):
    """Test that retention policy keeps scheduled deletion records."""
    user_id = "scheduled-deletion-user"
    
    # Set retention to 30 days
    settings = privacy_manager.get_privacy_settings(user_id)
    settings.dataRetentionDays = 30
    privacy_manager.update_privacy_settings(settings)
    
    # Create scheduled deletion record
    privacy_manager.schedule_deletion(user_id)
    
    # Enforce retention policy
    cleanup_stats = privacy_manager.enforce_retention_policy(user_id)
    
    # Should not delete scheduled deletion record
    assert cleanup_stats["oldDeletionRecordsRemoved"] == 0


def test_enforce_retention_policy_custom_retention_period(privacy_manager):
    """Test retention policy with custom retention period."""
    user_id = "custom-retention-user"
    
    # Set retention to 90 days
    settings = privacy_manager.get_privacy_settings(user_id)
    settings.dataRetentionDays = 90
    privacy_manager.update_privacy_settings(settings)
    
    # Create access log 60 days old
    log = privacy_manager.log_data_access(
        user_id=user_id,
        accessed_by="accessor",
        access_type="read",
        data_fields=["profile"],
        purpose="Old access"
    )
    log.timestamp = datetime.utcnow() - timedelta(days=60)
    privacy_manager._save_access_log(log)
    
    # Enforce retention policy
    cleanup_stats = privacy_manager.enforce_retention_policy(user_id)
    
    # Should not delete log (within 90-day retention)
    assert cleanup_stats["accessLogsDeleted"] == 0


def test_enforce_retention_policy_no_data(privacy_manager):
    """Test retention policy enforcement with no data to clean."""
    user_id = "no-data-user"
    
    # Enforce retention policy
    cleanup_stats = privacy_manager.enforce_retention_policy(user_id)
    
    # Should have zero deletions
    assert cleanup_stats["accessLogsDeleted"] == 0
    assert cleanup_stats["oldDeletionRecordsRemoved"] == 0


def test_get_all_users_for_retention_cleanup(privacy_manager):
    """Test getting all users for retention cleanup."""
    # Create privacy settings for multiple users
    user_ids = ["user-1", "user-2", "user-3"]
    
    for user_id in user_ids:
        privacy_manager.get_privacy_settings(user_id)
    
    # Get all users
    all_users = privacy_manager.get_all_users_for_retention_cleanup()
    
    assert len(all_users) == 3
    for user_id in user_ids:
        assert user_id in all_users


def test_get_all_users_for_retention_cleanup_empty(privacy_manager):
    """Test getting all users when none exist."""
    all_users = privacy_manager.get_all_users_for_retention_cleanup()
    assert len(all_users) == 0


def test_enforce_retention_policy_mixed_data(privacy_manager):
    """Test retention policy with mixed old and recent data."""
    user_id = "mixed-data-user"
    
    # Set retention to 30 days
    settings = privacy_manager.get_privacy_settings(user_id)
    settings.dataRetentionDays = 30
    privacy_manager.update_privacy_settings(settings)
    
    # Create 3 old logs
    for i in range(3):
        log = privacy_manager.log_data_access(
            user_id=user_id,
            accessed_by=f"old-{i}",
            access_type="read",
            data_fields=["profile"],
            purpose="Old"
        )
        log.timestamp = datetime.utcnow() - timedelta(days=60)
        privacy_manager._save_access_log(log)
    
    # Create 2 recent logs
    for i in range(2):
        privacy_manager.log_data_access(
            user_id=user_id,
            accessed_by=f"recent-{i}",
            access_type="read",
            data_fields=["profile"],
            purpose="Recent"
        )
    
    # Create old deletion record
    record = privacy_manager.schedule_deletion(user_id)
    record.status = DeletionStatus.COMPLETED
    record.completedAt = datetime.utcnow() - timedelta(days=60)
    privacy_manager._save_deletion_record(record)
    
    # Enforce retention policy
    cleanup_stats = privacy_manager.enforce_retention_policy(user_id)
    
    # Should delete 3 old logs and 1 old deletion record
    assert cleanup_stats["accessLogsDeleted"] == 3
    assert cleanup_stats["oldDeletionRecordsRemoved"] == 1
    
    # Verify recent logs still exist
    remaining_logs = privacy_manager.get_access_logs(user_id)
    assert len(remaining_logs) == 2


def test_enforce_retention_policy_default_365_days(privacy_manager):
    """Test that default retention period is 365 days."""
    user_id = "default-retention-user"
    
    # Get default settings
    settings = privacy_manager.get_privacy_settings(user_id)
    
    # Verify default retention is 365 days
    assert settings.dataRetentionDays == 365
    
    # Create log 200 days old
    log = privacy_manager.log_data_access(
        user_id=user_id,
        accessed_by="accessor",
        access_type="read",
        data_fields=["profile"],
        purpose="Old access"
    )
    log.timestamp = datetime.utcnow() - timedelta(days=200)
    privacy_manager._save_access_log(log)
    
    # Enforce retention policy
    cleanup_stats = privacy_manager.enforce_retention_policy(user_id)
    
    # Should not delete log (within 365-day default retention)
    assert cleanup_stats["accessLogsDeleted"] == 0
