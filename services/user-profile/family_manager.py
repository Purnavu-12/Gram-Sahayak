"""
Family member profile management.
Handles separate profiles for family members under a primary user account.
"""

import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

from encryption import EncryptionService
from models import (
    FamilyMemberProfile,
    CreateFamilyMemberRequest,
    PersonalInfo,
    Demographics,
    Economic,
    Preferences
)


class FamilyManager:
    """Manages family member profiles with separation and unique identifiers."""
    
    def __init__(self, storage_path: str = "./data/family", encryption_key: Optional[str] = None):
        """
        Initialize family manager.
        
        Args:
            storage_path: Directory for family member profiles
            encryption_key: Encryption key for secure storage
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.encryption_service = EncryptionService(encryption_key)
        self._cache: Dict[str, FamilyMemberProfile] = {}
    
    def create_family_member(self, request: CreateFamilyMemberRequest) -> FamilyMemberProfile:
        """
        Create a new family member profile.
        
        Args:
            request: Family member creation request
            
        Returns:
            Created family member profile
        """
        member_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        profile = FamilyMemberProfile(
            memberId=member_id,
            primaryUserId=request.primaryUserId,
            relationship=request.relationship,
            personalInfo=request.personalInfo,
            demographics=request.demographics,
            economic=request.economic,
            preferences=request.preferences,
            applicationHistory=[],
            createdAt=now,
            updatedAt=now
        )
        
        self._save_member(profile)
        self._cache[member_id] = profile
        
        return profile
    
    def get_family_member(self, member_id: str) -> Optional[FamilyMemberProfile]:
        """
        Get a family member profile by ID.
        
        Args:
            member_id: Family member identifier
            
        Returns:
            Family member profile if found, None otherwise
        """
        # Check cache first
        if member_id in self._cache:
            return self._cache[member_id]
        
        # Load from storage
        profile = self._load_member(member_id)
        if profile:
            self._cache[member_id] = profile
        
        return profile
    
    def get_family_members(self, primary_user_id: str) -> List[FamilyMemberProfile]:
        """
        Get all family members for a primary user.
        
        Args:
            primary_user_id: Primary user identifier
            
        Returns:
            List of family member profiles
        """
        members = []
        
        for member_file in self.storage_path.glob("*.enc"):
            member_id = member_file.stem
            profile = self.get_family_member(member_id)
            
            if profile and profile.primaryUserId == primary_user_id:
                members.append(profile)
        
        return members
    
    def update_family_member(
        self,
        member_id: str,
        personal_info: Optional[PersonalInfo] = None,
        demographics: Optional[Demographics] = None,
        economic: Optional[Economic] = None,
        preferences: Optional[Preferences] = None
    ) -> Optional[FamilyMemberProfile]:
        """
        Update a family member profile.
        
        Args:
            member_id: Family member identifier
            personal_info: Updated personal information
            demographics: Updated demographics
            economic: Updated economic information
            preferences: Updated preferences
            
        Returns:
            Updated profile if found, None otherwise
        """
        profile = self.get_family_member(member_id)
        
        if not profile:
            return None
        
        # Update fields if provided
        if personal_info:
            profile.personalInfo = personal_info
        if demographics:
            profile.demographics = demographics
        if economic:
            profile.economic = economic
        if preferences:
            profile.preferences = preferences
        
        profile.updatedAt = datetime.utcnow()
        
        self._save_member(profile)
        self._cache[member_id] = profile
        
        return profile
    
    def delete_family_member(self, member_id: str) -> bool:
        """
        Delete a family member profile.
        
        Args:
            member_id: Family member identifier
            
        Returns:
            True if deleted, False if not found
        """
        member_file = self.storage_path / f"{member_id}.enc"
        
        if not member_file.exists():
            return False
        
        member_file.unlink()
        self._cache.pop(member_id, None)
        
        return True
    
    def delete_all_family_members(self, primary_user_id: str) -> int:
        """
        Delete all family members for a primary user.
        
        Args:
            primary_user_id: Primary user identifier
            
        Returns:
            Number of family members deleted
        """
        members = self.get_family_members(primary_user_id)
        count = 0
        
        for member in members:
            if self.delete_family_member(member.memberId):
                count += 1
        
        return count
    
    def _save_member(self, profile: FamilyMemberProfile) -> None:
        """
        Save family member profile to encrypted storage.
        
        Args:
            profile: Family member profile to save
        """
        # Convert to JSON
        profile_json = profile.model_dump_json()
        
        # Encrypt
        encrypted_data = self.encryption_service.encrypt(profile_json)
        
        # Save to file
        member_file = self.storage_path / f"{profile.memberId}.enc"
        member_file.write_text(encrypted_data)
    
    def _load_member(self, member_id: str) -> Optional[FamilyMemberProfile]:
        """
        Load family member profile from encrypted storage.
        
        Args:
            member_id: Family member identifier
            
        Returns:
            Family member profile if found and valid, None otherwise
        """
        member_file = self.storage_path / f"{member_id}.enc"
        
        if not member_file.exists():
            return None
        
        try:
            # Read encrypted data
            encrypted_data = member_file.read_text()
            
            # Decrypt
            profile_json = self.encryption_service.decrypt(encrypted_data)
            
            # Parse JSON
            profile_dict = json.loads(profile_json)
            
            # Convert to FamilyMemberProfile
            return FamilyMemberProfile(**profile_dict)
        except Exception as e:
            print(f"Error loading family member {member_id}: {e}")
            return None
