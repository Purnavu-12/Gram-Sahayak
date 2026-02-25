"""
Secure storage service for user profiles with encryption.
"""

import json
import uuid
from datetime import datetime
from typing import Optional, Dict
from pathlib import Path

from encryption import EncryptionService
from models import UserProfile, CreateUserProfileRequest, UpdateUserProfileRequest


class UserProfileStorage:
    """Service for storing and retrieving encrypted user profiles."""
    
    def __init__(self, storage_path: str = "./data/profiles", encryption_key: Optional[str] = None):
        """
        Initialize storage service.
        
        Args:
            storage_path: Directory path for storing encrypted profiles
            encryption_key: Base64-encoded encryption key. If None, generates new key.
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.encryption_service = EncryptionService(encryption_key)
        self._profile_cache: Dict[str, UserProfile] = {}
    
    def create_profile(self, request: CreateUserProfileRequest) -> UserProfile:
        """
        Create a new user profile with encrypted storage.
        
        Args:
            request: Profile creation request
            
        Returns:
            Created user profile
        """
        user_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        profile = UserProfile(
            userId=user_id,
            personalInfo=request.personalInfo,
            demographics=request.demographics,
            economic=request.economic,
            preferences=request.preferences,
            applicationHistory=[],
            createdAt=now,
            updatedAt=now
        )
        
        self._save_profile(profile)
        self._profile_cache[user_id] = profile
        
        return profile
    
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Retrieve a user profile by ID.
        
        Args:
            user_id: User identifier
            
        Returns:
            User profile if found, None otherwise
        """
        # Check cache first
        if user_id in self._profile_cache:
            return self._profile_cache[user_id]
        
        # Load from storage
        profile = self._load_profile(user_id)
        if profile:
            self._profile_cache[user_id] = profile
        
        return profile
    
    def update_profile(self, request: UpdateUserProfileRequest) -> Optional[UserProfile]:
        """
        Update an existing user profile.
        
        Args:
            request: Profile update request
            
        Returns:
            Updated profile if found, None otherwise
        """
        profile = self.get_profile(request.userId)
        if not profile:
            return None
        
        # Update fields if provided
        if request.personalInfo:
            profile.personalInfo = request.personalInfo
        if request.demographics:
            profile.demographics = request.demographics
        if request.economic:
            profile.economic = request.economic
        if request.preferences:
            profile.preferences = request.preferences
        
        profile.updatedAt = datetime.utcnow()
        
        self._save_profile(profile)
        self._profile_cache[request.userId] = profile
        
        return profile
    
    def delete_profile(self, user_id: str) -> bool:
        """
        Delete a user profile permanently.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if deleted, False if not found
        """
        profile_file = self.storage_path / f"{user_id}.enc"
        
        if not profile_file.exists():
            return False
        
        profile_file.unlink()
        self._profile_cache.pop(user_id, None)
        
        return True
    
    def recognize_user(self, phone_number: str) -> Optional[UserProfile]:
        """
        Recognize a user by phone number and load their profile.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            User profile if found, None otherwise
        """
        # Scan all profiles to find matching phone number
        for profile_file in self.storage_path.glob("*.enc"):
            user_id = profile_file.stem
            profile = self.get_profile(user_id)
            
            if profile and profile.personalInfo.phoneNumber == phone_number:
                return profile
        
        return None
    
    def _save_profile(self, profile: UserProfile) -> None:
        """
        Save profile to encrypted storage.
        
        Args:
            profile: User profile to save
        """
        # Convert to JSON
        profile_json = profile.model_dump_json()
        
        # Encrypt
        encrypted_data = self.encryption_service.encrypt(profile_json)
        
        # Save to file
        profile_file = self.storage_path / f"{profile.userId}.enc"
        profile_file.write_text(encrypted_data)
    
    def _load_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Load profile from encrypted storage.
        
        Args:
            user_id: User identifier
            
        Returns:
            User profile if found and valid, None otherwise
        """
        profile_file = self.storage_path / f"{user_id}.enc"
        
        if not profile_file.exists():
            return None
        
        try:
            # Read encrypted data
            encrypted_data = profile_file.read_text()
            
            # Decrypt
            profile_json = self.encryption_service.decrypt(encrypted_data)
            
            # Parse JSON
            profile_dict = json.loads(profile_json)
            
            # Convert to UserProfile
            return UserProfile(**profile_dict)
        except Exception as e:
            print(f"Error loading profile {user_id}: {e}")
            return None
