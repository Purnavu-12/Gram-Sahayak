"""
Integration tests for Outcome Explanation System with Lifecycle Management

Tests the integration of outcome explanations with lifecycle management,
including notifications and guidance retrieval.

Validates: Requirement 6.5
"""

import pytest
from datetime import datetime, timedelta
from lifecycle_management import LifecycleManager, NotificationType, NotificationPriority
from outcome_explanation import OutcomeType, RejectionReason


@pytest.fixture
def lifecycle_manager():
    """Create a lifecycle manager instance for testing"""
    return LifecycleManager()


@pytest.fixture
def sample_application_id():
    """Sample application ID"""
    return "APP-INTEGRATION-12345"


class TestOutcomeNotificationIntegration:
    """Test integration of outcome notifications with lifecycle management"""

    @pytest.mark.asyncio
    async def test_send_approval_notification(self, lifecycle_manager, sample_application_id):
        """
        Test sending approval notification through lifecycle manager.
        Validates: Requirement 6.5 (inform users with clear explanations)
        """
        explanation = await lifecycle_manager.send_outcome_notification(
            application_id=sample_application_id,
            outcome_type=OutcomeType.APPROVED,
            scheme_name="PM-KISAN",
            benefit_amount="₹6,000 per year"
        )
        
        # Check explanation was created
        assert explanation.application_id == sample_application_id
        assert explanation.outcome_type == OutcomeType.APPROVED
        
        # Check notification was sent
        notifications = await lifecycle_manager.get_notifications(sample_application_id)
        assert len(notifications) > 0
        
        approval_notification = next(
            (n for n in notifications if n.notification_type == NotificationType.APPROVAL),
            None
        )
        assert approval_notification is not None
        assert approval_notification.priority == NotificationPriority.HIGH
        assert "approved" in approval_notification.message.lower()

    @pytest.mark.asyncio
    async def test_send_rejection_notification(self, lifecycle_manager, sample_application_id):
        """Test sending rejection notification through lifecycle manager"""
        explanation = await lifecycle_manager.send_outcome_notification(
            application_id=sample_application_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.INCOMPLETE_DOCUMENTS,
            specific_details=["Income certificate missing", "Bank statement not provided"]
        )
        
        # Check explanation was created
        assert explanation.outcome_type == OutcomeType.REJECTED
        assert explanation.appeal_eligible is True
        
        # Check notification was sent
        notifications = await lifecycle_manager.get_notifications(sample_application_id)
        rejection_notification = next(
            (n for n in notifications if n.notification_type == NotificationType.REJECTION),
            None
        )
        assert rejection_notification is not None
        assert rejection_notification.priority == NotificationPriority.HIGH

    @pytest.mark.asyncio
    async def test_notification_includes_explanation_details(self, lifecycle_manager, sample_application_id):
        """Test that notification includes explanation details"""
        await lifecycle_manager.send_outcome_notification(
            application_id=sample_application_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.INELIGIBLE
        )
        
        notifications = await lifecycle_manager.get_notifications(sample_application_id)
        notification = notifications[0]
        
        # Message should include key information
        message = notification.message.lower()
        assert "rejected" in message or "eligibility" in message
        assert "next steps" in message

    @pytest.mark.asyncio
    async def test_notification_action_required_for_rejection(self, lifecycle_manager, sample_application_id):
        """Test that rejection notification marks action as required"""
        await lifecycle_manager.send_outcome_notification(
            application_id=sample_application_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.INCOMPLETE_DOCUMENTS
        )
        
        notifications = await lifecycle_manager.get_notifications(sample_application_id)
        notification = notifications[0]
        
        # Should require action since appeal/resubmission is possible
        assert notification.action_required is True
        assert notification.action_details is not None

    @pytest.mark.asyncio
    async def test_notification_no_action_for_approval(self, lifecycle_manager, sample_application_id):
        """Test that approval notification doesn't require action"""
        await lifecycle_manager.send_outcome_notification(
            application_id=sample_application_id,
            outcome_type=OutcomeType.APPROVED
        )
        
        notifications = await lifecycle_manager.get_notifications(sample_application_id)
        notification = notifications[0]
        
        # Approval shouldn't require action
        assert notification.action_required is False


