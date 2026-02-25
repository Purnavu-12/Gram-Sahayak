"""
Property-Based Tests for Application Tracker Service
**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

Property 11: Complete Application Lifecycle Management
For any application submission, the Application_Tracker should:
1. Handle submission to correct portals (Requirement 6.1)
2. Provide confirmation details (Requirement 6.2)
3. Track status updates (Requirement 6.3)
4. Notify of additional requirements (Requirement 6.4)
5. Explain final outcomes with clear reasoning (Requirement 6.5)
"""
import pytest
import sys
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from government_portal_integration import (
    GovernmentPortalIntegration,
    PortalType,
    ApplicationStatus
)
from lifecycle_management import (
    LifecycleManager,
    NotificationType,
    NotificationPriority
)
from outcome_explanation import (
    OutcomeType,
    RejectionReason
)


# Custom strategies for generating valid test data
@st.composite
def portal_type_strategy(draw):
    """Generate valid portal types"""
    return draw(st.sampled_from(list(PortalType)))


@st.composite
def application_data_strategy(draw):
    """Generate valid application data"""
    schemes = ["PM-KISAN", "MGNREGA", "PM-FASAL-BIMA", "WIDOW-PENSION", "OLD-AGE-PENSION"]
    
    return {
        "scheme_id": draw(st.sampled_from(schemes)),
        "scheme_type": draw(st.sampled_from(["pension", "subsidy", "loan", "certificate", "registration"])),
        "applicant": {
            "name": draw(st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=("L",)))),
            "aadhaar": f"{draw(st.integers(min_value=1000, max_value=9999))}-{draw(st.integers(min_value=1000, max_value=9999))}-{draw(st.integers(min_value=1000, max_value=9999))}",
            "phone": f"+91-{draw(st.integers(min_value=7000000000, max_value=9999999999))}",
            "village": draw(st.text(min_size=3, max_size=30, alphabet=st.characters(whitelist_categories=("L",)))),
            "district": draw(st.text(min_size=3, max_size=30, alphabet=st.characters(whitelist_categories=("L",)))),
            "state": draw(st.sampled_from(["Uttar Pradesh", "Bihar", "Maharashtra", "Tamil Nadu", "Karnataka"]))
        },
        "bank_details": {
            "account_number": str(draw(st.integers(min_value=1000000000, max_value=9999999999))),
            "ifsc": f"SBIN000{draw(st.integers(min_value=1000, max_value=9999))}",
            "bank_name": draw(st.sampled_from(["State Bank of India", "Punjab National Bank", "Bank of Baroda"]))
        }
    }


@st.composite
def credentials_strategy(draw, portal_type: PortalType):
    """Generate valid credentials based on portal type"""
    if portal_type in (PortalType.MY_SCHEME, PortalType.DIGILOCKER):
        return {
            "client_id": draw(st.text(min_size=10, max_size=20, alphabet=st.characters(whitelist_categories=("L", "N")))),
            "client_secret": draw(st.text(min_size=20, max_size=40, alphabet=st.characters(whitelist_categories=("L", "N"))))
        }
    elif portal_type in (PortalType.E_SHRAM, PortalType.PM_KISAN, PortalType.MGNREGA):
        return {
            "api_key": draw(st.text(min_size=32, max_size=64, alphabet=st.characters(whitelist_categories=("L", "N"))))
        }
    elif portal_type in (PortalType.UMANG, PortalType.AYUSHMAN_BHARAT):
        return {
            "user_id": draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=("L", "N")))),
            "secret": draw(st.text(min_size=10, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N"))))
        }
    else:  # GENERIC or others
        return {
            "username": draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=("L", "N")))),
            "password": draw(st.text(min_size=8, max_size=20, alphabet=st.characters(whitelist_categories=("L", "N"))))
        }


@st.composite
def rejection_reason_strategy(draw):
    """Generate valid rejection reasons"""
    return draw(st.sampled_from(list(RejectionReason)))


