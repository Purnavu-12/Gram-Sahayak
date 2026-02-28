"""
User Profile Service API
Provides secure user profile management with encryption.
"""

import os
import logging
import json
import re
from typing import List
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from models import (
    CreateUserProfileRequest,
    UpdateUserProfileRequest,
    UserProfileResponse,
    UserProfile,
    VoiceUpdateRequest,
    VoiceUpdateResponse,
    DataDeletionRequest,
    DataDeletionResponse,
    DeletionRecord,
    CreateFamilyMemberRequest,
    FamilyMemberProfile,
    PrivacySettings,
    PrivacyConsent,
    DataAccessLog
)
from storage import UserProfileStorage
from voice_updates import VoiceUpdateParser
from privacy_manager import PrivacyManager
from family_manager import FamilyManager


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": "user-profile",
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

app = FastAPI(
    title="User Profile Service",
    description="Secure user profile management for Gram Sahayak",
    version="1.0.0"
)

# CORS middleware
allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


def sanitize_string(value: str) -> str:
    """Remove HTML tags and limit length for input sanitization."""
    if not value:
        return value
    clean = re.sub(r'<[^>]+>', '', value)
    return clean[:10000]

# Initialize services
encryption_key = os.getenv("ENCRYPTION_KEY")
storage = UserProfileStorage(
    storage_path=os.getenv("STORAGE_PATH", "./data/profiles"),
    encryption_key=encryption_key
)
voice_parser = VoiceUpdateParser()
privacy_manager = PrivacyManager(storage_path=os.getenv("PRIVACY_PATH", "./data/privacy"))
family_manager = FamilyManager(
    storage_path=os.getenv("FAMILY_PATH", "./data/family"),
    encryption_key=encryption_key
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "user-profile"}


