"""
Unit tests for Outcome Explanation System

Tests approval/rejection notifications, appeal guidance,
and resubmission guidance.

Validates: Requirement 6.5
"""

import pytest
from datetime import datetime, timedelta
from outcome_explanation import (
    OutcomeExplanationSystem,
    OutcomeType,
    RejectionReason,
    AppealEligibility,
    OutcomeExplanation,
    AppealGuidance,
    ResubmissionGuidance
)


@pytest.fixture
def outcome_system():
    """Create an outcome explanation system instance for testing"""
    return OutcomeExplanationSystem()


@pytest.fixture
def sample_application_id():
    """Sample application ID"""
    return "APP-TEST-12345"


class TestApprovalExplanations:
    """Test approval outcome explanations"""

    def test_generate_basic_approval_explanation(self, outcome_system, sample_application_id):
        """
        Test generating basic approval explanation.
        Validates: Requirement 6.5 (inform users with clear explanations)
        """
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.APPROVED
        )
        
        assert isinstance(explanation, OutcomeExplanation)
        assert explanation.application_id == sample_application_id
        assert explanation.outcome_type == OutcomeType.APPROVED
        assert "approved" in explanation.primary_reason.lower()
        assert len(explanation.detailed_explanation) > 0
        assert len(explanation.next_steps) > 0
        assert explanation.appeal_eligible is False
        assert explanation.resubmission_allowed is False

    def test_approval_with_scheme_name(self, outcome_system, sample_application_id):
        """Test approval explanation includes scheme name"""
        scheme_name = "PM-KISAN Scheme"
        
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.APPROVED,
            scheme_name=scheme_name
        )
        
        assert scheme_name in explanation.primary_reason
        assert scheme_name in explanation.detailed_explanation

    def test_approval_with_benefit_amount(self, outcome_system, sample_application_id):
        """Test approval explanation includes benefit amount"""
        benefit_amount = "₹6,000 per year"
        
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.APPROVED,
            benefit_amount=benefit_amount
        )
        
        assert benefit_amount in explanation.detailed_explanation

    def test_approval_with_specific_details(self, outcome_system, sample_application_id):
        """Test approval explanation includes specific details"""
        specific_details = [
            "Land ownership verified",
            "Bank account validated",
            "Aadhaar authentication successful"
        ]
        
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.APPROVED,
            specific_details=specific_details
        )
        
        assert explanation.supporting_details == specific_details

    def test_approval_includes_contact_info(self, outcome_system, sample_application_id):
        """Test approval explanation includes contact information"""
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.APPROVED
        )
        
        assert explanation.contact_info is not None
        assert "helpline" in explanation.contact_info

    def test_approval_next_steps_not_empty(self, outcome_system, sample_application_id):
        """Test approval explanation has meaningful next steps"""
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.APPROVED
        )
        
        assert len(explanation.next_steps) >= 3
        assert any("disburs" in step.lower() for step in explanation.next_steps)


class TestRejectionExplanations:
    """Test rejection outcome explanations"""

    def test_generate_rejection_incomplete_documents(self, outcome_system, sample_application_id):
        """
        Test rejection explanation for incomplete documents.
        Validates: Requirement 6.5 (clear explanations for outcomes)
        """
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.INCOMPLETE_DOCUMENTS
        )
        
        assert explanation.outcome_type == OutcomeType.REJECTED
        assert "incomplete" in explanation.primary_reason.lower()
        assert len(explanation.detailed_explanation) > 0
        assert explanation.appeal_eligible is True
        assert explanation.resubmission_allowed is True
        assert explanation.appeal_deadline is not None

    def test_generate_rejection_ineligible(self, outcome_system, sample_application_id):
        """Test rejection explanation for ineligibility"""
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.INELIGIBLE
        )
        
        assert "eligibility" in explanation.primary_reason.lower()
        assert explanation.appeal_eligible is True
        assert explanation.resubmission_allowed is False

    def test_generate_rejection_duplicate(self, outcome_system, sample_application_id):
        """Test rejection explanation for duplicate application"""
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.DUPLICATE_APPLICATION
        )
        
        assert "duplicate" in explanation.primary_reason.lower()
        assert explanation.appeal_eligible is False
        assert explanation.resubmission_allowed is False

    def test_generate_rejection_invalid_information(self, outcome_system, sample_application_id):
        """Test rejection explanation for invalid information"""
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.INVALID_INFORMATION
        )
        
        assert "invalid" in explanation.primary_reason.lower() or "incorrect" in explanation.primary_reason.lower()
        assert explanation.appeal_eligible is True
        assert explanation.resubmission_allowed is True

    def test_generate_rejection_expired_documents(self, outcome_system, sample_application_id):
        """Test rejection explanation for expired documents"""
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.EXPIRED_DOCUMENTS
        )
        
        assert "expired" in explanation.primary_reason.lower()
        assert explanation.appeal_eligible is False
        assert explanation.resubmission_allowed is True

    def test_rejection_with_specific_details(self, outcome_system, sample_application_id):
        """Test rejection explanation includes specific details"""
        specific_details = [
            "Income certificate missing",
            "Bank statement not provided",
            "Aadhaar verification failed"
        ]
        
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.INCOMPLETE_DOCUMENTS,
            specific_details=specific_details
        )
        
        assert explanation.supporting_details == specific_details

    def test_rejection_appeal_deadline_calculated(self, outcome_system, sample_application_id):
        """Test that appeal deadline is calculated correctly"""
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.INCOMPLETE_DOCUMENTS
        )
        
        assert explanation.appeal_deadline is not None
        # Appeal deadline should be in the future
        assert explanation.appeal_deadline > datetime.now()
        # Should be approximately 30 days from now
        days_diff = (explanation.appeal_deadline - datetime.now()).days
        assert 29 <= days_diff <= 31

    def test_rejection_next_steps_include_appeal_info(self, outcome_system, sample_application_id):
        """Test rejection next steps include appeal information when eligible"""
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.INCOMPLETE_DOCUMENTS
        )
        
        next_steps_text = " ".join(explanation.next_steps).lower()
        assert "appeal" in next_steps_text

    def test_rejection_next_steps_include_resubmission_info(self, outcome_system, sample_application_id):
        """Test rejection next steps include resubmission info when allowed"""
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.EXPIRED_DOCUMENTS
        )
        
        next_steps_text = " ".join(explanation.next_steps).lower()
        assert "resubmit" in next_steps_text or "correct" in next_steps_text


