"""
Integration tests for Application Lifecycle Management API endpoints

Tests the FastAPI endpoints for timeline tracking, notifications,
and additional information requests.

Validates: Requirements 6.2, 6.4
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from lifecycle_management import LifecycleManager
from government_portal_integration import GovernmentPortalIntegration


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_credentials():
    """Sample portal credentials"""
    return {
        "client_id": "test_client",
        "client_secret": "test_secret"
    }


@pytest.fixture
def sample_application_data():
    """Sample application data"""
    return {
        "scheme_id": "PM_KISAN_2024",
        "scheme_type": "subsidy",
        "applicant": {
            "name": "Test User",
            "aadhaar": "1234-5678-9012",
            "phone": "+91-9876543210"
        }
    }


class TestApplicationSubmissionWithTimeline:
    """Test application submission creates timeline"""

    def test_submit_application_creates_timeline(
        self,
        client,
        sample_application_data,
        sample_credentials
    ):
        """Test that submitting application creates timeline"""
        response = client.post(
            "/application/submit",
            json={
                "portal_type": "myscheme",
                "application_data": sample_application_data,
                "credentials": sample_credentials
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "confirmation_number" in data
        assert "application_id" in data
        assert "timeline" in data
        
        # Check timeline structure
        timeline = data["timeline"]
        assert "expected_completion" in timeline
        assert "estimated_days" in timeline
        assert "milestones" in timeline
        assert len(timeline["milestones"]) > 0

    def test_submit_application_timeline_has_milestones(
        self,
        client,
        sample_application_data,
        sample_credentials
    ):
        """Test that timeline includes proper milestones"""
        response = client.post(
            "/application/submit",
            json={
                "portal_type": "myscheme",
                "application_data": sample_application_data,
                "credentials": sample_credentials
            }
        )
        
        data = response.json()
        milestones = data["timeline"]["milestones"]
        
        # Check milestone structure
        for milestone in milestones:
            assert "stage" in milestone
            assert "title" in milestone
            assert "description" in milestone
            assert "expected_date" in milestone
            assert "completed" in milestone
        
        # First milestone should be completed
        assert milestones[0]["completed"] is True


class TestTimelineRetrieval:
    """Test timeline retrieval endpoint"""

    def test_get_timeline(self, client, sample_application_data, sample_credentials):
        """Test retrieving timeline for an application"""
        # First submit an application
        submit_response = client.post(
            "/application/submit",
            json={
                "portal_type": "myscheme",
                "application_data": sample_application_data,
                "credentials": sample_credentials
            }
        )
        
        application_id = submit_response.json()["application_id"]
        
        # Get timeline
        response = client.get(f"/application/{application_id}/timeline")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "timeline" in data
        assert data["timeline"]["application_id"] == application_id

    def test_get_timeline_not_found(self, client):
        """Test getting timeline for non-existent application"""
        response = client.get("/application/NONEXISTENT-123/timeline")
        
        assert response.status_code == 404


class TestStatusWithNotifications:
    """Test status check creates notifications"""

    def test_get_status_creates_notification(
        self,
        client,
        sample_application_data,
        sample_credentials
    ):
        """Test that checking status creates notification"""
        # Submit application
        submit_response = client.post(
            "/application/submit",
            json={
                "portal_type": "myscheme",
                "application_data": sample_application_data,
                "credentials": sample_credentials
            }
        )
        
        application_id = submit_response.json()["application_id"]
        
        # Check status
        status_response = client.post(
            "/application/status",
            json={
                "portal_type": "myscheme",
                "application_id": application_id,
                "credentials": sample_credentials
            }
        )
        
        assert status_response.status_code == 200
        
        # Get notifications
        notif_response = client.get(f"/application/{application_id}/notifications")
        
        assert notif_response.status_code == 200
        data = notif_response.json()
        
        assert data["success"] is True
        assert data["count"] > 0
        assert len(data["notifications"]) > 0

    def test_get_status_includes_timeline(
        self,
        client,
        sample_application_data,
        sample_credentials
    ):
        """Test that status response includes timeline"""
        # Submit application
        submit_response = client.post(
            "/application/submit",
            json={
                "portal_type": "myscheme",
                "application_data": sample_application_data,
                "credentials": sample_credentials
            }
        )
        
        application_id = submit_response.json()["application_id"]
        
        # Check status
        response = client.post(
            "/application/status",
            json={
                "portal_type": "myscheme",
                "application_id": application_id,
                "credentials": sample_credentials
            }
        )
        
        data = response.json()
        
        assert "timeline" in data
        assert "confirmation_number" in data["timeline"]
        assert "expected_completion" in data["timeline"]


class TestNotificationEndpoints:
    """Test notification management endpoints"""

    def test_get_notifications(self, client, sample_application_data, sample_credentials):
        """Test getting notifications for an application"""
        # Submit application (creates initial notification)
        submit_response = client.post(
            "/application/submit",
            json={
                "portal_type": "myscheme",
                "application_data": sample_application_data,
                "credentials": sample_credentials
            }
        )
        
        application_id = submit_response.json()["application_id"]
        
        # Get notifications
        response = client.get(f"/application/{application_id}/notifications")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "notifications" in data
        assert data["count"] > 0

    def test_get_unread_notifications(
        self,
        client,
        sample_application_data,
        sample_credentials
    ):
        """Test getting only unread notifications"""
        # Submit application
        submit_response = client.post(
            "/application/submit",
            json={
                "portal_type": "myscheme",
                "application_data": sample_application_data,
                "credentials": sample_credentials
            }
        )
        
        application_id = submit_response.json()["application_id"]
        
        # Get unread notifications
        response = client.get(
            f"/application/{application_id}/notifications?unread_only=true"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All should be unread
        assert all(not n["read"] for n in data["notifications"])

    def test_mark_notification_read(
        self,
        client,
        sample_application_data,
        sample_credentials
    ):
        """Test marking notification as read"""
        # Submit application
        submit_response = client.post(
            "/application/submit",
            json={
                "portal_type": "myscheme",
                "application_data": sample_application_data,
                "credentials": sample_credentials
            }
        )
        
        application_id = submit_response.json()["application_id"]
        
        # Get notifications
        notif_response = client.get(f"/application/{application_id}/notifications")
        notification_id = notif_response.json()["notifications"][0]["notification_id"]
        
        # Mark as read
        response = client.post(
            "/application/notification/read",
            json={
                "application_id": application_id,
                "notification_id": notification_id
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_notification_structure(
        self,
        client,
        sample_application_data,
        sample_credentials
    ):
        """Test notification has correct structure"""
        # Submit application
        submit_response = client.post(
            "/application/submit",
            json={
                "portal_type": "myscheme",
                "application_data": sample_application_data,
                "credentials": sample_credentials
            }
        )
        
        application_id = submit_response.json()["application_id"]
        
        # Get notifications
        response = client.get(f"/application/{application_id}/notifications")
        notifications = response.json()["notifications"]
        
        for notification in notifications:
            assert "notification_id" in notification
            assert "type" in notification
            assert "priority" in notification
            assert "title" in notification
            assert "message" in notification
            assert "created_at" in notification
            assert "read" in notification
            assert "action_required" in notification


class TestAdditionalInfoRequestEndpoints:
    """Test additional information request endpoints"""

    def test_create_additional_info_request(self, client):
        """Test creating additional info request"""
        application_id = "TEST-APP-123"
        
        response = client.post(
            "/application/additional-info/request",
            json={
                "application_id": application_id,
                "required_items": [
                    {
                        "name": "Income Certificate",
                        "description": "Certificate from Tehsildar"
                    },
                    {
                        "name": "Bank Statement",
                        "description": "Last 6 months"
                    }
                ],
                "due_days": 7
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "request" in data
        assert data["request"]["application_id"] == application_id
        assert len(data["request"]["items"]) == 2
        assert data["request"]["status"] == "pending"

    def test_get_additional_info_requests(self, client):
        """Test getting additional info requests"""
        application_id = "TEST-APP-456"
        
        # Create request
        client.post(
            "/application/additional-info/request",
            json={
                "application_id": application_id,
                "required_items": [
                    {"name": "Document", "description": "Required document"}
                ],
                "due_days": 7
            }
        )
        
        # Get requests
        response = client.get(f"/application/{application_id}/additional-info/requests")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["count"] > 0
        assert len(data["requests"]) > 0

    def test_get_additional_info_requests_by_status(self, client):
        """Test filtering requests by status"""
        application_id = "TEST-APP-789"
        
        # Create request
        client.post(
            "/application/additional-info/request",
            json={
                "application_id": application_id,
                "required_items": [
                    {"name": "Document", "description": "Required"}
                ],
                "due_days": 7
            }
        )
        
        # Get pending requests
        response = client.get(
            f"/application/{application_id}/additional-info/requests?status=pending"
        )
        
        data = response.json()
        assert all(r["status"] == "pending" for r in data["requests"])

    def test_submit_additional_info(self, client):
        """Test submitting additional information"""
        application_id = "TEST-APP-101"
        
        # Create request
        create_response = client.post(
            "/application/additional-info/request",
            json={
                "application_id": application_id,
                "required_items": [
                    {"name": "Document", "description": "Required"}
                ],
                "due_days": 7
            }
        )
        
        request_id = create_response.json()["request"]["request_id"]
        
        # Submit info
        response = client.post(
            "/application/additional-info/submit",
            json={
                "request_id": request_id,
                "application_id": application_id,
                "submitted_data": {
                    "document": "data"
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["request"]["status"] == "submitted"

    def test_submit_additional_info_invalid_request(self, client):
        """Test submitting info for invalid request"""
        response = client.post(
            "/application/additional-info/submit",
            json={
                "request_id": "INVALID-123",
                "application_id": "TEST-APP",
                "submitted_data": {"data": "value"}
            }
        )
        
        assert response.status_code == 400

    def test_additional_info_request_creates_notification(self, client):
        """Test that creating request creates notification"""
        application_id = "TEST-APP-202"
        
        # Create request
        client.post(
            "/application/additional-info/request",
            json={
                "application_id": application_id,
                "required_items": [
                    {"name": "Document", "description": "Required"}
                ],
                "due_days": 7
            }
        )
        
        # Check notifications
        response = client.get(f"/application/{application_id}/notifications")
        
        data = response.json()
        assert data["count"] > 0
        
        # Should have urgent notification
        notifications = data["notifications"]
        urgent_notifications = [
            n for n in notifications if n["priority"] == "urgent"
        ]
        assert len(urgent_notifications) > 0


class TestEndToEndLifecycle:
    """Test complete application lifecycle"""

    def test_complete_lifecycle_flow(
        self,
        client,
        sample_application_data,
        sample_credentials
    ):
        """Test complete flow from submission to additional info"""
        # 1. Submit application
        submit_response = client.post(
            "/application/submit",
            json={
                "portal_type": "myscheme",
                "application_data": sample_application_data,
                "credentials": sample_credentials
            }
        )
        
        assert submit_response.status_code == 200
        application_id = submit_response.json()["application_id"]
        confirmation_number = submit_response.json()["confirmation_number"]
        
        # 2. Get timeline
        timeline_response = client.get(f"/application/{application_id}/timeline")
        assert timeline_response.status_code == 200
        assert timeline_response.json()["timeline"]["confirmation_number"] == confirmation_number
        
        # 3. Check status
        status_response = client.post(
            "/application/status",
            json={
                "portal_type": "myscheme",
                "application_id": application_id,
                "credentials": sample_credentials
            }
        )
        assert status_response.status_code == 200
        
        # 4. Get notifications
        notif_response = client.get(f"/application/{application_id}/notifications")
        assert notif_response.status_code == 200
        assert notif_response.json()["count"] > 0
        
        # 5. Create additional info request
        info_request_response = client.post(
            "/application/additional-info/request",
            json={
                "application_id": application_id,
                "required_items": [
                    {"name": "Document", "description": "Required"}
                ],
                "due_days": 7
            }
        )
        assert info_request_response.status_code == 200
        request_id = info_request_response.json()["request"]["request_id"]
        
        # 6. Submit additional info
        submit_info_response = client.post(
            "/application/additional-info/submit",
            json={
                "request_id": request_id,
                "application_id": application_id,
                "submitted_data": {"document": "data"}
            }
        )
        assert submit_info_response.status_code == 200
        
        # 7. Verify final notifications
        final_notif_response = client.get(f"/application/{application_id}/notifications")
        # Should have multiple notifications from the lifecycle
        assert final_notif_response.json()["count"] >= 3
