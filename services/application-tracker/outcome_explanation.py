"""
Outcome Explanation System
Provides clear explanations for application outcomes (approval/rejection),
appeal guidance, and resubmission instructions.

Validates: Requirement 6.5
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class OutcomeType(str, Enum):
    """Types of application outcomes"""
    APPROVED = "approved"
    REJECTED = "rejected"
    PARTIALLY_APPROVED = "partially_approved"


class RejectionReason(str, Enum):
    """Common rejection reasons"""
    INCOMPLETE_DOCUMENTS = "incomplete_documents"
    INELIGIBLE = "ineligible"
    DUPLICATE_APPLICATION = "duplicate_application"
    INVALID_INFORMATION = "invalid_information"
    MISSING_CRITERIA = "missing_criteria"
    EXPIRED_DOCUMENTS = "expired_documents"
    TECHNICAL_ERROR = "technical_error"
    OTHER = "other"


class AppealEligibility(str, Enum):
    """Appeal eligibility status"""
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    EXPIRED = "expired"


class OutcomeExplanation(BaseModel):
    """Detailed explanation of application outcome"""
    application_id: str
    outcome_type: OutcomeType
    outcome_date: datetime
    primary_reason: str
    detailed_explanation: str
    supporting_details: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    appeal_eligible: bool = False
    appeal_deadline: Optional[datetime] = None
    resubmission_allowed: bool = False
    contact_info: Optional[Dict[str, str]] = None


class AppealGuidance(BaseModel):
    """Guidance for filing an appeal"""
    application_id: str
    eligibility: AppealEligibility
    appeal_deadline: Optional[datetime] = None
    appeal_process: List[Dict[str, str]] = Field(default_factory=list)
    required_documents: List[Dict[str, str]] = Field(default_factory=list)
    submission_methods: List[Dict[str, str]] = Field(default_factory=list)
    estimated_timeline: str
    contact_info: Dict[str, str]
    tips: List[str] = Field(default_factory=list)


class ResubmissionGuidance(BaseModel):
    """Guidance for resubmitting an application"""
    application_id: str
    resubmission_allowed: bool
    waiting_period: Optional[int] = None  # Days to wait before resubmission
    corrections_needed: List[Dict[str, str]] = Field(default_factory=list)
    resubmission_process: List[Dict[str, str]] = Field(default_factory=list)
    documents_to_update: List[Dict[str, str]] = Field(default_factory=list)
    estimated_timeline: str
    tips: List[str] = Field(default_factory=list)


class OutcomeExplanationSystem:
    """
    System for generating clear explanations of application outcomes
    and providing guidance for appeals and resubmissions.
    """

    def __init__(self):
        """Initialize the outcome explanation system"""
        # Rejection reason templates
        self.rejection_templates = self._initialize_rejection_templates()
        
        # Appeal eligibility rules
        self.appeal_rules = self._initialize_appeal_rules()
        
        # Resubmission rules
        self.resubmission_rules = self._initialize_resubmission_rules()

    def _initialize_rejection_templates(self) -> Dict[RejectionReason, Dict[str, Any]]:
        """Initialize templates for rejection explanations"""
        return {
            RejectionReason.INCOMPLETE_DOCUMENTS: {
                "primary": "Application rejected due to incomplete documentation",
                "explanation": "Your application could not be processed because required documents were missing or incomplete. "
                              "All mandatory documents must be submitted for the application to be considered.",
                "appeal_eligible": True,
                "resubmission_allowed": True
            },
            RejectionReason.INELIGIBLE: {
                "primary": "Application rejected - eligibility criteria not met",
                "explanation": "After careful review, we found that you do not meet the eligibility criteria for this scheme. "
                              "Eligibility is determined based on specific requirements such as income, age, occupation, or location.",
                "appeal_eligible": True,
                "resubmission_allowed": False
            },
            RejectionReason.DUPLICATE_APPLICATION: {
                "primary": "Application rejected - duplicate submission detected",
                "explanation": "Our records show that you have already submitted an application for this scheme. "
                              "Multiple applications for the same scheme are not allowed.",
                "appeal_eligible": False,
                "resubmission_allowed": False
            },
            RejectionReason.INVALID_INFORMATION: {
                "primary": "Application rejected due to invalid or incorrect information",
                "explanation": "The information provided in your application could not be verified or was found to be incorrect. "
                              "All information must be accurate and verifiable.",
                "appeal_eligible": True,
                "resubmission_allowed": True
            },
            RejectionReason.MISSING_CRITERIA: {
                "primary": "Application rejected - required criteria not satisfied",
                "explanation": "Your application does not satisfy one or more mandatory criteria for this scheme. "
                              "Please review the scheme requirements carefully.",
                "appeal_eligible": True,
                "resubmission_allowed": True
            },
            RejectionReason.EXPIRED_DOCUMENTS: {
                "primary": "Application rejected due to expired documents",
                "explanation": "One or more documents submitted with your application have expired. "
                              "All documents must be valid and current at the time of submission.",
                "appeal_eligible": False,
                "resubmission_allowed": True
            },
            RejectionReason.TECHNICAL_ERROR: {
                "primary": "Application rejected due to technical processing error",
                "explanation": "Your application could not be processed due to a technical error in our system. "
                              "This is not related to your eligibility or documentation.",
                "appeal_eligible": False,
                "resubmission_allowed": True
            },
            RejectionReason.OTHER: {
                "primary": "Application rejected",
                "explanation": "Your application has been rejected. Please contact the department for specific details.",
                "appeal_eligible": True,
                "resubmission_allowed": True
            }
        }

    def _initialize_appeal_rules(self) -> Dict[str, Any]:
        """Initialize rules for appeal eligibility"""
        return {
            "appeal_window_days": 30,  # Days from rejection to file appeal
            "processing_time": "30-45 days",
            "required_documents": [
                {
                    "name": "Appeal Letter",
                    "description": "Written statement explaining why you believe the decision should be reconsidered"
                },
                {
                    "name": "Original Application Copy",
                    "description": "Copy of your original application with confirmation number"
                },
                {
                    "name": "Supporting Evidence",
                    "description": "Any additional documents or evidence supporting your appeal"
                }
            ],
            "submission_methods": [
                {
                    "method": "Online Portal",
                    "description": "Submit through the government portal using your application ID"
                },
                {
                    "method": "District Office",
                    "description": "Submit in person at your district welfare office"
                },
                {
                    "method": "Registered Post",
                    "description": "Mail to the department address with acknowledgment"
                }
            ]
        }

    def _initialize_resubmission_rules(self) -> Dict[str, Any]:
        """Initialize rules for resubmission"""
        return {
            "default_waiting_period": 0,  # Days to wait before resubmission
            "processing_time": "15-30 days",
            "general_tips": [
                "Review all eligibility criteria carefully before resubmitting",
                "Ensure all documents are current and valid",
                "Double-check all information for accuracy",
                "Keep copies of all submitted documents",
                "Note your new confirmation number for tracking"
            ]
        }

    def generate_outcome_explanation(
        self,
        application_id: str,
        outcome_type: OutcomeType,
        rejection_reason: Optional[RejectionReason] = None,
        specific_details: Optional[List[str]] = None,
        scheme_name: Optional[str] = None,
        benefit_amount: Optional[str] = None
    ) -> OutcomeExplanation:
        """
        Generate a clear explanation for an application outcome.
        
        Args:
            application_id: Application identifier
            outcome_type: Type of outcome (approved/rejected/partially_approved)
            rejection_reason: Reason for rejection (if applicable)
            specific_details: Specific details about the outcome
            scheme_name: Name of the scheme
            benefit_amount: Benefit amount (for approvals)
            
        Returns:
            OutcomeExplanation with detailed information
            
        Validates: Requirement 6.5 (inform users with clear explanations)
        """
        outcome_date = datetime.now()
        
        if outcome_type == OutcomeType.APPROVED:
            return self._generate_approval_explanation(
                application_id,
                outcome_date,
                scheme_name,
                benefit_amount,
                specific_details
            )
        elif outcome_type == OutcomeType.REJECTED:
            return self._generate_rejection_explanation(
                application_id,
                outcome_date,
                rejection_reason or RejectionReason.OTHER,
                specific_details
            )
        else:  # PARTIALLY_APPROVED
            return self._generate_partial_approval_explanation(
                application_id,
                outcome_date,
                specific_details
            )

    def _generate_approval_explanation(
        self,
        application_id: str,
        outcome_date: datetime,
        scheme_name: Optional[str],
        benefit_amount: Optional[str],
        specific_details: Optional[List[str]]
    ) -> OutcomeExplanation:
        """Generate explanation for approved application"""
        scheme_text = f" for {scheme_name}" if scheme_name else ""
        benefit_text = f" of {benefit_amount}" if benefit_amount else ""
        
        primary_reason = f"Application approved{scheme_text}"
        
        detailed_explanation = (
            f"Congratulations! Your application has been approved{scheme_text}. "
            f"You have been found eligible and all requirements have been satisfied. "
        )
        
        if benefit_amount:
            detailed_explanation += f"You will receive benefits{benefit_text}. "
        
        detailed_explanation += (
            "The benefits will be processed and disbursed according to the scheme guidelines."
        )
        
        supporting_details = specific_details or [
            "All eligibility criteria verified successfully",
            "Documents validated and accepted",
            "Application processed and approved by authorized officer"
        ]
        
        next_steps = [
            "Benefits will be disbursed to your registered bank account",
            "You will receive a confirmation SMS/email with disbursement details",
            "Keep your confirmation number for future reference",
            "Contact the helpline if you don't receive benefits within the expected timeline"
        ]
        
        return OutcomeExplanation(
            application_id=application_id,
            outcome_type=OutcomeType.APPROVED,
            outcome_date=outcome_date,
            primary_reason=primary_reason,
            detailed_explanation=detailed_explanation,
            supporting_details=supporting_details,
            next_steps=next_steps,
            appeal_eligible=False,
            resubmission_allowed=False,
            contact_info={
                "helpline": "1800-XXX-XXXX",
                "email": "support@scheme.gov.in"
            }
        )

    def _generate_rejection_explanation(
        self,
        application_id: str,
        outcome_date: datetime,
        rejection_reason: RejectionReason,
        specific_details: Optional[List[str]]
    ) -> OutcomeExplanation:
        """Generate explanation for rejected application"""
        template = self.rejection_templates[rejection_reason]
        
        appeal_deadline = None
        if template["appeal_eligible"]:
            appeal_deadline = outcome_date + timedelta(
                days=self.appeal_rules["appeal_window_days"]
            )
        
        next_steps = []
        
        if template["appeal_eligible"]:
            next_steps.append(
                f"You can file an appeal within {self.appeal_rules['appeal_window_days']} days "
                f"(by {appeal_deadline.strftime('%d %B %Y')})"
            )
        
        if template["resubmission_allowed"]:
            next_steps.append("You can correct the issues and resubmit your application")
        
        next_steps.extend([
            "Review the detailed explanation and supporting details carefully",
            "Contact the helpline for clarification if needed",
            "Keep your application ID for future reference"
        ])
        
        return OutcomeExplanation(
            application_id=application_id,
            outcome_type=OutcomeType.REJECTED,
            outcome_date=outcome_date,
            primary_reason=template["primary"],
            detailed_explanation=template["explanation"],
            supporting_details=specific_details or [],
            next_steps=next_steps,
            appeal_eligible=template["appeal_eligible"],
            appeal_deadline=appeal_deadline,
            resubmission_allowed=template["resubmission_allowed"],
            contact_info={
                "helpline": "1800-XXX-XXXX",
                "email": "support@scheme.gov.in",
                "office": "District Welfare Office"
            }
        )

    def _generate_partial_approval_explanation(
        self,
        application_id: str,
        outcome_date: datetime,
        specific_details: Optional[List[str]]
    ) -> OutcomeExplanation:
        """Generate explanation for partially approved application"""
        return OutcomeExplanation(
            application_id=application_id,
            outcome_type=OutcomeType.PARTIALLY_APPROVED,
            outcome_date=outcome_date,
            primary_reason="Application partially approved",
            detailed_explanation=(
                "Your application has been partially approved. Some components of your application "
                "have been accepted while others require additional review or documentation."
            ),
            supporting_details=specific_details or [
                "Some eligibility criteria met",
                "Additional verification required for certain components"
            ],
            next_steps=[
                "Review which components were approved",
                "Submit additional information for pending components",
                "Approved benefits will be processed separately",
                "Contact the office for details on pending items"
            ],
            appeal_eligible=True,
            appeal_deadline=outcome_date + timedelta(days=30),
            resubmission_allowed=True,
            contact_info={
                "helpline": "1800-XXX-XXXX",
                "email": "support@scheme.gov.in"
            }
        )

    def generate_appeal_guidance(
        self,
        application_id: str,
        rejection_date: datetime,
        rejection_reason: RejectionReason
    ) -> AppealGuidance:
        """
        Generate guidance for filing an appeal.
        
        Args:
            application_id: Application identifier
            rejection_date: Date of rejection
            rejection_reason: Reason for rejection
            
        Returns:
            AppealGuidance with detailed appeal process
            
        Validates: Requirement 6.5 (appeal guidance)
        """
        # Check appeal eligibility
        template = self.rejection_templates[rejection_reason]
        
        if not template["appeal_eligible"]:
            return AppealGuidance(
                application_id=application_id,
                eligibility=AppealEligibility.NOT_ELIGIBLE,
                estimated_timeline="N/A",
                contact_info={
                    "helpline": "1800-XXX-XXXX",
                    "email": "support@scheme.gov.in"
                },
                tips=[
                    "Appeals are not available for this rejection reason",
                    "Consider resubmitting with corrections if allowed",
                    "Contact the helpline for alternative options"
                ]
            )
        
        # Check if appeal window has expired
        appeal_deadline = rejection_date + timedelta(
            days=self.appeal_rules["appeal_window_days"]
        )
        
        if datetime.now() > appeal_deadline:
            return AppealGuidance(
                application_id=application_id,
                eligibility=AppealEligibility.EXPIRED,
                appeal_deadline=appeal_deadline,
                estimated_timeline="N/A",
                contact_info={
                    "helpline": "1800-XXX-XXXX",
                    "email": "support@scheme.gov.in"
                },
                tips=[
                    f"Appeal window expired on {appeal_deadline.strftime('%d %B %Y')}",
                    "Consider resubmitting a new application if eligible",
                    "Contact the office for exceptional circumstances"
                ]
            )
        
        # Generate appeal process steps
        appeal_process = [
            {
                "step": "1. Prepare Appeal Letter",
                "description": "Write a clear letter explaining why the decision should be reconsidered. "
                              "Include your application ID and specific reasons for appeal."
            },
            {
                "step": "2. Gather Supporting Documents",
                "description": "Collect all documents that support your appeal, including any missing "
                              "or corrected documents from the original application."
            },
            {
                "step": "3. Complete Appeal Form",
                "description": "Fill out the official appeal form available on the portal or at the district office."
            },
            {
                "step": "4. Submit Appeal",
                "description": "Submit your appeal through one of the available methods before the deadline."
            },
            {
                "step": "5. Track Appeal Status",
                "description": "Use your appeal reference number to track the status of your appeal."
            }
        ]
        
        # Generate tips based on rejection reason
        tips = [
            "Submit your appeal as early as possible within the deadline",
            "Be specific and factual in your appeal letter",
            "Include all relevant supporting documents",
            "Keep copies of all submitted documents",
            "Follow up regularly on your appeal status"
        ]
        
        if rejection_reason == RejectionReason.INCOMPLETE_DOCUMENTS:
            tips.append("Ensure all previously missing documents are included with the appeal")
        elif rejection_reason == RejectionReason.INVALID_INFORMATION:
            tips.append("Provide verified documents to support the corrected information")
        elif rejection_reason == RejectionReason.INELIGIBLE:
            tips.append("Clearly explain how you meet the eligibility criteria with evidence")
        
        return AppealGuidance(
            application_id=application_id,
            eligibility=AppealEligibility.ELIGIBLE,
            appeal_deadline=appeal_deadline,
            appeal_process=appeal_process,
            required_documents=self.appeal_rules["required_documents"],
            submission_methods=self.appeal_rules["submission_methods"],
            estimated_timeline=self.appeal_rules["processing_time"],
            contact_info={
                "helpline": "1800-XXX-XXXX",
                "email": "appeals@scheme.gov.in",
                "office": "District Welfare Office - Appeals Section"
            },
            tips=tips
        )

    def generate_resubmission_guidance(
        self,
        application_id: str,
        rejection_reason: RejectionReason,
        specific_corrections: Optional[List[Dict[str, str]]] = None
    ) -> ResubmissionGuidance:
        """
        Generate guidance for resubmitting an application.
        
        Args:
            application_id: Application identifier
            rejection_reason: Reason for rejection
            specific_corrections: Specific corrections needed
            
        Returns:
            ResubmissionGuidance with detailed resubmission process
            
        Validates: Requirement 6.5 (resubmission guidance)
        """
        template = self.rejection_templates[rejection_reason]
        
        if not template["resubmission_allowed"]:
            return ResubmissionGuidance(
                application_id=application_id,
                resubmission_allowed=False,
                estimated_timeline="N/A",
                tips=[
                    "Resubmission is not allowed for this rejection reason",
                    "Consider filing an appeal if eligible",
                    "Contact the helpline for alternative options"
                ]
            )
        
        # Generate corrections needed based on rejection reason
        corrections_needed = specific_corrections or self._get_default_corrections(rejection_reason)
        
        # Generate resubmission process
        resubmission_process = [
            {
                "step": "1. Review Rejection Details",
                "description": "Carefully review the rejection reason and all specific issues mentioned."
            },
            {
                "step": "2. Correct All Issues",
                "description": "Address each issue mentioned in the rejection. Gather corrected or missing documents."
            },
            {
                "step": "3. Verify Eligibility",
                "description": "Ensure you meet all eligibility criteria before resubmitting."
            },
            {
                "step": "4. Prepare New Application",
                "description": "Fill out a fresh application form with corrected information."
            },
            {
                "step": "5. Submit Application",
                "description": "Submit the new application through the portal. You will receive a new confirmation number."
            }
        ]
        
        # Documents to update based on rejection reason
        documents_to_update = self._get_documents_to_update(rejection_reason)
        
        # Waiting period
        waiting_period = self.resubmission_rules["default_waiting_period"]
        if rejection_reason == RejectionReason.DUPLICATE_APPLICATION:
            waiting_period = 90  # Wait 90 days for duplicate applications
        
        return ResubmissionGuidance(
            application_id=application_id,
            resubmission_allowed=True,
            waiting_period=waiting_period,
            corrections_needed=corrections_needed,
            resubmission_process=resubmission_process,
            documents_to_update=documents_to_update,
            estimated_timeline=self.resubmission_rules["processing_time"],
            tips=self.resubmission_rules["general_tips"]
        )

    def _get_default_corrections(self, rejection_reason: RejectionReason) -> List[Dict[str, str]]:
        """Get default corrections needed based on rejection reason"""
        corrections_map = {
            RejectionReason.INCOMPLETE_DOCUMENTS: [
                {
                    "issue": "Missing Documents",
                    "correction": "Submit all required documents as per the scheme checklist"
                }
            ],
            RejectionReason.INVALID_INFORMATION: [
                {
                    "issue": "Incorrect Information",
                    "correction": "Verify and correct all information with supporting documents"
                }
            ],
            RejectionReason.MISSING_CRITERIA: [
                {
                    "issue": "Eligibility Criteria Not Met",
                    "correction": "Review eligibility requirements and provide evidence of meeting criteria"
                }
            ],
            RejectionReason.EXPIRED_DOCUMENTS: [
                {
                    "issue": "Expired Documents",
                    "correction": "Obtain fresh, valid copies of all expired documents"
                }
            ],
            RejectionReason.TECHNICAL_ERROR: [
                {
                    "issue": "Technical Processing Error",
                    "correction": "Resubmit the same application - no changes needed"
                }
            ]
        }
        
        return corrections_map.get(rejection_reason, [
            {
                "issue": "Application Issues",
                "correction": "Review rejection details and correct all mentioned issues"
            }
        ])

    def _get_documents_to_update(self, rejection_reason: RejectionReason) -> List[Dict[str, str]]:
        """Get documents that need to be updated based on rejection reason"""
        if rejection_reason == RejectionReason.EXPIRED_DOCUMENTS:
            return [
                {
                    "document": "All Expired Documents",
                    "action": "Obtain fresh copies with current validity"
                }
            ]
        elif rejection_reason == RejectionReason.INCOMPLETE_DOCUMENTS:
            return [
                {
                    "document": "Missing Documents",
                    "action": "Submit all documents from the required checklist"
                }
            ]
        elif rejection_reason == RejectionReason.INVALID_INFORMATION:
            return [
                {
                    "document": "Verification Documents",
                    "action": "Provide documents that verify the corrected information"
                }
            ]
        else:
            return []
