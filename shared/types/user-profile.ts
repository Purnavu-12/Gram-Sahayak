/**
 * User Profile type definitions for Gram Sahayak
 */

export enum Gender {
  MALE = 'male',
  FEMALE = 'female',
  OTHER = 'other'
}

export enum CasteCategory {
  GENERAL = 'general',
  OBC = 'obc',
  SC = 'sc',
  ST = 'st',
  EWS = 'ews'
}

export enum Religion {
  HINDU = 'hindu',
  MUSLIM = 'muslim',
  CHRISTIAN = 'christian',
  SIKH = 'sikh',
  BUDDHIST = 'buddhist',
  JAIN = 'jain',
  OTHER = 'other'
}

export enum Occupation {
  FARMER = 'farmer',
  AGRICULTURAL_LABORER = 'agricultural_laborer',
  DAILY_WAGE_WORKER = 'daily_wage_worker',
  SELF_EMPLOYED = 'self_employed',
  GOVERNMENT_EMPLOYEE = 'government_employee',
  PRIVATE_EMPLOYEE = 'private_employee',
  UNEMPLOYED = 'unemployed',
  STUDENT = 'student',
  RETIRED = 'retired',
  OTHER = 'other'
}

export enum LanguageCode {
  HI = 'hi', // Hindi
  BN = 'bn', // Bengali
  TE = 'te', // Telugu
  MR = 'mr', // Marathi
  TA = 'ta', // Tamil
  GU = 'gu', // Gujarati
  KN = 'kn', // Kannada
  ML = 'ml', // Malayalam
  OR = 'or', // Odia
  PA = 'pa', // Punjabi
  AS = 'as', // Assamese
  UR = 'ur', // Urdu
  EN = 'en'  // English
}

export enum DialectCode {
  STANDARD = 'standard',
  REGIONAL = 'regional'
}

export enum CommunicationMode {
  VOICE = 'voice',
  TEXT = 'text',
  MULTIMODAL = 'multimodal'
}

export interface LandDetails {
  owned: boolean;
  areaInAcres: number;
  irrigated: boolean;
}

export interface BankDetails {
  hasAccount: boolean;
  accountNumber?: string;
  ifscCode?: string;
  bankName?: string;
}

export interface ApplicationRecord {
  applicationId: string;
  schemeId: string;
  schemeName: string;
  submittedDate: Date;
  status: string;
  lastUpdated: Date;
}

export interface PersonalInfo {
  name: string;
  age: number;
  gender: Gender;
  phoneNumber: string;
  aadhaarNumber?: string;
}

export interface Demographics {
  state: string;
  district: string;
  block: string;
  village: string;
  caste: CasteCategory;
  religion: Religion;
  familySize: number;
}

export interface Economic {
  annualIncome: number;
  occupation: Occupation;
  landOwnership: LandDetails;
  bankAccount: BankDetails;
}

export interface Preferences {
  preferredLanguage: LanguageCode;
  preferredDialect: DialectCode;
  communicationMode: CommunicationMode;
}

export interface UserProfile {
  userId: string;
  personalInfo: PersonalInfo;
  demographics: Demographics;
  economic: Economic;
  preferences: Preferences;
  applicationHistory: ApplicationRecord[];
  createdAt: Date;
  updatedAt: Date;
}

export interface CreateUserProfileRequest {
  personalInfo: PersonalInfo;
  demographics: Demographics;
  economic: Economic;
  preferences: Preferences;
}

export interface UpdateUserProfileRequest {
  userId: string;
  personalInfo?: Partial<PersonalInfo>;
  demographics?: Partial<Demographics>;
  economic?: Partial<Economic>;
  preferences?: Partial<Preferences>;
}

export interface UserProfileResponse {
  success: boolean;
  profile?: UserProfile;
  error?: string;
}
