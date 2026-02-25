/**
 * Core interfaces for Scheme Matching Service
 * Handles government scheme discovery and eligibility matching
 */

export type Gender = 'male' | 'female' | 'other';
export type CasteCategory = 'general' | 'obc' | 'sc' | 'st' | 'other';
export type Religion = 'hindu' | 'muslim' | 'christian' | 'sikh' | 'buddhist' | 'jain' | 'other';
export type Occupation = 'farmer' | 'laborer' | 'artisan' | 'shopkeeper' | 'student' | 'unemployed' | 'other';

export interface UserProfile {
  userId: string;
  personalInfo: {
    name: string;
    age: number;
    gender: Gender;
    phoneNumber: string;
    aadhaarNumber?: string;
  };
  demographics: {
    state: string;
    district: string;
    block: string;
    village: string;
    caste: CasteCategory;
    religion: Religion;
    familySize: number;
  };
  economic: {
    annualIncome: number;
    occupation: Occupation;
    landOwnership?: {
      hasLand: boolean;
      acres?: number;
    };
    bankAccount?: {
      accountNumber: string;
      ifscCode: string;
      bankName: string;
    };
  };
  preferences: {
    preferredLanguage: string;
    preferredDialect: string;
    communicationMode: 'voice' | 'text' | 'both';
  };
  applicationHistory: ApplicationRecord[];
}

export interface ApplicationRecord {
  schemeId: string;
  applicationDate: Date;
  status: 'pending' | 'approved' | 'rejected' | 'incomplete';
  confirmationNumber?: string;
}

export interface SchemeMatch {
  schemeId: string;
  name: string;
  matchScore: number;
  eligibilityStatus: 'eligible' | 'likely_eligible' | 'ineligible';
  estimatedBenefit: number;
  applicationDifficulty: 'easy' | 'medium' | 'hard';
  reason: string;
}

export interface EligibilityResult {
  isEligible: boolean;
  confidence: number;
  matchedCriteria: string[];
  unmatchedCriteria: string[];
  missingInformation: string[];
  recommendations: string[];
}

export interface SchemeUpdate {
  schemeId: string;
  changes: Record<string, any>;
  effectiveDate: Date;
}

export interface UserPreferences {
  prioritizeBenefit: boolean;
  prioritizeEase: boolean;
  excludeCategories?: string[];
}

export interface RankedScheme extends SchemeMatch {
  rank: number;
  priorityScore: number;
}

/**
 * Scheme Matcher Service Interface
 * Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
 */
export interface SchemeMatcher {
  /**
   * Find all schemes user is potentially eligible for
   * @param userProfile - Complete user profile data
   * @returns Promise resolving to array of scheme matches
   */
  findEligibleSchemes(userProfile: UserProfile): Promise<SchemeMatch[]>;

  /**
   * Evaluate eligibility for a specific scheme
   * @param schemeId - Scheme identifier
   * @param userProfile - User profile data
   * @returns Promise resolving to detailed eligibility result
   */
  evaluateEligibility(schemeId: string, userProfile: UserProfile): Promise<EligibilityResult>;

  /**
   * Update scheme database with new information
   * @param schemes - Array of scheme updates
   * @returns Promise resolving when update is complete
   */
  updateSchemeDatabase(schemes: SchemeUpdate[]): Promise<void>;

  /**
   * Get priority-ranked list of schemes
   * @param schemes - Schemes to rank
   * @param preferences - User preferences for ranking
   * @returns Promise resolving to ranked schemes
   */
  getPriorityRanking(schemes: SchemeMatch[], preferences: UserPreferences): Promise<RankedScheme[]>;
}
