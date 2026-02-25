"""
Unit tests for Application Lifecycle Management Service

Tests confirmation tracking, timeline management, notifications,
and additional information request handling.

Validates: Requirements 6.2, 6.4
"""

import pytest
from datetime import datetime, timedelta
from lifecycle_management import (
    LifecycleManager,
    NotificationType,
    NotificationPriority,
    ApplicationTimeline,
    Notification,
    AdditionalInfoRequest
)


@pytest.fixture
def lifecycle_manager():
    """Create a lifecycle manager instance for testing"""
    return LifecycleManager()


@pytest.fixture
def sample_application():
    """Sample application data"""
    return {
        "confirmation_number": "MYS123456789",
        "application_id": "MYSCHEME-1705315200",
        "portal_type": "myscheme",
        "scheme_type": "pension"
    }


class TestTimelineCreation:
    """Test timeline creation and tracking"""

    @pytest.mark.asyncio
    async def test_create_timeline_basic(self, lifecycle_manager, sample_application):
        """Test basic timeline creation"""
        timeline = await lifecycle_manager.create_timeline(
            confirmation_number=sample_application["confirmation_number"],
            application_id=sample_application["application_id"],
            portal_type=sample_application["portal_type"]
        )
        
        assert isinstance(timeline, ApplicationTimeline)
        assert timeline.confirmation_number == sample_application["confirmation_number"]
        assert timeline.application_id == sample_application["application_id"]
        assert timeline.estimated_days > 0
        assert timeline.expected_completion > timeline.submitted_at
        assert len(timeline.milestones) > 0

    @pytest.mark.asyncio
    async def test_create_timeline_with_scheme_type(self, lifecycle_manager, sample_application):
        """Test timeline creation with scheme type adjustment"""
        timeline = await lifecycle_manager.create_timeline(
            confirmation_number=sample_application["confirmation_number"],
            application_id=sample_application["application_id"],
            portal_type=sample_application["portal_type"],
            scheme_type="pension"
        )
        
        # Pension schemes should have additional processing time
        assert timeline.estimated_days >= 21  # Base time for myscheme

    @pytest.mark.asyncio
    async def test_timeline_milestones_structure(self, lifecycle_manager, sample_application):
        """Test that milestones have correct structure"""
        timeline = await lifecycle_manager.create_timeline(
            confirmation_number=sample_application["confirmation_number"],
            application_id=sample_application["application_id"],
            portal_type=sample_application["portal_type"]
        )
        
        # Check milestone structure
        for milestone in timeline.milestones:
            assert "stage" in milestone
            assert "title" in milestone
            assert "description" in milestone
            assert "expected_date" in milestone
            assert "completed" in milestone
        
        # First milestone (submission) should be completed
        assert timeline.milestones[0]["completed"] is True
        assert timeline.milestones[0]["stage"] == "submission"

    @pytest.mark.asyncio
    async def test_timeline_creates_notification(self, lifecycle_manager, sample_application):
        """Test that timeline creation sends initial notification"""
        await lifecycle_manager.create_timeline(
            confirmation_number=sample_application["confirmation_number"],
            application_id=sample_application["application_id"],
            portal_type=sample_application["portal_type"]
        )
        
        # Check that notification was created
        notifications = await lifecycle_manager.get_notifications(
            sample_application["application_id"]
        )
        
        assert len(notifications) > 0
        assert notifications[0].notification_type == NotificationType.STATUS_UPDATE
        assert sample_application["confirmation_number"] in notifications[0].message