class TestPartialApprovalExplanations:
    """Test partial approval outcome explanations"""

    def test_generate_partial_approval_explanation(self, outcome_system, sample_application_id):
        """Test generating partial approval explanation"""
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.PARTIALLY_APPROVED
        )
        
        assert explanation.outcome_type == OutcomeType.PARTIALLY_APPROVED
        assert "partial" in explanation.primary_reason.lower()
        assert explanation.appeal_eligible is True
        assert explanation.resubmission_allowed is True

    def test_partial_approval_with_specific_details(self, outcome_system, sample_application_id):
        """Test partial approval with specific details"""
        specific_details = [
            "Land subsidy component approved",
            "Equipment subsidy pending verification"
        ]
        
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.PARTIALLY_APPROVED,
            specific_details=specific_details
        )
        
        assert explanation.supporting_details == specific_details


class TestAppealGuidance:
    """Test appeal guidance generation"""

    def test_generate_appeal_guidance_eligible(self, outcome_system, sample_application_id):
        """
        Test generating appeal guidance for eligible application.
        Validates: Requirement 6.5 (appeal guidance)
        """
        rejection_date = datetime.now()
        
        guidance = outcome_system.generate_appeal_guidance(
            application_id=sample_application_id,
            rejection_date=rejection_date,
            rejection_reason=RejectionReason.INCOMPLETE_DOCUMENTS
        )
        
        assert isinstance(guidance, AppealGuidance)
        assert guidance.application_id == sample_application_id
        assert guidance.eligibility == AppealEligibility.ELIGIBLE
        assert guidance.appeal_deadline is not None
        assert len(guidance.appeal_process) > 0
        assert len(guidance.required_documents) > 0
        assert len(guidance.submission_methods) > 0
        assert len(guidance.tips) > 0

    def test_appeal_guidance_not_eligible(self, outcome_system, sample_application_id):
        """Test appeal guidance for non-eligible rejection"""
        rejection_date = datetime.now()
        
        guidance = outcome_system.generate_appeal_guidance(
            application_id=sample_application_id,
            rejection_date=rejection_date,
            rejection_reason=RejectionReason.DUPLICATE_APPLICATION
        )
        
        assert guidance.eligibility == AppealEligibility.NOT_ELIGIBLE
        assert guidance.appeal_deadline is None
        assert len(guidance.tips) > 0

    def test_appeal_guidance_expired(self, outcome_system, sample_application_id):
        """Test appeal guidance for expired appeal window"""
        rejection_date = datetime.now() - timedelta(days=60)  # 60 days ago
        
        guidance = outcome_system.generate_appeal_guidance(
            application_id=sample_application_id,
            rejection_date=rejection_date,
            rejection_reason=RejectionReason.INCOMPLETE_DOCUMENTS
        )
        
        assert guidance.eligibility == AppealEligibility.EXPIRED
        assert guidance.appeal_deadline is not None
        assert guidance.appeal_deadline < datetime.now()

    def test_appeal_process_has_steps(self, outcome_system, sample_application_id):
        """Test that appeal process has clear steps"""
        rejection_date = datetime.now()
        
        guidance = outcome_system.generate_appeal_guidance(
            application_id=sample_application_id,
            rejection_date=rejection_date,
            rejection_reason=RejectionReason.INELIGIBLE
        )
        
        assert len(guidance.appeal_process) >= 3
        for step in guidance.appeal_process:
            assert "step" in step
            assert "description" in step

    def test_appeal_required_documents_specified(self, outcome_system, sample_application_id):
        """Test that required documents are specified"""
        rejection_date = datetime.now()
        
        guidance = outcome_system.generate_appeal_guidance(
            application_id=sample_application_id,
            rejection_date=rejection_date,
            rejection_reason=RejectionReason.INVALID_INFORMATION
        )
        
        assert len(guidance.required_documents) > 0
        for doc in guidance.required_documents:
            assert "name" in doc
            assert "description" in doc

    def test_appeal_submission_methods_provided(self, outcome_system, sample_application_id):
        """Test that submission methods are provided"""
        rejection_date = datetime.now()
        
        guidance = outcome_system.generate_appeal_guidance(
            application_id=sample_application_id,
            rejection_date=rejection_date,
            rejection_reason=RejectionReason.MISSING_CRITERIA
        )
        
        assert len(guidance.submission_methods) > 0
        for method in guidance.submission_methods:
            assert "method" in method
            assert "description" in method

    def test_appeal_contact_info_provided(self, outcome_system, sample_application_id):
        """Test that contact information is provided"""
        rejection_date = datetime.now()
        
        guidance = outcome_system.generate_appeal_guidance(
            application_id=sample_application_id,
            rejection_date=rejection_date,
            rejection_reason=RejectionReason.INCOMPLETE_DOCUMENTS
        )
        
        assert guidance.contact_info is not None
        assert len(guidance.contact_info) > 0

    def test_appeal_tips_reason_specific(self, outcome_system, sample_application_id):
        """Test that tips are specific to rejection reason"""
        rejection_date = datetime.now()
        
        # Test for incomplete documents
        guidance1 = outcome_system.generate_appeal_guidance(
            application_id=sample_application_id,
            rejection_date=rejection_date,
            rejection_reason=RejectionReason.INCOMPLETE_DOCUMENTS
        )
        
        # Test for invalid information
        guidance2 = outcome_system.generate_appeal_guidance(
            application_id=sample_application_id,
            rejection_date=rejection_date,
            rejection_reason=RejectionReason.INVALID_INFORMATION
        )
        
        # Tips should be different for different reasons
        assert guidance1.tips != guidance2.tips


