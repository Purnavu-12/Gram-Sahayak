"""
User Profile Service API
Provides secure user profile management with encryption.
"""

import os
from typing import List
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

app = FastAPI(
    title="User Profile Service",
    description="Secure user profile management for Gram Sahayak",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        raise HTTPException(status_code=500, detail=str(e))


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
        updates = voice_parser.parse_update(request.naturalLanguageUpdate, profile)
        
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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
    ip_address = request.client.host if request else None
    privacy_manager.log_data_access(
        user_id=user_id,
        accessed_by="user",
        access_type="read",
        data_fields=["access_logs"],
        purpose="User viewed access logs",
        ip_address=ip_address
    )
    
    return logs


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