class TestOutcomeExplanationRetrieval:
    """Test retrieving outcome explanations"""

    @pytest.mark.asyncio
    async def test_get_outcome_explanation(self, lifecycle_manager, sample_application_id):
        """Test retrieving outcome explanation"""
        # Send outcome notification
        await lifecycle_manager.send_outcome_notification(
            application_id=sample_application_id,
            outcome_type=OutcomeType.APPROVED,
            scheme_name="Test Scheme"
        )
        
        # Retrieve explanation
        explanation = await lifecycle_manager.get_outcome_explanation(sample_application_id)
        
        assert explanation is not None
        assert explanation.application_id == sample_application_id
        assert explanation.outcome_type == OutcomeType.APPROVED

    @pytest.mark.asyncio
    async def test_get_nonexistent_outcome_explanation(self, lifecycle_manager):
        """Test retrieving explanation for non-existent application"""
        explanation = await lifecycle_manager.get_outcome_explanation("NONEXISTENT-123")
        assert explanation is None


class TestAppealGuidanceIntegration:
    """Test appeal guidance integration with lifecycle management"""

    @pytest.mark.asyncio
    async def test_get_appeal_guidance_for_rejected_application(
        self,
        lifecycle_manager,
        sample_application_id
    ):
        """
        Test getting appeal guidance for rejected application.
        Validates: Requirement 6.5 (appeal guidance)
        """
        # Send rejection notification
        await lifecycle_manager.send_outcome_notification(
            application_id=sample_application_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.INCOMPLETE_DOCUMENTS
        )
        
        # Get appeal guidance
        guidance = await lifecycle_manager.get_appeal_guidance(sample_application_id)
        
        assert guidance is not None
        assert guidance.application_id == sample_application_id
        assert len(guidance.appeal_process) > 0
        assert len(guidance.required_documents) > 0

    @pytest.mark.asyncio
    async def test_get_appeal_guidance_for_approved_application(
        self,
        lifecycle_manager,
        sample_application_id
    ):
        """Test that appeal guidance is not available for approved applications"""
        # Send approval notification
        await lifecycle_manager.send_outcome_notification(
            application_id=sample_application_id,
            outcome_type=OutcomeType.APPROVED
        )
        
        # Try to get appeal guidance
        guidance = await lifecycle_manager.get_appeal_guidance(sample_application_id)
        
        # Should be None for approved applications
        assert guidance is None

    @pytest.mark.asyncio
    async def test_get_appeal_guidance_nonexistent_application(self, lifecycle_manager):
        """Test getting appeal guidance for non-existent application"""
        guidance = await lifecycle_manager.get_appeal_guidance("NONEXISTENT-123")
        assert guidance is None

    @pytest.mark.asyncio
    async def test_appeal_guidance_different_rejection_reasons(self, lifecycle_manager):
        """Test that appeal guidance varies by rejection reason"""
        app_id_1 = "APP-001"
        app_id_2 = "APP-002"
        
        # Rejection with appeal eligible
        await lifecycle_manager.send_outcome_notification(
            application_id=app_id_1,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.INCOMPLETE_DOCUMENTS
        )
        
        # Rejection with appeal not eligible
        await lifecycle_manager.send_outcome_notification(
            application_id=app_id_2,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.DUPLICATE_APPLICATION
        )
        
        guidance_1 = await lifecycle_manager.get_appeal_guidance(app_id_1)
        guidance_2 = await lifecycle_manager.get_appeal_guidance(app_id_2)
        
        # First should be eligible, second should not
        assert guidance_1 is not None
        assert guidance_2 is not None
        # Eligibility should be different
        assert guidance_1.eligibility != guidance_2.eligibility