class TestResubmissionGuidance:
    """Test resubmission guidance generation"""

    def test_generate_resubmission_guidance_allowed(self, outcome_system, sample_application_id):
        """
        Test generating resubmission guidance when allowed.
        Validates: Requirement 6.5 (resubmission guidance)
        """
        guidance = outcome_system.generate_resubmission_guidance(
            application_id=sample_application_id,
            rejection_reason=RejectionReason.INCOMPLETE_DOCUMENTS
        )
        
        assert isinstance(guidance, ResubmissionGuidance)
        assert guidance.application_id == sample_application_id
        assert guidance.resubmission_allowed is True
        assert len(guidance.corrections_needed) > 0
        assert len(guidance.resubmission_process) > 0
        assert len(guidance.tips) > 0

    def test_resubmission_guidance_not_allowed(self, outcome_system, sample_application_id):
        """Test resubmission guidance when not allowed"""
        guidance = outcome_system.generate_resubmission_guidance(
            application_id=sample_application_id,
            rejection_reason=RejectionReason.INELIGIBLE
        )
        
        assert guidance.resubmission_allowed is False
        assert len(guidance.tips) > 0

    def test_resubmission_waiting_period(self, outcome_system, sample_application_id):
        """Test that waiting period is specified"""
        guidance = outcome_system.generate_resubmission_guidance(
            application_id=sample_application_id,
            rejection_reason=RejectionReason.EXPIRED_DOCUMENTS
        )
        
        assert guidance.waiting_period is not None
        assert guidance.waiting_period >= 0

    def test_resubmission_corrections_needed(self, outcome_system, sample_application_id):
        """Test that corrections needed are specified"""
        guidance = outcome_system.generate_resubmission_guidance(
            application_id=sample_application_id,
            rejection_reason=RejectionReason.INVALID_INFORMATION
        )
        
        assert len(guidance.corrections_needed) > 0
        for correction in guidance.corrections_needed:
            assert "issue" in correction
            assert "correction" in correction

    def test_resubmission_with_specific_corrections(self, outcome_system, sample_application_id):
        """Test resubmission guidance with specific corrections"""
        specific_corrections = [
            {
                "issue": "Income certificate expired",
                "correction": "Submit fresh income certificate dated within last 6 months"
            },
            {
                "issue": "Bank account mismatch",
                "correction": "Provide bank statement matching Aadhaar name"
            }
        ]
        
        guidance = outcome_system.generate_resubmission_guidance(
            application_id=sample_application_id,
            rejection_reason=RejectionReason.INVALID_INFORMATION,
            specific_corrections=specific_corrections
        )
        
        assert guidance.corrections_needed == specific_corrections

    def test_resubmission_process_has_steps(self, outcome_system, sample_application_id):
        """Test that resubmission process has clear steps"""
        guidance = outcome_system.generate_resubmission_guidance(
            application_id=sample_application_id,
            rejection_reason=RejectionReason.INCOMPLETE_DOCUMENTS
        )
        
        assert len(guidance.resubmission_process) >= 3
        for step in guidance.resubmission_process:
            assert "step" in step
            assert "description" in step

    def test_resubmission_documents_to_update(self, outcome_system, sample_application_id):
        """Test that documents to update are specified"""
        guidance = outcome_system.generate_resubmission_guidance(
            application_id=sample_application_id,
            rejection_reason=RejectionReason.EXPIRED_DOCUMENTS
        )
        
        assert len(guidance.documents_to_update) > 0
        for doc in guidance.documents_to_update:
            assert "document" in doc
            assert "action" in doc

    def test_resubmission_estimated_timeline(self, outcome_system, sample_application_id):
        """Test that estimated timeline is provided"""
        guidance = outcome_system.generate_resubmission_guidance(
            application_id=sample_application_id,
            rejection_reason=RejectionReason.INCOMPLETE_DOCUMENTS
        )
        
        assert guidance.estimated_timeline is not None
        assert len(guidance.estimated_timeline) > 0


