"""
Data models for user profile management.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class CasteCategory(str, Enum):
    GENERAL = "general"
    OBC = "obc"
    SC = "sc"
    ST = "st"
    EWS = "ews"


class Religion(str, Enum):
    HINDU = "hindu"
    MUSLIM = "muslim"
    CHRISTIAN = "christian"
    SIKH = "sikh"
    BUDDHIST = "buddhist"
    JAIN = "jain"
    OTHER = "other"


class Occupation(str, Enum):
    FARMER = "farmer"
    AGRICULTURAL_LABORER = "agricultural_laborer"
    DAILY_WAGE_WORKER = "daily_wage_worker"
    SELF_EMPLOYED = "self_employed"
    GOVERNMENT_EMPLOYEE = "government_employee"
    PRIVATE_EMPLOYEE = "private_employee"
    UNEMPLOYED = "unemployed"
    STUDENT = "student"
    RETIRED = "retired"
    OTHER = "other"


class LanguageCode(str, Enum):
    HI = "hi"  # Hindi
    BN = "bn"  # Bengali
    TE = "te"  # Telugu
    MR = "mr"  # Marathi
    TA = "ta"  # Tamil
    GU = "gu"  # Gujarati
    KN = "kn"  # Kannada
    ML = "ml"  # Malayalam
    OR = "or"  # Odia
    PA = "pa"  # Punjabi
    AS = "as"  # Assamese
    UR = "ur"  # Urdu
    EN = "en"  # English


class DialectCode(str, Enum):
    STANDARD = "standard"
    REGIONAL = "regional"


class CommunicationMode(str, Enum):
    VOICE = "voice"
    TEXT = "text"
    MULTIMODAL = "multimodal"


class LandDetails(BaseModel):
    owned: bool
    areaInAcres: float = Field(ge=0)
    irrigated: bool


class BankDetails(BaseModel):
    hasAccount: bool
    accountNumber: Optional[str] = None
    ifscCode: Optional[str] = None
    bankName: Optional[str] = None
    
    @field_validator('ifscCode')
    @classmethod
    def validate_ifsc(cls, v):
        if v and len(v) != 11:
            raise ValueError('IFSC code must be 11 characters')
        return v


class ApplicationRecord(BaseModel):
    applicationId: str
    schemeId: str
    schemeName: str
    submittedDate: datetime
    status: str
    lastUpdated: datetime


class PersonalInfo(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    age: int = Field(ge=0, le=150)
    gender: Gender
    phoneNumber: str = Field(pattern=r'^\+?[1-9]\d{9,14}$')
    aadhaarNumber: Optional[str] = Field(None, pattern=r'^\d{12}$')


class Demographics(BaseModel):
    state: str = Field(min_length=1, max_length=100)
    district: str = Field(min_length=1, max_length=100)
    block: str = Field(min_length=1, max_length=100)
    village: str = Field(min_length=1, max_length=100)
    caste: CasteCategory
    religion: Religion
    familySize: int = Field(ge=1, le=50)


class Economic(BaseModel):
    annualIncome: float = Field(ge=0)
    occupation: Occupation
    landOwnership: LandDetails
    bankAccount: BankDetails


class Preferences(BaseModel):
    preferredLanguage: LanguageCode
    preferredDialect: DialectCode
    communicationMode: CommunicationMode


class UserProfile(BaseModel):
    userId: str
    personalInfo: PersonalInfo
    demographics: Demographics
    economic: Economic
    preferences: Preferences
    applicationHistory: List[ApplicationRecord] = Field(default_factory=list)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)


class CreateUserProfileRequest(BaseModel):
    personalInfo: PersonalInfo
    demographics: Demographics
    economic: Economic
    preferences: Preferences


class UpdateUserProfileRequest(BaseModel):
    userId: str
    personalInfo: Optional[PersonalInfo] = None
    demographics: Optional[Demographics] = None
    economic: Optional[Economic] = None
    preferences: Optional[Preferences] = None


class UserProfileResponse(BaseModel):
    success: bool
    profile: Optional[UserProfile] = None
    error: Optional[str] = None


class VoiceUpdateRequest(BaseModel):
    userId: str
    naturalLanguageUpdate: str
    confirmationRequired: bool = True


class VoiceUpdateResponse(BaseModel):
    success: bool
    parsedUpdates: Optional[dict] = None
    confirmationMessage: Optional[str] = None
    requiresConfirmation: bool = False
    error: Optional[str] = None


class DataDeletionRequest(BaseModel):
    userId: str
    reason: Optional[str] = None


class DataDeletionResponse(BaseModel):
    success: bool
    scheduledDeletionDate: Optional[datetime] = None
    confirmationId: Optional[str] = None
    error: Optional[str] = None


class DeletionStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DeletionRecord(BaseModel):
    deletionId: str
    userId: str
    requestedAt: datetime
    scheduledDeletionDate: datetime
    status: DeletionStatus
    reason: Optional[str] = None
    completedAt: Optional[datetime] = None


class FamilyMemberProfile(BaseModel):
    memberId: str
    primaryUserId: str
    relationship: str
    personalInfo: PersonalInfo
    demographics: Demographics
    economic: Economic
    preferences: Preferences
    applicationHistory: List[ApplicationRecord] = Field(default_factory=list)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)


class CreateFamilyMemberRequest(BaseModel):
    primaryUserId: str
    relationship: str
    personalInfo: PersonalInfo
    demographics: Demographics
    economic: Economic
    preferences: Preferences


class PrivacyConsent(str, Enum):
    DATA_COLLECTION = "data_collection"
    DATA_SHARING = "data_sharing"
    MARKETING = "marketing"
    ANALYTICS = "analytics"


class ConsentRecord(BaseModel):
    consentType: PrivacyConsent
    granted: bool
    timestamp: datetime
    version: str = "1.0"


class DataAccessLog(BaseModel):
    logId: str
    userId: str
    accessedBy: str
    accessType: str
    timestamp: datetime
    dataFields: List[str]
    purpose: str
    ipAddress: Optional[str] = None


class PrivacySettings(BaseModel):
    userId: str
    consents: List[ConsentRecord] = Field(default_factory=list)
    dataRetentionDays: int = 365
    allowFamilyAccess: bool = True
    allowDataExport: bool = True
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