class TestTimelineRetrieval:
    """Test timeline retrieval and updates"""

    @pytest.mark.asyncio
    async def test_get_timeline(self, lifecycle_manager, sample_application):
        """Test retrieving a timeline"""
        # Create timeline
        created_timeline = await lifecycle_manager.create_timeline(
            confirmation_number=sample_application["confirmation_number"],
            application_id=sample_application["application_id"],
            portal_type=sample_application["portal_type"]
        )
        
        # Retrieve timeline
        retrieved_timeline = await lifecycle_manager.get_timeline(
            sample_application["application_id"]
        )
        
        assert retrieved_timeline is not None
        assert retrieved_timeline.application_id == created_timeline.application_id
        assert retrieved_timeline.confirmation_number == created_timeline.confirmation_number

    @pytest.mark.asyncio
    async def test_get_nonexistent_timeline(self, lifecycle_manager):
        """Test retrieving a timeline that doesn't exist"""
        timeline = await lifecycle_manager.get_timeline("NONEXISTENT-123")
        assert timeline is None

    @pytest.mark.asyncio
    async def test_update_timeline_milestone(self, lifecycle_manager, sample_application):
        """Test updating timeline with milestone completion"""
        # Create timeline
        await lifecycle_manager.create_timeline(
            confirmation_number=sample_application["confirmation_number"],
            application_id=sample_application["application_id"],
            portal_type=sample_application["portal_type"]
        )
        
        # Update timeline
        updated_timeline = await lifecycle_manager.update_timeline(
            application_id=sample_application["application_id"],
            current_stage="acknowledgment"
        )
        
        # Check that milestone was marked complete
        acknowledgment_milestone = next(
            m for m in updated_timeline.milestones if m["stage"] == "acknowledgment"
        )
        assert acknowledgment_milestone["completed"] is True
        assert "completed_at" in acknowledgment_milestone

    @pytest.mark.asyncio
    async def test_update_timeline_expected_completion(self, lifecycle_manager, sample_application):
        """Test updating expected completion date"""
        # Create timeline
        original_timeline = await lifecycle_manager.create_timeline(
            confirmation_number=sample_application["confirmation_number"],
            application_id=sample_application["application_id"],
            portal_type=sample_application["portal_type"]
        )
        
        # Update with new expected completion
        new_completion = original_timeline.expected_completion + timedelta(days=7)
        updated_timeline = await lifecycle_manager.update_timeline(
            application_id=sample_application["application_id"],
            current_stage="verification",
            new_expected_completion=new_completion
        )
        
        assert updated_timeline.expected_completion == new_completion
        
        # Should create a timeline update notification
        notifications = await lifecycle_manager.get_notifications(
            sample_application["application_id"]
        )
        timeline_notifications = [
            n for n in notifications
            if n.notification_type == NotificationType.TIMELINE_UPDATE
        ]
        assert len(timeline_notifications) > 0


class TestNotifications:
    """Test notification system"""

    @pytest.mark.asyncio
    async def test_send_status_notification(self, lifecycle_manager, sample_application):
        """Test sending status update notification"""
        notification = await lifecycle_manager.send_status_notification(
            application_id=sample_application["application_id"],
            status="under_review",
            status_description="Application is under review by officials",
            next_steps=["Wait for review", "Check status regularly"]
        )
        
        assert isinstance(notification, Notification)
        assert notification.notification_type == NotificationType.STATUS_UPDATE
        assert notification.application_id == sample_application["application_id"]
        assert "under review" in notification.message.lower()
        assert "Wait for review" in notification.message

    @pytest.mark.asyncio
    async def test_notification_priority_for_urgent_status(self, lifecycle_manager, sample_application):
        """Test that urgent statuses get high priority"""
        notification = await lifecycle_manager.send_status_notification(
            application_id=sample_application["application_id"],
            status="pending_documents",
            status_description="Additional documents required",
            next_steps=["Submit documents"]
        )
        
        assert notification.priority == NotificationPriority.URGENT
        assert notification.action_required is True

    @pytest.mark.asyncio
    async def test_notification_priority_for_final_status(self, lifecycle_manager, sample_application):
        """Test that final statuses get high priority"""
        notification = await lifecycle_manager.send_status_notification(
            application_id=sample_application["application_id"],
            status="approved",
            status_description="Application approved",
            next_steps=["Wait for disbursement"]
        )
        
        assert notification.priority == NotificationPriority.HIGH

    @pytest.mark.asyncio
    async def test_get_notifications(self, lifecycle_manager, sample_application):
        """Test retrieving notifications"""
        # Send multiple notifications
        await lifecycle_manager.send_status_notification(
            application_id=sample_application["application_id"],
            status="submitted",
            status_description="Submitted",
            next_steps=[]
        )
        await lifecycle_manager.send_status_notification(
            application_id=sample_application["application_id"],
            status="under_review",
            status_description="Under review",
            next_steps=[]
        )
        
        notifications = await lifecycle_manager.get_notifications(
            sample_application["application_id"]
        )
        
        assert len(notifications) >= 2

    @pytest.mark.asyncio
    async def test_get_unread_notifications(self, lifecycle_manager, sample_application):
        """Test retrieving only unread notifications"""
        # Send notification
        await lifecycle_manager.send_status_notification(
            application_id=sample_application["application_id"],
            status="submitted",
            status_description="Submitted",
            next_steps=[]
        )
        
        # Get all notifications
        all_notifications = await lifecycle_manager.get_notifications(
            sample_application["application_id"]
        )
        
        # Mark one as read
        await lifecycle_manager.mark_notification_read(
            sample_application["application_id"],
            all_notifications[0].notification_id
        )
        
        # Get unread only
        unread = await lifecycle_manager.get_notifications(
            sample_application["application_id"],
            unread_only=True
        )
        
        assert len(unread) == len(all_notifications) - 1

    @pytest.mark.asyncio
    async def test_mark_notification_read(self, lifecycle_manager, sample_application):
        """Test marking notification as read"""
        # Send notification
        notification = await lifecycle_manager.send_status_notification(
            application_id=sample_application["application_id"],
            status="submitted",
            status_description="Submitted",
            next_steps=[]
        )
        
        assert notification.read is False
        
        # Mark as read
        success = await lifecycle_manager.mark_notification_read(
            sample_application["application_id"],
            notification.notification_id
        )
        
        assert success is True
        
        # Verify it's marked read
        notifications = await lifecycle_manager.get_notifications(
            sample_application["application_id"]
        )
        marked_notification = next(
            n for n in notifications if n.notification_id == notification.notification_id
        )
        assert marked_notification.read is True