class TestRejectionTemplates:
    """Test rejection reason templates"""

    def test_all_rejection_reasons_have_templates(self, outcome_system):
        """Test that all rejection reasons have templates"""
        for reason in RejectionReason:
            assert reason in outcome_system.rejection_templates
            template = outcome_system.rejection_templates[reason]
            assert "primary" in template
            assert "explanation" in template
            assert "appeal_eligible" in template
            assert "resubmission_allowed" in template

    def test_template_consistency(self, outcome_system):
        """Test that templates are consistent"""
        for reason, template in outcome_system.rejection_templates.items():
            # Primary reason should be a non-empty string
            assert isinstance(template["primary"], str)
            assert len(template["primary"]) > 0
            
            # Explanation should be detailed
            assert isinstance(template["explanation"], str)
            assert len(template["explanation"]) > 50
            
            # Flags should be boolean
            assert isinstance(template["appeal_eligible"], bool)
            assert isinstance(template["resubmission_allowed"], bool)


class TestAppealRules:
    """Test appeal rules configuration"""

    def test_appeal_rules_initialized(self, outcome_system):
        """Test that appeal rules are properly initialized"""
        rules = outcome_system.appeal_rules
        
        assert "appeal_window_days" in rules
        assert "processing_time" in rules
        assert "required_documents" in rules
        assert "submission_methods" in rules
        
        assert rules["appeal_window_days"] > 0
        assert len(rules["required_documents"]) > 0
        assert len(rules["submission_methods"]) > 0


class TestResubmissionRules:
    """Test resubmission rules configuration"""

    def test_resubmission_rules_initialized(self, outcome_system):
        """Test that resubmission rules are properly initialized"""
        rules = outcome_system.resubmission_rules
        
        assert "default_waiting_period" in rules
        assert "processing_time" in rules
        assert "general_tips" in rules
        
        assert rules["default_waiting_period"] >= 0
        assert len(rules["general_tips"]) > 0


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_rejection_without_reason_defaults_to_other(self, outcome_system, sample_application_id):
        """Test that rejection without reason defaults to OTHER"""
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.REJECTED
        )
        
        # Should use OTHER template
        assert explanation.outcome_type == OutcomeType.REJECTED
        assert len(explanation.detailed_explanation) > 0

    def test_outcome_date_is_current(self, outcome_system, sample_application_id):
        """Test that outcome date is set to current time"""
        before = datetime.now()
        
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.APPROVED
        )
        
        after = datetime.now()
        
        assert before <= explanation.outcome_date <= after

    def test_empty_specific_details_handled(self, outcome_system, sample_application_id):
        """Test that empty specific details are handled gracefully"""
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.APPROVED,
            specific_details=[]
        )
        
        # Should use default details
        assert len(explanation.supporting_details) > 0

    def test_none_specific_details_handled(self, outcome_system, sample_application_id):
        """Test that None specific details are handled gracefully"""
        explanation = outcome_system.generate_outcome_explanation(
            application_id=sample_application_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.INCOMPLETE_DOCUMENTS,
            specific_details=None
        )
        
        # Should work without error
        assert explanation.outcome_type == OutcomeType.REJECTED
