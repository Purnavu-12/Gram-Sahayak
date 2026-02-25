"""
Privacy management and data deletion service.
Handles user consent, data access logging, and 30-day deletion compliance.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from pathlib import Path

from models import (
    DeletionRecord,
    DeletionStatus,
    DataAccessLog,
    PrivacySettings,
    ConsentRecord,
    PrivacyConsent
)


class PrivacyManager:
    """Manages privacy settings, consent, and data deletion."""
    
    def __init__(self, storage_path: str = "./data/privacy"):
        """
        Initialize privacy manager.
        
        Args:
            storage_path: Directory for privacy-related data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.deletion_path = self.storage_path / "deletions"
        self.deletion_path.mkdir(exist_ok=True)
        
        self.access_log_path = self.storage_path / "access_logs"
        self.access_log_path.mkdir(exist_ok=True)
        
        self.settings_path = self.storage_path / "settings"
        self.settings_path.mkdir(exist_ok=True)
    
    def schedule_deletion(self, user_id: str, reason: Optional[str] = None) -> DeletionRecord:
        """
        Schedule a user profile for deletion with 30-day compliance.
        
        Args:
            user_id: User identifier
            reason: Optional reason for deletion
            
        Returns:
            Deletion record with scheduled date
        """
        deletion_id = str(uuid.uuid4())
        now = datetime.utcnow()
        scheduled_date = now + timedelta(days=30)
        
        record = DeletionRecord(
            deletionId=deletion_id,
            userId=user_id,
            requestedAt=now,
            scheduledDeletionDate=scheduled_date,
            status=DeletionStatus.SCHEDULED,
            reason=reason
        )
        
        self._save_deletion_record(record)
        
        return record
    
    def cancel_deletion(self, deletion_id: str) -> bool:
        """
        Cancel a scheduled deletion.
        
        Args:
            deletion_id: Deletion record identifier
            
        Returns:
            True if cancelled, False if not found or already completed
        """
        record = self._load_deletion_record(deletion_id)
        
        if not record or record.status == DeletionStatus.COMPLETED:
            return False
        
        record.status = DeletionStatus.CANCELLED
        self._save_deletion_record(record)
        
        return True
    
    def get_deletion_status(self, user_id: str) -> Optional[DeletionRecord]:
        """
        Get the deletion status for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Deletion record if found, None otherwise
        """
        # Find deletion record for user
        for deletion_file in self.deletion_path.glob("*.json"):
            record = self._load_deletion_record(deletion_file.stem)
            if record and record.userId == user_id and record.status != DeletionStatus.CANCELLED:
                return record
        
        return None
    
    def get_pending_deletions(self) -> List[DeletionRecord]:
        """
        Get all deletion records that are due for processing.
        
        Returns:
            List of deletion records ready for processing
        """
        now = datetime.utcnow()
        pending = []
        
        for deletion_file in self.deletion_path.glob("*.json"):
            record = self._load_deletion_record(deletion_file.stem)
            if record and record.status == DeletionStatus.SCHEDULED:
                if record.scheduledDeletionDate <= now:
                    pending.append(record)
        
        return pending
    
    def mark_deletion_completed(self, deletion_id: str) -> bool:
        """
        Mark a deletion as completed.
        
        Args:
            deletion_id: Deletion record identifier
            
        Returns:
            True if marked completed, False if not found
        """
        record = self._load_deletion_record(deletion_id)
        
        if not record:
            return False
        
        record.status = DeletionStatus.COMPLETED
        record.completedAt = datetime.utcnow()
        self._save_deletion_record(record)
        
        return True
    
    def log_data_access(
        self,
        user_id: str,
        accessed_by: str,
        access_type: str,
        data_fields: List[str],
        purpose: str,
        ip_address: Optional[str] = None
    ) -> DataAccessLog:
        """
        Log data access for audit trail.
        
        Args:
            user_id: User whose data was accessed
            accessed_by: Identifier of accessor (user, service, admin)
            access_type: Type of access (read, update, delete)
            data_fields: List of fields accessed
            purpose: Purpose of access
            ip_address: Optional IP address of accessor
            
        Returns:
            Created access log entry
        """
        log_id = str(uuid.uuid4())
        
        log = DataAccessLog(
            logId=log_id,
            userId=user_id,
            accessedBy=accessed_by,
            accessType=access_type,
            timestamp=datetime.utcnow(),
            dataFields=data_fields,
            purpose=purpose,
            ipAddress=ip_address
        )
        
        self._save_access_log(log)
        
        return log
    
    def get_access_logs(self, user_id: str, limit: int = 100) -> List[DataAccessLog]:
        """
        Get access logs for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of logs to return
            
        Returns:
            List of access logs, most recent first
        """
        logs = []
        
        user_log_dir = self.access_log_path / user_id
        if not user_log_dir.exists():
            return logs
        
        log_files = sorted(user_log_dir.glob("*.json"), reverse=True)
        
        for log_file in log_files[:limit]:
            log = self._load_access_log(log_file)
            if log:
                logs.append(log)
        
        return logs
    
    def get_privacy_settings(self, user_id: str) -> PrivacySettings:
        """
        Get privacy settings for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Privacy settings (creates default if not exists)
        """
        settings = self._load_privacy_settings(user_id)
        
        if not settings:
            # Create default settings
            settings = PrivacySettings(
                userId=user_id,
                consents=[],
                dataRetentionDays=365,
                allowFamilyAccess=True,
                allowDataExport=True
            )
            self._save_privacy_settings(settings)
        
        return settings
    
    def update_privacy_settings(self, settings: PrivacySettings) -> PrivacySettings:
        """
        Update privacy settings for a user.
        
        Args:
            settings: Updated privacy settings
            
        Returns:
            Updated settings
        """
        settings.updatedAt = datetime.utcnow()
        self._save_privacy_settings(settings)
        
        return settings
    
    def update_consent(
        self,
        user_id: str,
        consent_type: PrivacyConsent,
        granted: bool,
        version: str = "1.0"
    ) -> PrivacySettings:
        """
        Update a specific consent for a user.
        
        Args:
            user_id: User identifier
            consent_type: Type of consent
            granted: Whether consent is granted
            version: Version of consent terms
            
        Returns:
            Updated privacy settings
        """
        settings = self.get_privacy_settings(user_id)
        
        # Remove existing consent of same type
        settings.consents = [c for c in settings.consents if c.consentType != consent_type]
        
        # Add new consent
        consent = ConsentRecord(
            consentType=consent_type,
            granted=granted,
            timestamp=datetime.utcnow(),
            version=version
        )
        settings.consents.append(consent)
        
        return self.update_privacy_settings(settings)
    
    def _save_deletion_record(self, record: DeletionRecord) -> None:
        """Save deletion record to storage."""
        file_path = self.deletion_path / f"{record.deletionId}.json"
        file_path.write_text(record.model_dump_json(indent=2))
    
    def _load_deletion_record(self, deletion_id: str) -> Optional[DeletionRecord]:
        """Load deletion record from storage."""
        file_path = self.deletion_path / f"{deletion_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            data = json.loads(file_path.read_text())
            return DeletionRecord(**data)
        except Exception as e:
            print(f"Error loading deletion record {deletion_id}: {e}")
            return None
    
    def _save_access_log(self, log: DataAccessLog) -> None:
        """Save access log to storage."""
        user_log_dir = self.access_log_path / log.userId
        user_log_dir.mkdir(exist_ok=True)
        
        file_path = user_log_dir / f"{log.logId}.json"
        file_path.write_text(log.model_dump_json(indent=2))
    
    def _load_access_log(self, file_path: Path) -> Optional[DataAccessLog]:
        """Load access log from storage."""
        try:
            data = json.loads(file_path.read_text())
            return DataAccessLog(**data)
        except Exception as e:
            print(f"Error loading access log {file_path}: {e}")
            return None
    
    def _save_privacy_settings(self, settings: PrivacySettings) -> None:
        """Save privacy settings to storage."""
        file_path = self.settings_path / f"{settings.userId}.json"
        file_path.write_text(settings.model_dump_json(indent=2))
    
    def _load_privacy_settings(self, user_id: str) -> Optional[PrivacySettings]:
        """Load privacy settings from storage."""
        file_path = self.settings_path / f"{user_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            data = json.loads(file_path.read_text())
            return PrivacySettings(**data)
        except Exception as e:
            print(f"Error loading privacy settings {user_id}: {e}")
            return None