class TestAdditionalInfoRequests:
    """Test additional information request handling"""

    @pytest.mark.asyncio
    async def test_create_additional_info_request(self, lifecycle_manager, sample_application):
        """Test creating additional information request"""
        required_items = [
            {
                "name": "Income Certificate",
                "description": "Certificate from Tehsildar showing annual income"
            },
            {
                "name": "Bank Statement",
                "description": "Last 6 months bank statement"
            }
        ]
        
        request = await lifecycle_manager.create_additional_info_request(
            application_id=sample_application["application_id"],
            required_items=required_items,
            due_days=7
        )
        
        assert isinstance(request, AdditionalInfoRequest)
        assert request.application_id == sample_application["application_id"]
        assert len(request.items) == 2
        assert request.status == "pending"
        assert request.due_date > request.requested_at

    @pytest.mark.asyncio
    async def test_additional_info_request_creates_notification(self, lifecycle_manager, sample_application):
        """Test that additional info request creates urgent notification"""
        required_items = [
            {"name": "Document", "description": "Required document"}
        ]
        
        await lifecycle_manager.create_additional_info_request(
            application_id=sample_application["application_id"],
            required_items=required_items
        )
        
        # Check notification
        notifications = await lifecycle_manager.get_notifications(
            sample_application["application_id"]
        )
        
        info_notifications = [
            n for n in notifications
            if n.notification_type == NotificationType.ADDITIONAL_INFO_REQUIRED
        ]
        
        assert len(info_notifications) > 0
        assert info_notifications[0].priority == NotificationPriority.URGENT
        assert info_notifications[0].action_required is True

    @pytest.mark.asyncio
    async def test_get_additional_info_requests(self, lifecycle_manager, sample_application):
        """Test retrieving additional info requests"""
        required_items = [{"name": "Document", "description": "Required"}]
        
        # Create request
        await lifecycle_manager.create_additional_info_request(
            application_id=sample_application["application_id"],
            required_items=required_items
        )
        
        # Retrieve requests
        requests = await lifecycle_manager.get_additional_info_requests(
            sample_application["application_id"]
        )
        
        assert len(requests) > 0
        assert requests[0].application_id == sample_application["application_id"]

    @pytest.mark.asyncio
    async def test_get_additional_info_requests_by_status(self, lifecycle_manager, sample_application):
        """Test filtering requests by status"""
        required_items = [{"name": "Document", "description": "Required"}]
        
        # Create request
        await lifecycle_manager.create_additional_info_request(
            application_id=sample_application["application_id"],
            required_items=required_items
        )
        
        # Get pending requests
        pending = await lifecycle_manager.get_additional_info_requests(
            sample_application["application_id"],
            status="pending"
        )
        
        assert len(pending) > 0
        assert all(r.status == "pending" for r in pending)

    @pytest.mark.asyncio
    async def test_submit_additional_info(self, lifecycle_manager, sample_application):
        """Test submitting additional information"""
        required_items = [{"name": "Document", "description": "Required"}]
        
        # Create request
        request = await lifecycle_manager.create_additional_info_request(
            application_id=sample_application["application_id"],
            required_items=required_items
        )
        
        # Submit info
        submitted_data = {"document": "data"}
        updated_request = await lifecycle_manager.submit_additional_info(
            request_id=request.request_id,
            application_id=sample_application["application_id"],
            submitted_data=submitted_data
        )
        
        assert updated_request.status == "submitted"
        assert updated_request.submitted_at is not None

    @pytest.mark.asyncio
    async def test_submit_additional_info_creates_notification(self, lifecycle_manager, sample_application):
        """Test that submitting info creates confirmation notification"""
        required_items = [{"name": "Document", "description": "Required"}]
        
        # Create and submit
        request = await lifecycle_manager.create_additional_info_request(
            application_id=sample_application["application_id"],
            required_items=required_items
        )
        
        await lifecycle_manager.submit_additional_info(
            request_id=request.request_id,
            application_id=sample_application["application_id"],
            submitted_data={"document": "data"}
        )
        
        # Check for confirmation notification
        notifications = await lifecycle_manager.get_notifications(
            sample_application["application_id"]
        )
        
        confirmation_notifications = [
            n for n in notifications
            if "submitted successfully" in n.message.lower()
        ]
        
        assert len(confirmation_notifications) > 0

    @pytest.mark.asyncio
    async def test_submit_additional_info_invalid_request(self, lifecycle_manager, sample_application):
        """Test submitting info for invalid request raises error"""
        with pytest.raises(ValueError, match="not found"):
            await lifecycle_manager.submit_additional_info(
                request_id="INVALID-123",
                application_id=sample_application["application_id"],
                submitted_data={"data": "value"}
            )

    @pytest.mark.asyncio
    async def test_submit_additional_info_already_submitted(self, lifecycle_manager, sample_application):
        """Test submitting info for already submitted request raises error"""
        required_items = [{"name": "Document", "description": "Required"}]
        
        # Create and submit
        request = await lifecycle_manager.create_additional_info_request(
            application_id=sample_application["application_id"],
            required_items=required_items
        )
        
        await lifecycle_manager.submit_additional_info(
            request_id=request.request_id,
            application_id=sample_application["application_id"],
            submitted_data={"document": "data"}
        )
        
        # Try to submit again
        with pytest.raises(ValueError, match="not pending"):
            await lifecycle_manager.submit_additional_info(
                request_id=request.request_id,
                application_id=sample_application["application_id"],
                submitted_data={"document": "data2"}
            )