@st.composite
def additional_info_items_strategy(draw):
    """Generate valid additional information items"""
    num_items = draw(st.integers(min_value=1, max_value=5))
    items = []
    
    for _ in range(num_items):
        items.append({
            "name": draw(st.sampled_from([
                "Income Certificate", "Bank Statement", "Land Records",
                "Caste Certificate", "Residence Proof", "Age Proof"
            ])),
            "description": draw(st.text(min_size=10, max_size=100, alphabet=st.characters(whitelist_categories=("L", "P"))))
        })
    
    return items


@pytest.mark.asyncio
@given(
    portal_type=portal_type_strategy(),
    application_data=application_data_strategy(),
    data=st.data()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_complete_application_lifecycle(portal_type: PortalType, application_data: Dict[str, Any], data):
    """
    **Feature: gram-sahayak, Property 11: Complete Application Lifecycle Management**
    **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
    
    Property: For any application submission, the Application_Tracker should handle:
    1. Submission to correct portals (Requirement 6.1)
    2. Confirmation details (Requirement 6.2)
    3. Status updates (Requirement 6.3)
    4. Additional requirements (Requirement 6.4)
    5. Final outcomes with clear reasoning (Requirement 6.5)
    """
    portal_integration = GovernmentPortalIntegration()
    lifecycle_manager = LifecycleManager()
    
    # Generate credentials for the portal type
    credentials = data.draw(credentials_strategy(portal_type))
    
    # 1. Test submission to correct portal (Requirement 6.1)
    submission_result = await portal_integration.submit_application(
        portal_type,
        application_data,
        credentials
    )
    
    # Property 1: Submission must succeed or fail gracefully
    assert "success" in submission_result, "Submission result must include success field"
    assert "portal" in submission_result, "Submission result must include portal field"
    assert submission_result["portal"] == portal_type.value, "Portal must match request"
    
    if not submission_result["success"]:
        # If submission fails, that's acceptable - just verify error handling
        await portal_integration.close()
        return
    
    # Property 2: Successful submission must provide confirmation details (Requirement 6.2)
    assert "submission_id" in submission_result, "Must provide submission_id"
    assert "confirmation_number" in submission_result, "Must provide confirmation_number"
    assert "application_id" in submission_result, "Must provide application_id"
    assert "submitted_at" in submission_result, "Must provide submission timestamp"
    assert "expected_processing_time" in submission_result, "Must provide expected processing time"
    
    conf_num = submission_result["confirmation_number"]
    app_id = submission_result["application_id"]
    
    # Property 3: Confirmation number must be non-empty and properly formatted
    assert isinstance(conf_num, str) and len(conf_num) > 0, "Confirmation number must be non-empty string"
    assert len(conf_num) <= 12, "Confirmation number should be reasonable length"
    
    # 2. Test timeline creation with confirmation details (Requirement 6.2)
    timeline = await lifecycle_manager.create_timeline(
        confirmation_number=conf_num,
        application_id=app_id,
        portal_type=portal_type.value,
        scheme_type=application_data.get("scheme_type")
    )
    
    # Property 4: Timeline must be created with all required fields
    assert timeline.confirmation_number == conf_num, "Timeline confirmation number must match"
    assert timeline.application_id == app_id, "Timeline application ID must match"
    assert timeline.estimated_days > 0, "Estimated days must be positive"
    assert timeline.expected_completion > timeline.submitted_at, \
        "Expected completion must be after submission"
    assert len(timeline.milestones) > 0, "Timeline must have at least one milestone"
    
    # Property 5: First milestone must be submission and completed
    first_milestone = timeline.milestones[0]
    assert first_milestone["stage"] == "submission", "First milestone must be submission"
    assert first_milestone["completed"] is True, "Submission milestone must be completed"
    
    # 3. Test status tracking (Requirement 6.3)
    status_result = await portal_integration.get_application_status(
        portal_type,
        app_id,
        credentials
    )
    
    # Property 6: Status retrieval must succeed
    assert status_result["success"] is True, "Status retrieval must succeed"
    assert status_result["application_id"] == app_id, "Status application ID must match"
    assert "status" in status_result, "Status result must include status"
    assert "next_steps" in status_result, "Status result must include next_steps"
    assert isinstance(status_result["next_steps"], list), "Next steps must be a list"
    assert len(status_result["next_steps"]) > 0, "Next steps must not be empty"
    
    # 4. Test additional information request handling (Requirement 6.4)
    required_items = data.draw(additional_info_items_strategy())
    
    info_request = await lifecycle_manager.create_additional_info_request(
        application_id=app_id,
        required_items=required_items,
        due_days=7
    )
    
    # Property 7: Additional info request must be created with all fields
    assert info_request.application_id == app_id, "Request application ID must match"
    assert len(info_request.items) == len(required_items), "Request items must match"
    assert info_request.status == "pending", "Initial status must be pending"
    assert info_request.due_date > info_request.requested_at, "Due date must be after request date"
    
    # 5. Test outcome explanation (Requirement 6.5)
    rejection_reason = data.draw(rejection_reason_strategy())
    
    rejection_explanation = await lifecycle_manager.send_outcome_notification(
        application_id=app_id,
        outcome_type=OutcomeType.REJECTED,
        rejection_reason=rejection_reason
    )
    
    # Property 8: Rejection explanation must have all required fields
    assert rejection_explanation.application_id == app_id, "Explanation application ID must match"
    assert rejection_explanation.outcome_type == OutcomeType.REJECTED, "Outcome type must be rejected"
    assert len(rejection_explanation.primary_reason) > 0, "Must have primary reason"
    assert len(rejection_explanation.detailed_explanation) > 0, "Must have detailed explanation"
    assert len(rejection_explanation.next_steps) > 0, "Must have next steps"
    assert isinstance(rejection_explanation.appeal_eligible, bool), "Appeal eligibility must be boolean"
    assert isinstance(rejection_explanation.resubmission_allowed, bool), "Resubmission allowed must be boolean"
    
    # Property 9: If appeal eligible, must have deadline
    if rejection_explanation.appeal_eligible:
        assert rejection_explanation.appeal_deadline is not None, "Appeal eligible must have deadline"
        assert rejection_explanation.appeal_deadline > datetime.now(), "Appeal deadline must be in future"
    
    # Property 10: Rejection must include contact information
    assert rejection_explanation.contact_info is not None, "Must include contact info"
    assert len(rejection_explanation.contact_info) > 0, "Contact info must not be empty"
    
    # Cleanup
    await portal_integration.close()


@pytest.mark.asyncio
@given(
    portal_type=portal_type_strategy(),
    application_data=application_data_strategy(),
    data=st.data()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_submission_idempotency(portal_type: PortalType, application_data: Dict[str, Any], data):
    """
    **Feature: gram-sahayak, Property 11: Complete Application Lifecycle - Uniqueness**
    **Validates: Requirement 6.1**
    
    Property: Multiple submissions must generate unique identifiers
    """
    portal_integration = GovernmentPortalIntegration()
    credentials = data.draw(credentials_strategy(portal_type))
    
    # Submit same application twice
    result1 = await portal_integration.submit_application(
        portal_type,
        application_data,
        credentials
    )
    
    result2 = await portal_integration.submit_application(
        portal_type,
        application_data,
        credentials
    )
    
    if result1["success"] and result2["success"]:
        # Property 1: Submission IDs must be unique
        assert result1["submission_id"] != result2["submission_id"], \
            "Submission IDs must be unique"
        
        # Property 2: Confirmation numbers must be unique
        assert result1["confirmation_number"] != result2["confirmation_number"], \
            "Confirmation numbers must be unique"
        
        # Property 3: Application IDs must be unique
        assert result1["application_id"] != result2["application_id"], \
            "Application IDs must be unique"
    
    await portal_integration.close()



@pytest.mark.asyncio
@given(
    portal_type=portal_type_strategy(),
    application_data=application_data_strategy(),
    data=st.data()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_timeline_consistency(portal_type: PortalType, application_data: Dict[str, Any], data):
    """
    **Feature: gram-sahayak, Property 11: Complete Application Lifecycle - Timeline**
    **Validates: Requirement 6.2**
    
    Property: Timeline must be consistent and logical
    """
    portal_integration = GovernmentPortalIntegration()
    lifecycle_manager = LifecycleManager()
    credentials = data.draw(credentials_strategy(portal_type))
    
    # Submit application
    submission_result = await portal_integration.submit_application(
        portal_type,
        application_data,
        credentials
    )
    
    if submission_result["success"]:
        app_id = submission_result["application_id"]
        conf_num = submission_result["confirmation_number"]
        
        # Create timeline
        timeline = await lifecycle_manager.create_timeline(
            confirmation_number=conf_num,
            application_id=app_id,
            portal_type=portal_type.value,
            scheme_type=application_data.get("scheme_type")
        )
        
        # Property 1: Milestones must be in chronological order
        for i in range(len(timeline.milestones) - 1):
            current_date = datetime.fromisoformat(timeline.milestones[i]["expected_date"].replace('Z', '+00:00'))
            next_date = datetime.fromisoformat(timeline.milestones[i + 1]["expected_date"].replace('Z', '+00:00'))
            assert current_date <= next_date, "Milestones must be in chronological order"
        
        # Property 2: Last milestone date must match expected completion
        last_milestone_date = datetime.fromisoformat(
            timeline.milestones[-1]["expected_date"].replace('Z', '+00:00')
        )
        # Allow small difference due to timezone handling
        time_diff = abs((last_milestone_date - timeline.expected_completion).total_seconds())
        assert time_diff < 60, "Last milestone must match expected completion"
        
        # Property 3: Estimated days must match date difference
        actual_days = (timeline.expected_completion - timeline.submitted_at).days
        assert abs(actual_days - timeline.estimated_days) <= 1, \
            "Estimated days must match actual date difference"
        
        # Property 4: Timeline update must maintain consistency
        updated_timeline = await lifecycle_manager.update_timeline(
            application_id=app_id,
            current_stage="acknowledgment"
        )
        
        assert updated_timeline.application_id == app_id, "Application ID must remain same"
        assert updated_timeline.confirmation_number == conf_num, "Confirmation number must remain same"
        assert updated_timeline.submitted_at == timeline.submitted_at, "Submission date must remain same"
        
        # Property 5: Updated milestone must be marked complete
        ack_milestone = next(m for m in updated_timeline.milestones if m["stage"] == "acknowledgment")
        assert ack_milestone["completed"] is True, "Updated milestone must be completed"
        assert "completed_at" in ack_milestone, "Completed milestone must have completion time"
    
    await portal_integration.close()


@pytest.mark.asyncio
@given(
    portal_type=portal_type_strategy(),
    application_data=application_data_strategy(),
    data=st.data()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_notification_completeness(portal_type: PortalType, application_data: Dict[str, Any], data):
    """
    **Feature: gram-sahayak, Property 11: Complete Application Lifecycle - Notifications**
    **Validates: Requirements 6.2, 6.4**
    
    Property: All lifecycle events must generate appropriate notifications
    """
    portal_integration = GovernmentPortalIntegration()
    lifecycle_manager = LifecycleManager()
    credentials = data.draw(credentials_strategy(portal_type))
    
    # Submit application
    submission_result = await portal_integration.submit_application(
        portal_type,
        application_data,
        credentials
    )
    
    if submission_result["success"]:
        app_id = submission_result["application_id"]
        conf_num = submission_result["confirmation_number"]
        
        # Create timeline (generates initial notification)
        await lifecycle_manager.create_timeline(
            confirmation_number=conf_num,
            application_id=app_id,
            portal_type=portal_type.value
        )
        
        # Property 1: Initial notification must exist
        notifications = await lifecycle_manager.get_notifications(app_id)
        assert len(notifications) > 0, "Must have initial notification"
        
        # Property 2: All notifications must have required fields
        for notif in notifications:
            assert notif.notification_id is not None, "Must have notification ID"
            assert notif.application_id == app_id, "Must have correct application ID"
            assert notif.notification_type is not None, "Must have notification type"
            assert notif.priority is not None, "Must have priority"
            assert len(notif.title) > 0, "Must have non-empty title"
            assert len(notif.message) > 0, "Must have non-empty message"
            assert notif.created_at is not None, "Must have creation timestamp"
            assert isinstance(notif.read, bool), "Read flag must be boolean"
            assert isinstance(notif.action_required, bool), "Action required must be boolean"
        
        # Property 3: Can mark notifications as read
        first_notif = notifications[0]
        success = await lifecycle_manager.mark_notification_read(
            app_id,
            first_notif.notification_id
        )
        assert success is True, "Must be able to mark notification as read"
        
        # Property 4: Unread filter must work correctly
        unread = await lifecycle_manager.get_notifications(app_id, unread_only=True)
        assert all(not n.read for n in unread), "Unread filter must return only unread"
        
        # Property 5: Additional info request must create notification
        required_items = [{"name": "Test Doc", "description": "Test description"}]
        await lifecycle_manager.create_additional_info_request(
            application_id=app_id,
            required_items=required_items,
            due_days=7
        )
        
        all_notifications = await lifecycle_manager.get_notifications(app_id)
        info_notifications = [n for n in all_notifications 
                             if n.notification_type == NotificationType.ADDITIONAL_INFO_REQUIRED]
        assert len(info_notifications) > 0, "Additional info request must create notification"
        
        # Property 6: Urgent notifications must have correct priority
        urgent_notif = info_notifications[0]
        assert urgent_notif.priority == NotificationPriority.URGENT, \
            "Additional info notification must be urgent"
        assert urgent_notif.action_required is True, \
            "Additional info notification must require action"
    
    await portal_integration.close()


@pytest.mark.asyncio
@given(
    rejection_reason=rejection_reason_strategy()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_outcome_explanation_completeness(rejection_reason: RejectionReason):
    """
    **Feature: gram-sahayak, Property 11: Complete Application Lifecycle - Outcomes**
    **Validates: Requirement 6.5**
    
    Property: All rejection reasons must have complete explanations and guidance
    """
    lifecycle_manager = LifecycleManager()
    app_id = f"TEST-APP-{rejection_reason.value}"
    
    # Send rejection notification
    explanation = await lifecycle_manager.send_outcome_notification(
        application_id=app_id,
        outcome_type=OutcomeType.REJECTED,
        rejection_reason=rejection_reason,
        specific_details=["Test detail 1", "Test detail 2"]
    )
    
    # Property 1: Explanation must have all required fields
    assert explanation.application_id == app_id, "Application ID must match"
    assert explanation.outcome_type == OutcomeType.REJECTED, "Outcome type must be rejected"
    assert len(explanation.primary_reason) > 0, "Must have primary reason"
    assert len(explanation.detailed_explanation) > 50, \
        "Detailed explanation must be substantial (>50 chars)"
    assert len(explanation.next_steps) > 0, "Must have next steps"
    
    # Property 2: Next steps must be actionable
    for step in explanation.next_steps:
        assert len(step) > 10, "Each step must be substantial (>10 chars)"
    
    # Property 3: Appeal/resubmission flags must be consistent
    if explanation.appeal_eligible:
        assert explanation.appeal_deadline is not None, \
            "Appeal eligible must have deadline"
        # Appeal deadline must be in future
        assert explanation.appeal_deadline > datetime.now(), \
            "Appeal deadline must be in future"
        
        # Must mention appeal in next steps
        next_steps_text = " ".join(explanation.next_steps).lower()
        assert "appeal" in next_steps_text, "Next steps must mention appeal when eligible"
    
    if explanation.resubmission_allowed:
        # Must mention resubmission in next steps
        next_steps_text = " ".join(explanation.next_steps).lower()
        assert any(word in next_steps_text for word in ["resubmit", "correct", "fix"]), \
            "Next steps must mention resubmission when allowed"
    
    # Property 4: Contact info must be provided
    assert explanation.contact_info is not None, "Must provide contact info"
    assert "helpline" in explanation.contact_info, "Must include helpline"
    
    # Property 5: Appeal guidance must be available when eligible
    if explanation.appeal_eligible:
        appeal_guidance = await lifecycle_manager.get_appeal_guidance(app_id)
        
        assert appeal_guidance is not None, "Appeal guidance must be available"
        assert len(appeal_guidance.appeal_process) >= 3, \
            "Appeal process must have at least 3 steps"
        assert len(appeal_guidance.required_documents) > 0, \
            "Must specify required documents"
        assert len(appeal_guidance.submission_methods) > 0, \
            "Must specify submission methods"
        assert len(appeal_guidance.tips) > 0, "Must provide tips"
        
        # All process steps must be detailed
        for step in appeal_guidance.appeal_process:
            assert len(step["description"]) > 20, \
                "Process step description must be detailed (>20 chars)"
    
    # Property 6: Resubmission guidance must be available when allowed
    if explanation.resubmission_allowed:
        resubmission_guidance = await lifecycle_manager.get_resubmission_guidance(app_id)
        
        assert resubmission_guidance is not None, "Resubmission guidance must be available"
        assert resubmission_guidance.resubmission_allowed is True, \
            "Resubmission must be allowed"
        assert len(resubmission_guidance.corrections_needed) > 0, \
            "Must specify corrections needed"
        assert len(resubmission_guidance.resubmission_process) >= 3, \
            "Resubmission process must have at least 3 steps"
        assert len(resubmission_guidance.tips) > 0, "Must provide tips"
        
        # Waiting period must be reasonable
        assert resubmission_guidance.waiting_period is not None, "Must have waiting period"
        assert 0 <= resubmission_guidance.waiting_period <= 365, \
            "Waiting period must be reasonable (0-365 days)"


@pytest.mark.asyncio
@given(
    portal_type=portal_type_strategy(),
    application_data=application_data_strategy(),
    data=st.data()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_status_consistency(portal_type: PortalType, application_data: Dict[str, Any], data):
    """
    **Feature: gram-sahayak, Property 11: Complete Application Lifecycle - Status Tracking**
    **Validates: Requirement 6.3**
    
    Property: Status tracking must be consistent and deterministic
    """
    portal_integration = GovernmentPortalIntegration()
    credentials = data.draw(credentials_strategy(portal_type))
    
    # Submit application
    submission_result = await portal_integration.submit_application(
        portal_type,
        application_data,
        credentials
    )
    
    if submission_result["success"]:
        app_id = submission_result["application_id"]
        
        # Get status multiple times
        status1 = await portal_integration.get_application_status(
            portal_type,
            app_id,
            credentials
        )
        
        status2 = await portal_integration.get_application_status(
            portal_type,
            app_id,
            credentials
        )
        
        if status1["success"] and status2["success"]:
            # Property 1: Status must be consistent for same application
            assert status1["status"] == status2["status"], \
                "Status must be consistent across calls"
            
            # Property 2: Application ID must match
            assert status1["application_id"] == app_id, "Application ID must match"
            assert status2["application_id"] == app_id, "Application ID must match"
            
            # Property 3: Progress must be consistent
            assert status1["progress_percentage"] == status2["progress_percentage"], \
                "Progress must be consistent"
            
            # Property 4: Status description must be consistent
            assert status1["status_description"] == status2["status_description"], \
                "Status description must be consistent"
    
    await portal_integration.close()