@app.post("/profiles", response_model=UserProfileResponse)
async def create_profile(request: CreateUserProfileRequest):
    """
    Create a new user profile with encrypted storage.
    
    Args:
        request: Profile creation request
        
    Returns:
        Created user profile
    """
    try:
        profile = storage.create_profile(request)
        return UserProfileResponse(success=True, profile=profile)
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/profiles/{user_id}", response_model=UserProfileResponse)
async def get_profile(user_id: str):
    """
    Retrieve a user profile by ID.
    
    Args:
        user_id: User identifier
        
    Returns:
        User profile if found
    """
    profile = storage.get_profile(user_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Log data access
    privacy_manager.log_data_access(
        user_id=user_id,
        accessed_by="api",
        access_type="read",
        data_fields=["profile"],
        purpose="Profile retrieval"
    )
    
    return UserProfileResponse(success=True, profile=profile)


@app.put("/profiles", response_model=UserProfileResponse)
async def update_profile(request: UpdateUserProfileRequest):
    """
    Update an existing user profile.
    
    Args:
        request: Profile update request
        
    Returns:
        Updated user profile
    """
    profile = storage.update_profile(request)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return UserProfileResponse(success=True, profile=profile)


@app.delete("/profiles/{user_id}")
async def delete_profile(user_id: str):
    """
    Delete a user profile permanently.
    
    Args:
        user_id: User identifier
        
    Returns:
        Success status
    """
    success = storage.delete_profile(user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return {"success": True, "message": "Profile deleted successfully"}


@app.get("/profiles/recognize/{phone_number}", response_model=UserProfileResponse)
async def recognize_user(phone_number: str):
    """
    Recognize a user by phone number and load their profile.
    
    Args:
        phone_number: User's phone number
        
    Returns:
        User profile if found
    """
    profile = storage.recognize_user(phone_number)
    
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserProfileResponse(success=True, profile=profile)


@app.post("/profiles/voice-update", response_model=VoiceUpdateResponse)
async def voice_update_profile(request: VoiceUpdateRequest):
    """
    Update user profile using natural language voice input.
    
    Args:
        request: Voice update request with natural language
        
    Returns:
        Parsed updates and confirmation message
    """
    try:
        # Get current profile
        profile = storage.get_profile(request.userId)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Parse natural language update
        sanitized_input = sanitize_string(request.naturalLanguageUpdate)
        updates = voice_parser.parse_update(sanitized_input, profile)
        
        if not updates:
            return VoiceUpdateResponse(
                success=False,
                error="Could not understand the update request"
            )
        
        # Generate confirmation message
        confirmation = voice_parser.generate_confirmation_message(updates)
        
        # If confirmation required, return parsed updates for user approval
        if request.confirmationRequired:
            return VoiceUpdateResponse(
                success=True,
                parsedUpdates=updates,
                confirmationMessage=confirmation,
                requiresConfirmation=True
            )
        
        # Apply updates directly
        updated_profile = voice_parser.apply_updates(profile, updates)
        storage.update_profile(UpdateUserProfileRequest(
            userId=request.userId,
            personalInfo=updated_profile.personalInfo,
            demographics=updated_profile.demographics,
            economic=updated_profile.economic,
            preferences=updated_profile.preferences
        ))
        
        # Log data access
        privacy_manager.log_data_access(
            user_id=request.userId,
            accessed_by="voice_update_system",
            access_type="update",
            data_fields=list(updates.keys()),
            purpose="Voice-based profile update"
        )
        
        return VoiceUpdateResponse(
            success=True,
            parsedUpdates=updates,
            confirmationMessage="Profile updated successfully"
        )
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/profiles/voice-update/confirm")
async def confirm_voice_update(user_id: str, updates: dict):
    """
    Confirm and apply voice-based profile updates.
    
    Args:
        user_id: User identifier
        updates: Parsed updates to apply
        
    Returns:
        Success status
    """
    try:
        profile = storage.get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Apply updates
        updated_profile = voice_parser.apply_updates(profile, updates)
        storage.update_profile(UpdateUserProfileRequest(
            userId=user_id,
            personalInfo=updated_profile.personalInfo,
            demographics=updated_profile.demographics,
            economic=updated_profile.economic,
            preferences=updated_profile.preferences
        ))
        
        # Log data access
        privacy_manager.log_data_access(
            user_id=user_id,
            accessed_by="voice_update_system",
            access_type="update",
            data_fields=list(updates.keys()),
            purpose="Confirmed voice-based profile update"
        )
        
        return {"success": True, "message": "Profile updated successfully"}
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/profiles/deletion/schedule", response_model=DataDeletionResponse)
async def schedule_data_deletion(request: DataDeletionRequest):
    """
    Schedule complete data deletion with 30-day compliance.
    
    Args:
        request: Data deletion request
        
    Returns:
        Deletion record with scheduled date
    """
    try:
        # Verify profile exists
        profile = storage.get_profile(request.userId)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Schedule deletion
        deletion_record = privacy_manager.schedule_deletion(request.userId, request.reason)
        
        # Log data access
        privacy_manager.log_data_access(
            user_id=request.userId,
            accessed_by="deletion_system",
            access_type="delete",
            data_fields=["all"],
            purpose="Data deletion scheduled"
        )
        
        return DataDeletionResponse(
            success=True,
            scheduledDeletionDate=deletion_record.scheduledDeletionDate,
            confirmationId=deletion_record.deletionId
        )
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/profiles/deletion/status/{user_id}")
async def get_deletion_status(user_id: str):
    """
    Get deletion status for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Deletion record if scheduled
    """
    deletion_record = privacy_manager.get_deletion_status(user_id)
    
    if not deletion_record:
        return {"scheduled": False}
    
    return {
        "scheduled": True,
        "deletionId": deletion_record.deletionId,
        "scheduledDate": deletion_record.scheduledDeletionDate,
        "status": deletion_record.status
    }


@app.post("/profiles/deletion/cancel/{deletion_id}")
async def cancel_deletion(deletion_id: str):
    """
    Cancel a scheduled deletion.
    
    Args:
        deletion_id: Deletion record identifier
        
    Returns:
        Success status
    """
    success = privacy_manager.cancel_deletion(deletion_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Deletion record not found or already completed")
    
    return {"success": True, "message": "Deletion cancelled successfully"}


@app.post("/profiles/deletion/process")
async def process_pending_deletions():
    """
    Process all pending deletions that are due.
    This endpoint should be called by a scheduled job.
    
    Returns:
        Number of profiles deleted
    """
    try:
        pending = privacy_manager.get_pending_deletions()
        deleted_count = 0
        
        for deletion_record in pending:
            # Delete user profile
            if storage.delete_profile(deletion_record.userId):
                # Delete family members
                family_manager.delete_all_family_members(deletion_record.userId)
                
                # Mark deletion as completed
                privacy_manager.mark_deletion_completed(deletion_record.deletionId)
                deleted_count += 1
        
        return {
            "success": True,
            "deletedCount": deleted_count,
            "message": f"Processed {deleted_count} pending deletions"
        }
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/profiles/{user_id}/family", response_model=FamilyMemberProfile)
async def create_family_member(user_id: str, request: CreateFamilyMemberRequest):
    """
    Create a family member profile under a primary user.
    
    Args:
        user_id: Primary user identifier
        request: Family member creation request
        
    Returns:
        Created family member profile
    """
    try:
        # Verify primary user exists
        profile = storage.get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Primary user not found")
        
        # Ensure request has correct primary user ID
        request.primaryUserId = user_id
        
        # Create family member
        member = family_manager.create_family_member(request)
        
        # Log data access
        privacy_manager.log_data_access(
            user_id=user_id,
            accessed_by="family_management_system",
            access_type="create",
            data_fields=["family_member"],
            purpose="Family member profile created"
        )
        
        return member
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/profiles/{user_id}/family", response_model=List[FamilyMemberProfile])
async def get_family_members(user_id: str):
    """
    Get all family members for a primary user.
    
    Args:
        user_id: Primary user identifier
        
    Returns:
        List of family member profiles
    """
    # Verify primary user exists
    profile = storage.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Primary user not found")
    
    members = family_manager.get_family_members(user_id)
    
    # Log data access
    privacy_manager.log_data_access(
        user_id=user_id,
        accessed_by="family_management_system",
        access_type="read",
        data_fields=["family_members"],
        purpose="Family members retrieved"
    )
    
    return members


@app.get("/profiles/family/{member_id}", response_model=FamilyMemberProfile)
async def get_family_member(member_id: str):
    """
    Get a specific family member profile.
    
    Args:
        member_id: Family member identifier
        
    Returns:
        Family member profile
    """
    member = family_manager.get_family_member(member_id)
    
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")
    
    # Log data access
    privacy_manager.log_data_access(
        user_id=member.primaryUserId,
        accessed_by="family_management_system",
        access_type="read",
        data_fields=["family_member"],
        purpose="Family member profile retrieved"
    )
    
    return member


@app.delete("/profiles/family/{member_id}")
async def delete_family_member(member_id: str):
    """
    Delete a family member profile.
    
    Args:
        member_id: Family member identifier
        
    Returns:
        Success status
    """
    member = family_manager.get_family_member(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")
    
    success = family_manager.delete_family_member(member_id)
    
    if success:
        # Log data access
        privacy_manager.log_data_access(
            user_id=member.primaryUserId,
            accessed_by="family_management_system",
            access_type="delete",
            data_fields=["family_member"],
            purpose="Family member profile deleted"
        )
    
    return {"success": success, "message": "Family member deleted successfully"}


@app.get("/profiles/{user_id}/privacy", response_model=PrivacySettings)
async def get_privacy_settings(user_id: str):
    """
    Get privacy settings for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Privacy settings
    """
    # Verify user exists
    profile = storage.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    settings = privacy_manager.get_privacy_settings(user_id)
    
    return settings


@app.put("/profiles/{user_id}/privacy", response_model=PrivacySettings)
async def update_privacy_settings(user_id: str, settings: PrivacySettings):
    """
    Update privacy settings for a user.
    
    Args:
        user_id: User identifier
        settings: Updated privacy settings
        
    Returns:
        Updated privacy settings
    """
    # Verify user exists
    profile = storage.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Ensure user ID matches
    settings.userId = user_id
    
    updated_settings = privacy_manager.update_privacy_settings(settings)
    
    # Log data access
    privacy_manager.log_data_access(
        user_id=user_id,
        accessed_by="privacy_management_system",
        access_type="update",
        data_fields=["privacy_settings"],
        purpose="Privacy settings updated"
    )
    
    return updated_settings


@app.post("/profiles/{user_id}/privacy/consent")
async def update_consent(
    user_id: str,
    consent_type: PrivacyConsent,
    granted: bool,
    version: str = "1.0"
):
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
    # Verify user exists
    profile = storage.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    settings = privacy_manager.update_consent(user_id, consent_type, granted, version)
    
    # Log data access
    privacy_manager.log_data_access(
        user_id=user_id,
        accessed_by="privacy_management_system",
        access_type="update",
        data_fields=["consent"],
        purpose=f"Consent updated: {consent_type.value}"
    )
    
    return settings


@app.get("/profiles/{user_id}/access-logs", response_model=List[DataAccessLog])
async def get_access_logs(user_id: str, limit: int = 100, request: Request = None):
    """
    Get data access logs for a user.
    
    Args:
        user_id: User identifier
        limit: Maximum number of logs to return
        
    Returns:
        List of access logs
    """
    # Verify user exists
    profile = storage.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    logs = privacy_manager.get_access_logs(user_id, limit)
    
    # Log this access
    ip_address = request.client.host if request and request.client else None
    privacy_manager.log_data_access(
        user_id=user_id,
        accessed_by="user",
        access_type="read",
        data_fields=["access_logs"],
        purpose="User viewed access logs",
        ip_address=ip_address
    )
    
    return logs


@app.get("/profiles/{user_id}/export")
async def export_user_data(user_id: str, include_access_logs: bool = True, request: Request = None):
    """
    Export all user data for transparency and portability.
    
    Args:
        user_id: User identifier
        include_access_logs: Whether to include access logs in export
        
    Returns:
        Complete user data export
    """
    # Verify user exists
    profile = storage.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user allows data export
    settings = privacy_manager.get_privacy_settings(user_id)
    if not settings.allowDataExport:
        raise HTTPException(status_code=403, detail="Data export is disabled for this user")
    
    # Get family members
    family_members = family_manager.get_family_members(user_id)
    
    # Export data
    export_data = privacy_manager.export_user_data(
        user_id=user_id,
        profile=profile,
        family_members=family_members,
        include_access_logs=include_access_logs
    )
    
    # Log this access
    ip_address = request.client.host if request else None
    privacy_manager.log_data_access(
        user_id=user_id,
        accessed_by="user",
        access_type="read",
        data_fields=["all"],
        purpose="User exported data",
        ip_address=ip_address
    )
    
    return export_data


@app.post("/profiles/{user_id}/retention/enforce")
async def enforce_retention_policy(user_id: str):
    """
    Enforce data retention policy for a specific user.
    Cleans up old data based on user's retention settings.
    
    Args:
        user_id: User identifier
        
    Returns:
        Cleanup statistics
    """
    # Verify user exists
    profile = storage.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    cleanup_stats = privacy_manager.enforce_retention_policy(user_id)
    
    # Log this action
    privacy_manager.log_data_access(
        user_id=user_id,
        accessed_by="retention_system",
        access_type="delete",
        data_fields=["old_data"],
        purpose="Retention policy enforcement"
    )
    
    return {
        "success": True,
        "userId": user_id,
        "cleanupStats": cleanup_stats
    }


@app.post("/admin/retention/enforce-all")
async def enforce_retention_policy_all():
    """
    Enforce data retention policy for all users.
    This endpoint should be called by a scheduled job.
    
    Returns:
        Overall cleanup statistics
    """
    try:
        user_ids = privacy_manager.get_all_users_for_retention_cleanup()
        
        total_stats = {
            "usersProcessed": 0,
            "totalAccessLogsDeleted": 0,
            "totalDeletionRecordsRemoved": 0
        }
        
        for user_id in user_ids:
            # Check if user still exists
            if storage.get_profile(user_id):
                cleanup_stats = privacy_manager.enforce_retention_policy(user_id)
                total_stats["usersProcessed"] += 1
                total_stats["totalAccessLogsDeleted"] += cleanup_stats["accessLogsDeleted"]
                total_stats["totalDeletionRecordsRemoved"] += cleanup_stats["oldDeletionRecordsRemoved"]
        
        return {
            "success": True,
            "stats": total_stats
        }
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/profiles/{user_id}/privacy/dashboard")
async def get_privacy_dashboard(user_id: str):
    """
    Get comprehensive privacy control dashboard data for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Privacy dashboard with settings, deletion status, and recent access logs
    """
    # Verify user exists
    profile = storage.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get privacy settings
    settings = privacy_manager.get_privacy_settings(user_id)
    
    # Get deletion status
    deletion_status = privacy_manager.get_deletion_status(user_id)
    
    # Get recent access logs
    recent_logs = privacy_manager.get_access_logs(user_id, limit=10)
    
    # Get family members count
    family_members = family_manager.get_family_members(user_id)
    
    dashboard = {
        "userId": user_id,
        "privacySettings": settings,
        "deletionStatus": deletion_status,
        "recentAccessLogs": recent_logs,
        "familyMembersCount": len(family_members),
        "dataExportAvailable": settings.allowDataExport,
        "accountCreatedAt": profile.createdAt,
        "lastUpdatedAt": profile.updatedAt
    }
    
    return dashboard


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