class TestResubmissionGuidanceIntegration:
    """Test resubmission guidance integration with lifecycle management"""

    @pytest.mark.asyncio
    async def test_get_resubmission_guidance_for_rejected_application(
        self,
        lifecycle_manager,
        sample_application_id
    ):
        """
        Test getting resubmission guidance for rejected application.
        Validates: Requirement 6.5 (resubmission guidance)
        """
        # Send rejection notification
        await lifecycle_manager.send_outcome_notification(
            application_id=sample_application_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.EXPIRED_DOCUMENTS
        )
        
        # Get resubmission guidance
        guidance = await lifecycle_manager.get_resubmission_guidance(sample_application_id)
        
        assert guidance is not None
        assert guidance.application_id == sample_application_id
        assert guidance.resubmission_allowed is True
        assert len(guidance.resubmission_process) > 0

    @pytest.mark.asyncio
    async def test_get_resubmission_guidance_with_specific_corrections(
        self,
        lifecycle_manager,
        sample_application_id
    ):
        """Test getting resubmission guidance with specific corrections"""
        # Send rejection notification
        await lifecycle_manager.send_outcome_notification(
            application_id=sample_application_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.INVALID_INFORMATION
        )
        
        # Get resubmission guidance with specific corrections
        specific_corrections = [
            {
                "issue": "Aadhaar name mismatch",
                "correction": "Update Aadhaar or provide name change certificate"
            }
        ]
        
        guidance = await lifecycle_manager.get_resubmission_guidance(
            sample_application_id,
            specific_corrections=specific_corrections
        )
        
        assert guidance is not None
        assert guidance.corrections_needed == specific_corrections

    @pytest.mark.asyncio
    async def test_get_resubmission_guidance_not_allowed(
        self,
        lifecycle_manager,
        sample_application_id
    ):
        """Test that resubmission guidance reflects when not allowed"""
        # Send rejection where resubmission is not allowed
        await lifecycle_manager.send_outcome_notification(
            application_id=sample_application_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.INELIGIBLE
        )
        
        # Get resubmission guidance
        guidance = await lifecycle_manager.get_resubmission_guidance(sample_application_id)
        
        # Should return guidance but with resubmission_allowed = False
        assert guidance is not None
        assert guidance.resubmission_allowed is False

    @pytest.mark.asyncio
    async def test_get_resubmission_guidance_for_approved_application(
        self,
        lifecycle_manager,
        sample_application_id
    ):
        """Test that resubmission guidance is not available for approved applications"""
        # Send approval notification
        await lifecycle_manager.send_outcome_notification(
            application_id=sample_application_id,
            outcome_type=OutcomeType.APPROVED
        )
        
        # Try to get resubmission guidance
        guidance = await lifecycle_manager.get_resubmission_guidance(sample_application_id)
        
        # Should be None for approved applications
        assert guidance is None


class TestRejectionReasonInference:
    """Test rejection reason inference from explanations"""

    @pytest.mark.asyncio
    async def test_infer_incomplete_documents(self, lifecycle_manager):
        """Test inferring incomplete documents rejection reason"""
        app_id = "APP-INFER-001"
        
        await lifecycle_manager.send_outcome_notification(
            application_id=app_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.INCOMPLETE_DOCUMENTS
        )
        
        explanation = await lifecycle_manager.get_outcome_explanation(app_id)
        inferred_reason = lifecycle_manager._infer_rejection_reason(explanation)
        
        assert inferred_reason == RejectionReason.INCOMPLETE_DOCUMENTS

    @pytest.mark.asyncio
    async def test_infer_ineligible(self, lifecycle_manager):
        """Test inferring ineligible rejection reason"""
        app_id = "APP-INFER-002"
        
        await lifecycle_manager.send_outcome_notification(
            application_id=app_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.INELIGIBLE
        )
        
        explanation = await lifecycle_manager.get_outcome_explanation(app_id)
        inferred_reason = lifecycle_manager._infer_rejection_reason(explanation)
        
        assert inferred_reason == RejectionReason.INELIGIBLE

    @pytest.mark.asyncio
    async def test_infer_duplicate(self, lifecycle_manager):
        """Test inferring duplicate application rejection reason"""
        app_id = "APP-INFER-003"
        
        await lifecycle_manager.send_outcome_notification(
            application_id=app_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.DUPLICATE_APPLICATION
        )
        
        explanation = await lifecycle_manager.get_outcome_explanation(app_id)
        inferred_reason = lifecycle_manager._infer_rejection_reason(explanation)
        
        assert inferred_reason == RejectionReason.DUPLICATE_APPLICATION


