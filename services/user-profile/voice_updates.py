"""
Voice-based profile update service.
Converts natural language updates to structured profile changes.
"""

import re
from typing import Dict, Optional, Any
from datetime import datetime

from models import (
    UserProfile,
    PersonalInfo,
    Demographics,
    Economic,
    Preferences,
    Gender,
    CasteCategory,
    Religion,
    Occupation,
    LanguageCode,
    DialectCode,
    CommunicationMode,
    LandDetails,
    BankDetails
)


class VoiceUpdateParser:
    """Parses natural language updates into structured profile changes."""
    
    def __init__(self):
        # Mapping patterns for different field types
        self.gender_patterns = {
            r'\b(male|man|boy)\b': Gender.MALE,
            r'\b(female|woman|girl)\b': Gender.FEMALE,
            r'\b(other|transgender)\b': Gender.OTHER
        }
        
        self.occupation_patterns = {
            r'\b(farmer|farming|agriculture)\b': Occupation.FARMER,
            r'\b(agricultural\s*labor|farm\s*labor)\b': Occupation.AGRICULTURAL_LABORER,
            r'\b(daily\s*wage|daily\s*labor)\b': Occupation.DAILY_WAGE_WORKER,
            r'\b(self[\s-]?employed|business)\b': Occupation.SELF_EMPLOYED,
            r'\b(government\s*job|government\s*employee)\b': Occupation.GOVERNMENT_EMPLOYEE,
            r'\b(private\s*job|private\s*employee)\b': Occupation.PRIVATE_EMPLOYEE,
            r'\b(unemployed|no\s*job)\b': Occupation.UNEMPLOYED,
            r'\b(student|studying)\b': Occupation.STUDENT,
            r'\b(retired|pension)\b': Occupation.RETIRED
        }
        
        self.caste_patterns = {
            r'\b(general|unreserved)\b': CasteCategory.GENERAL,
            r'\b(obc|other\s*backward)\b': CasteCategory.OBC,
            r'\b(sc|scheduled\s*caste)\b': CasteCategory.SC,
            r'\b(st|scheduled\s*tribe)\b': CasteCategory.ST,
            r'\b(ews|economically\s*weaker)\b': CasteCategory.EWS
        }
        
        self.language_patterns = {
            r'\b(hindi)\b': LanguageCode.HI,
            r'\b(bengali|bangla)\b': LanguageCode.BN,
            r'\b(telugu)\b': LanguageCode.TE,
            r'\b(marathi)\b': LanguageCode.MR,
            r'\b(tamil)\b': LanguageCode.TA,
            r'\b(gujarati)\b': LanguageCode.GU,
            r'\b(kannada)\b': LanguageCode.KN,
            r'\b(malayalam)\b': LanguageCode.ML,
            r'\b(odia|oriya)\b': LanguageCode.OR,
            r'\b(punjabi)\b': LanguageCode.PA,
            r'\b(assamese)\b': LanguageCode.AS,
            r'\b(urdu)\b': LanguageCode.UR,
            r'\b(english)\b': LanguageCode.EN
        }
    
    def parse_update(self, natural_language: str, current_profile: UserProfile) -> Dict[str, Any]:
        """
        Parse natural language update into structured changes.
        
        Args:
            natural_language: User's natural language update
            current_profile: Current user profile
            
        Returns:
            Dictionary of parsed updates
        """
        text = natural_language.lower()
        updates = {}
        
        # Parse name updates
        name_match = re.search(r'(?:my\s+name\s+is|name\s+is|call\s+me)\s+([a-zA-Z\s]+?)(?:\s+and|\s+my|$|\.)', text)
        if name_match:
            updates['name'] = name_match.group(1).strip().title()
        
        # Parse age updates
        age_match = re.search(r'(?:i\s+am|age\s+is|i\'m)\s+(\d+)\s*(?:years?\s*old)?', text)
        if age_match:
            updates['age'] = int(age_match.group(1))
        
        # Parse gender updates
        for pattern, gender in self.gender_patterns.items():
            if re.search(pattern, text):
                updates['gender'] = gender
                break
        
        # Parse phone number updates
        phone_match = re.search(r'(?:phone|mobile|number)\s*(?:is|:)?\s*(\+?\d{10,15})', text)
        if phone_match:
            updates['phoneNumber'] = phone_match.group(1)
        
        # Parse occupation updates
        for pattern, occupation in self.occupation_patterns.items():
            if re.search(pattern, text):
                updates['occupation'] = occupation
                break
        
        # Parse income updates
        income_match = re.search(r'(?:income|earn|salary)\s*(?:is|of)?\s*(?:rs\.?|rupees?)?\s*(\d+(?:,\d+)*)', text)
        if income_match:
            income_str = income_match.group(1).replace(',', '')
            updates['annualIncome'] = float(income_str)
        
        # Parse caste updates
        for pattern, caste in self.caste_patterns.items():
            if re.search(pattern, text):
                updates['caste'] = caste
                break
        
        # Parse language preference updates
        for pattern, language in self.language_patterns.items():
            if re.search(pattern, text):
                updates['preferredLanguage'] = language
                break
        
        # Parse location updates
        village_match = re.search(r'village\s+([a-zA-Z]+)', text, re.IGNORECASE)
        if village_match:
            updates['village'] = village_match.group(1).strip().title()
        
        district_match = re.search(r'([a-zA-Z]+)\s+district', text, re.IGNORECASE)
        if district_match:
            updates['district'] = district_match.group(1).strip().title()
        
        state_match = re.search(r'([a-zA-Z]+)\s+state', text, re.IGNORECASE)
        if state_match:
            updates['state'] = state_match.group(1).strip().title()
        
        # Parse family size updates
        family_match = re.search(r'(?:family\s+(?:of|has|size))\s+(\d+)', text)
        if family_match:
            updates['familySize'] = int(family_match.group(1))
        
        # Parse land ownership updates
        # Check for negative patterns first (don't have land)
        if re.search(r'\b(no|don\'t|do\s+not)\s+(?:have|own)\s+(?:any\s+)?land\b', text):
            updates['landOwned'] = False
        # Then check for positive patterns (own/have land)
        elif re.search(r'\b(own|have)\s+land\b', text):
            updates['landOwned'] = True
            land_area_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:acre|acres)', text)
            if land_area_match:
                updates['landArea'] = float(land_area_match.group(1))
        
        return updates
    
    def generate_confirmation_message(self, updates: Dict[str, Any]) -> str:
        """
        Generate a human-readable confirmation message for parsed updates.
        
        Args:
            updates: Dictionary of parsed updates
            
        Returns:
            Confirmation message
        """
        if not updates:
            return "I couldn't understand any updates from your message. Please try again."
        
        messages = []
        
        if 'name' in updates:
            messages.append(f"Change name to {updates['name']}")
        if 'age' in updates:
            messages.append(f"Update age to {updates['age']} years")
        if 'gender' in updates:
            messages.append(f"Set gender to {updates['gender'].value}")
        if 'phoneNumber' in updates:
            messages.append(f"Update phone number to {updates['phoneNumber']}")
        if 'occupation' in updates:
            messages.append(f"Change occupation to {updates['occupation'].value}")
        if 'annualIncome' in updates:
            messages.append(f"Update annual income to Rs. {updates['annualIncome']:,.0f}")
        if 'caste' in updates:
            messages.append(f"Set caste category to {updates['caste'].value}")
        if 'preferredLanguage' in updates:
            messages.append(f"Change preferred language to {updates['preferredLanguage'].value}")
        if 'village' in updates:
            messages.append(f"Update village to {updates['village']}")
        if 'district' in updates:
            messages.append(f"Update district to {updates['district']}")
        if 'state' in updates:
            messages.append(f"Update state to {updates['state']}")
        if 'familySize' in updates:
            messages.append(f"Set family size to {updates['familySize']} members")
        if 'landOwned' in updates:
            if updates['landOwned']:
                land_msg = "You own land"
                if 'landArea' in updates:
                    land_msg += f" ({updates['landArea']} acres)"
                messages.append(land_msg)
            else:
                messages.append("You don't own land")
        
        confirmation = "I understood the following updates:\n" + "\n".join(f"- {msg}" for msg in messages)
        confirmation += "\n\nPlease confirm if these updates are correct."
        
        return confirmation
    
    def apply_updates(self, profile: UserProfile, updates: Dict[str, Any]) -> UserProfile:
        """
        Apply parsed updates to a user profile.
        
        Args:
            profile: Current user profile
            updates: Dictionary of updates to apply
            
        Returns:
            Updated user profile
        """
        # Update personal info
        if any(k in updates for k in ['name', 'age', 'gender', 'phoneNumber']):
            personal_dict = profile.personalInfo.model_dump()
            if 'name' in updates:
                personal_dict['name'] = updates['name']
            if 'age' in updates:
                personal_dict['age'] = updates['age']
            if 'gender' in updates:
                personal_dict['gender'] = updates['gender']
            if 'phoneNumber' in updates:
                personal_dict['phoneNumber'] = updates['phoneNumber']
            profile.personalInfo = PersonalInfo(**personal_dict)
        
        # Update demographics
        if any(k in updates for k in ['state', 'district', 'village', 'caste', 'familySize']):
            demo_dict = profile.demographics.model_dump()
            if 'state' in updates:
                demo_dict['state'] = updates['state']
            if 'district' in updates:
                demo_dict['district'] = updates['district']
            if 'village' in updates:
                demo_dict['village'] = updates['village']
            if 'caste' in updates:
                demo_dict['caste'] = updates['caste']
            if 'familySize' in updates:
                demo_dict['familySize'] = updates['familySize']
            profile.demographics = Demographics(**demo_dict)
        
        # Update economic info
        if any(k in updates for k in ['occupation', 'annualIncome', 'landOwned', 'landArea']):
            econ_dict = profile.economic.model_dump()
            if 'occupation' in updates:
                econ_dict['occupation'] = updates['occupation']
            if 'annualIncome' in updates:
                econ_dict['annualIncome'] = updates['annualIncome']
            if 'landOwned' in updates or 'landArea' in updates:
                land_dict = econ_dict['landOwnership']
                if 'landOwned' in updates:
                    land_dict['owned'] = updates['landOwned']
                if 'landArea' in updates:
                    land_dict['areaInAcres'] = updates['landArea']
                econ_dict['landOwnership'] = land_dict
            profile.economic = Economic(**econ_dict)
        
        # Update preferences
        if 'preferredLanguage' in updates:
            pref_dict = profile.preferences.model_dump()
            pref_dict['preferredLanguage'] = updates['preferredLanguage']
            profile.preferences = Preferences(**pref_dict)
        
        profile.updatedAt = datetime.utcnow()
        
        return profile