class TestProcessingTimeCalculation:
    """Test processing time calculation logic"""

    def test_calculate_processing_time_different_portals(self, lifecycle_manager):
        """Test that different portals have different processing times"""
        myscheme_time = lifecycle_manager._calculate_processing_time("myscheme")
        eshram_time = lifecycle_manager._calculate_processing_time("eshram")
        pmkisan_time = lifecycle_manager._calculate_processing_time("pmkisan")
        
        assert myscheme_time > 0
        assert eshram_time > 0
        assert pmkisan_time > 0
        # Different portals should have different times
        assert not (myscheme_time == eshram_time == pmkisan_time)

    def test_calculate_processing_time_with_scheme_adjustment(self, lifecycle_manager):
        """Test that scheme type adjusts processing time"""
        base_time = lifecycle_manager._calculate_processing_time("myscheme")
        pension_time = lifecycle_manager._calculate_processing_time("myscheme", "pension")
        certificate_time = lifecycle_manager._calculate_processing_time("myscheme", "certificate")
        
        # Pension should take longer
        assert pension_time > base_time
        # Certificate should be faster
        assert certificate_time < base_time

    def test_calculate_processing_time_minimum(self, lifecycle_manager):
        """Test that processing time has minimum of 1 day"""
        # Even with fast certificate on fast portal
        time = lifecycle_manager._calculate_processing_time("digilocker", "certificate")
        assert time >= 1


class TestNotificationSubscription:
    """Test notification subscription system"""

    @pytest.mark.asyncio
    async def test_subscribe_to_notifications(self, lifecycle_manager, sample_application):
        """Test subscribing to notifications"""
        received_notifications = []
        
        def callback(notification):
            received_notifications.append(notification)
        
        # Subscribe
        lifecycle_manager.subscribe_to_notifications(
            sample_application["application_id"],
            callback
        )
        
        # Send notification
        await lifecycle_manager.send_status_notification(
            application_id=sample_application["application_id"],
            status="submitted",
            status_description="Submitted",
            next_steps=[]
        )
        
        # Check callback was called
        assert len(received_notifications) > 0

    @pytest.mark.asyncio
    async def test_unsubscribe_from_notifications(self, lifecycle_manager, sample_application):
        """Test unsubscribing from notifications"""
        received_notifications = []
        
        def callback(notification):
            received_notifications.append(notification)
        
        # Subscribe and unsubscribe
        lifecycle_manager.subscribe_to_notifications(
            sample_application["application_id"],
            callback
        )
        lifecycle_manager.unsubscribe_from_notifications(
            sample_application["application_id"],
            callback
        )
        
        # Send notification
        await lifecycle_manager.send_status_notification(
            application_id=sample_application["application_id"],
            status="submitted",
            status_description="Submitted",
            next_steps=[]
        )
        
        # Callback should not be called
        assert len(received_notifications) == 0