class TestCompleteOutcomeWorkflow:
    """Test complete outcome workflow from notification to guidance"""

    @pytest.mark.asyncio
    async def test_complete_rejection_workflow(self, lifecycle_manager, sample_application_id):
        """
        Test complete workflow for rejection with appeal and resubmission.
        Validates: Requirement 6.5 (complete outcome explanation system)
        """
        # Step 1: Send rejection notification
        explanation = await lifecycle_manager.send_outcome_notification(
            application_id=sample_application_id,
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.INCOMPLETE_DOCUMENTS,
            specific_details=["Income certificate missing"]
        )
        
        assert explanation.outcome_type == OutcomeType.REJECTED
        assert explanation.appeal_eligible is True
        assert explanation.resubmission_allowed is True
        
        # Step 2: Check notification was sent
        notifications = await lifecycle_manager.get_notifications(sample_application_id)
        assert len(notifications) > 0
        assert notifications[0].notification_type == NotificationType.REJECTION
        
        # Step 3: Get appeal guidance
        appeal_guidance = await lifecycle_manager.get_appeal_guidance(sample_application_id)
        assert appeal_guidance is not None
        assert len(appeal_guidance.appeal_process) > 0
        
        # Step 4: Get resubmission guidance
        resubmission_guidance = await lifecycle_manager.get_resubmission_guidance(
            sample_application_id
        )
        assert resubmission_guidance is not None
        assert resubmission_guidance.resubmission_allowed is True
        
        # Step 5: Retrieve explanation again
        retrieved_explanation = await lifecycle_manager.get_outcome_explanation(
            sample_application_id
        )
        assert retrieved_explanation is not None
        assert retrieved_explanation.application_id == sample_application_id

    @pytest.mark.asyncio
    async def test_complete_approval_workflow(self, lifecycle_manager, sample_application_id):
        """Test complete workflow for approval"""
        # Step 1: Send approval notification
        explanation = await lifecycle_manager.send_outcome_notification(
            application_id=sample_application_id,
            outcome_type=OutcomeType.APPROVED,
            scheme_name="PM-KISAN",
            benefit_amount="₹6,000 per year"
        )
        
        assert explanation.outcome_type == OutcomeType.APPROVED
        assert explanation.appeal_eligible is False
        assert explanation.resubmission_allowed is False
        
        # Step 2: Check notification was sent
        notifications = await lifecycle_manager.get_notifications(sample_application_id)
        assert len(notifications) > 0
        assert notifications[0].notification_type == NotificationType.APPROVAL
        
        # Step 3: Verify appeal guidance is not available
        appeal_guidance = await lifecycle_manager.get_appeal_guidance(sample_application_id)
        assert appeal_guidance is None
        
        # Step 4: Verify resubmission guidance is not available
        resubmission_guidance = await lifecycle_manager.get_resubmission_guidance(
            sample_application_id
        )
        assert resubmission_guidance is None


class TestMultipleApplications:
    """Test handling multiple applications with different outcomes"""

    @pytest.mark.asyncio
    async def test_multiple_applications_different_outcomes(self, lifecycle_manager):
        """Test handling multiple applications with different outcomes"""
        app_ids = ["APP-MULTI-001", "APP-MULTI-002", "APP-MULTI-003"]
        
        # Send different outcomes
        await lifecycle_manager.send_outcome_notification(
            application_id=app_ids[0],
            outcome_type=OutcomeType.APPROVED
        )
        
        await lifecycle_manager.send_outcome_notification(
            application_id=app_ids[1],
            outcome_type=OutcomeType.REJECTED,
            rejection_reason=RejectionReason.INCOMPLETE_DOCUMENTS
        )
        
        await lifecycle_manager.send_outcome_notification(
            application_id=app_ids[2],
            outcome_type=OutcomeType.PARTIALLY_APPROVED
        )
        
        # Verify each has correct outcome
        explanation_1 = await lifecycle_manager.get_outcome_explanation(app_ids[0])
        explanation_2 = await lifecycle_manager.get_outcome_explanation(app_ids[1])
        explanation_3 = await lifecycle_manager.get_outcome_explanation(app_ids[2])
        
        assert explanation_1.outcome_type == OutcomeType.APPROVED
        assert explanation_2.outcome_type == OutcomeType.REJECTED
        assert explanation_3.outcome_type == OutcomeType.PARTIALLY_APPROVED
        
        # Verify notifications are separate
        notifications_1 = await lifecycle_manager.get_notifications(app_ids[0])
        notifications_2 = await lifecycle_manager.get_notifications(app_ids[1])
        notifications_3 = await lifecycle_manager.get_notifications(app_ids[2])
        
        assert len(notifications_1) > 0
        assert len(notifications_2) > 0
        assert len(notifications_3) > 0
