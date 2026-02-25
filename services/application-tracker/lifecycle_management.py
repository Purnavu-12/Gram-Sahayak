"""
Application Lifecycle Management Service
Manages the complete application lifecycle including confirmation tracking,
timeline management, notifications, and additional information requests.

Validates: Requirements 6.2, 6.4
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
import asyncio
from outcome_explanation import (
    OutcomeExplanationSystem,
    OutcomeType,
    RejectionReason,
    OutcomeExplanation,
    AppealGuidance,
    ResubmissionGuidance
)


class NotificationType(str, Enum):
    """Types of notifications"""
    STATUS_UPDATE = "status_update"
    ADDITIONAL_INFO_REQUIRED = "additional_info_required"
    APPROVAL = "approval"
    REJECTION = "rejection"
    TIMELINE_UPDATE = "timeline_update"
    REMINDER = "reminder"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ApplicationTimeline(BaseModel):
    """Timeline information for an application"""
    confirmation_number: str
    application_id: str
    submitted_at: datetime
    expected_completion: datetime
    estimated_days: int
    milestones: List[Dict[str, Any]] = Field(default_factory=list)
    last_updated: datetime


class Notification(BaseModel):
    """Notification model"""
    notification_id: str
    application_id: str
    notification_type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    created_at: datetime
    read: bool = False
    action_required: bool = False
    action_details: Optional[Dict[str, Any]] = None


class AdditionalInfoRequest(BaseModel):
    """Request for additional information"""
    request_id: str
    application_id: str
    requested_at: datetime
    due_date: datetime
    items: List[Dict[str, Any]]
    status: str = "pending"
    submitted_at: Optional[datetime] = None


class LifecycleManager:
    """
    Manages application lifecycle including tracking, notifications,
    and additional information requests.
    """

    def __init__(self):
        """Initialize the lifecycle manager"""
        # Storage for timelines, notifications, and requests
        self.timelines: Dict[str, ApplicationTimeline] = {}
        self.notifications: Dict[str, List[Notification]] = {}
        self.info_requests: Dict[str, List[AdditionalInfoRequest]] = {}
        
        # Notification subscribers (in production, this would be a message queue)
        self.notification_subscribers: Dict[str, List[callable]] = {}
        
        # Outcome explanation system
        self.outcome_system = OutcomeExplanationSystem()
        
        # Storage for outcome explanations
        self.outcome_explanations: Dict[str, OutcomeExplanation] = {}

    async def create_timeline(
        self,
        confirmation_number: str,
        application_id: str,
        portal_type: str,
        scheme_type: Optional[str] = None
    ) -> ApplicationTimeline:
        """
        Create a timeline for a submitted application.
        
        Args:
            confirmation_number: Unique confirmation number
            application_id: Application identifier
            portal_type: Type of government portal
            scheme_type: Optional scheme type for specific timeline estimates
            
        Returns:
            ApplicationTimeline with expected completion and milestones
            
        Validates: Requirement 6.2 (confirmation numbers and expected timelines)
        """
        submitted_at = datetime.now()
        
        # Calculate expected completion based on portal and scheme type
        estimated_days = self._calculate_processing_time(portal_type, scheme_type)
        expected_completion = submitted_at + timedelta(days=estimated_days)
        
        # Create milestones based on typical government processing
        milestones = self._generate_milestones(
            submitted_at,
            expected_completion,
            portal_type
        )
        
        timeline = ApplicationTimeline(
            confirmation_number=confirmation_number,
            application_id=application_id,
            submitted_at=submitted_at,
            expected_completion=expected_completion,
            estimated_days=estimated_days,
            milestones=milestones,
            last_updated=submitted_at
        )
        
        # Store timeline
        self.timelines[application_id] = timeline
        
        # Send initial confirmation notification
        await self._send_notification(
            application_id=application_id,
            notification_type=NotificationType.STATUS_UPDATE,
            priority=NotificationPriority.MEDIUM,
            title="Application Submitted Successfully",
            message=f"Your application has been submitted. Confirmation number: {confirmation_number}. "
                   f"Expected completion: {expected_completion.strftime('%d %B %Y')} "
                   f"(approximately {estimated_days} days).",
            action_required=False
        )
        
        return timeline

    def _calculate_processing_time(
        self,
        portal_type: str,
        scheme_type: Optional[str] = None
    ) -> int:
        """
        Calculate expected processing time based on portal and scheme.
        
        Returns:
            Estimated processing time in days
        """
        # Base processing times by portal (in days)
        base_times = {
            "myscheme": 21,
            "eshram": 7,
            "umang": 14,
            "pmkisan": 30,
            "mgnrega": 15,
            "ayushmanbharat": 45,
            "digilocker": 1,
            "generic": 21
        }
        
        base_time = base_times.get(portal_type, 21)
        
        # Adjust based on scheme type if provided
        if scheme_type:
            scheme_adjustments = {
                "pension": 15,  # Additional days for pension schemes
                "subsidy": 10,
                "loan": 20,
                "certificate": -7,  # Faster for certificates
                "registration": -5
            }
            
            for key, adjustment in scheme_adjustments.items():
                if key in scheme_type.lower():
                    base_time += adjustment
                    break
        
        return max(base_time, 1)  # Minimum 1 day

    def _generate_milestones(
        self,
        submitted_at: datetime,
        expected_completion: datetime,
        portal_type: str
    ) -> List[Dict[str, Any]]:
        """
        Generate typical milestones for application processing.
        
        Returns:
            List of milestone dictionaries with dates and descriptions
        """
        total_days = (expected_completion - submitted_at).days
        
        milestones = [
            {
                "stage": "submission",
                "title": "Application Submitted",
                "description": "Your application has been received",
                "expected_date": submitted_at.isoformat(),
                "completed": True,
                "completed_at": submitted_at.isoformat()
            },
            {
                "stage": "acknowledgment",
                "title": "Acknowledgment",
                "description": "Application acknowledged by department",
                "expected_date": (submitted_at + timedelta(days=int(total_days * 0.1))).isoformat(),
                "completed": False
            },
            {
                "stage": "verification",
                "title": "Document Verification",
                "description": "Documents are being verified",
                "expected_date": (submitted_at + timedelta(days=int(total_days * 0.3))).isoformat(),
                "completed": False
            },
            {
                "stage": "review",
                "title": "Under Review",
                "description": "Application is under review by officials",
                "expected_date": (submitted_at + timedelta(days=int(total_days * 0.6))).isoformat(),
                "completed": False
            },
            {
                "stage": "approval",
                "title": "Approval Process",
                "description": "Application is in final approval stage",
                "expected_date": (submitted_at + timedelta(days=int(total_days * 0.9))).isoformat(),
                "completed": False
            },
            {
                "stage": "completion",
                "title": "Completed",
                "description": "Application processing completed",
                "expected_date": expected_completion.isoformat(),
                "completed": False
            }
        ]
        
        return milestones

    async def get_timeline(self, application_id: str) -> Optional[ApplicationTimeline]:
        """
        Get timeline for an application.
        
        Args:
            application_id: Application identifier
            
        Returns:
            ApplicationTimeline if found, None otherwise
        """
        return self.timelines.get(application_id)

    async def update_timeline(
        self,
        application_id: str,
        current_stage: str,
        new_expected_completion: Optional[datetime] = None
    ) -> ApplicationTimeline:
        """
        Update timeline based on current progress.
        
        Args:
            application_id: Application identifier
            current_stage: Current processing stage
            new_expected_completion: Updated expected completion date
            
        Returns:
            Updated ApplicationTimeline
        """
        timeline = self.timelines.get(application_id)
        if not timeline:
            raise ValueError(f"Timeline not found for application {application_id}")
        
        # Update milestones
        for milestone in timeline.milestones:
            if milestone["stage"] == current_stage and not milestone["completed"]:
                milestone["completed"] = True
                milestone["completed_at"] = datetime.now().isoformat()
        
        # Update expected completion if provided
        if new_expected_completion:
            old_date = timeline.expected_completion
            timeline.expected_completion = new_expected_completion
            timeline.estimated_days = (new_expected_completion - timeline.submitted_at).days
            
            # Notify about timeline change
            await self._send_notification(
                application_id=application_id,
                notification_type=NotificationType.TIMELINE_UPDATE,
                priority=NotificationPriority.MEDIUM,
                title="Timeline Updated",
                message=f"Expected completion date updated from {old_date.strftime('%d %B %Y')} "
                       f"to {new_expected_completion.strftime('%d %B %Y')}.",
                action_required=False
            )
        
        timeline.last_updated = datetime.now()
        self.timelines[application_id] = timeline
        
        return timeline

    async def send_status_notification(
        self,
        application_id: str,
        status: str,
        status_description: str,
        next_steps: List[str]
    ) -> Notification:
        """
        Send notification about status update.
        
        Args:
            application_id: Application identifier
            status: Current status
            status_description: Human-readable status description
            next_steps: List of next steps
            
        Returns:
            Created Notification
            
        Validates: Requirement 6.2 (status update notifications)
        """
        # Determine priority based on status
        priority = NotificationPriority.MEDIUM
        if status in ["approved", "rejected"]:
            priority = NotificationPriority.HIGH
        elif status == "pending_documents":
            priority = NotificationPriority.URGENT
        
        # Format next steps
        next_steps_text = "\n".join([f"• {step}" for step in next_steps])
        
        message = f"{status_description}\n\nNext Steps:\n{next_steps_text}"
        
        return await self._send_notification(
            application_id=application_id,
            notification_type=NotificationType.STATUS_UPDATE,
            priority=priority,
            title=f"Status Update: {status.replace('_', ' ').title()}",
            message=message,
            action_required=(status == "pending_documents")
        )

    async def create_additional_info_request(
        self,
        application_id: str,
        required_items: List[Dict[str, Any]],
        due_days: int = 7
    ) -> AdditionalInfoRequest:
        """
        Create a request for additional information.
        
        Args:
            application_id: Application identifier
            required_items: List of required information/documents
            due_days: Number of days to provide information
            
        Returns:
            Created AdditionalInfoRequest
            
        Validates: Requirement 6.4 (notify users and guide next steps)
        """
        import uuid
        
        request_id = str(uuid.uuid4())
        requested_at = datetime.now()
        due_date = requested_at + timedelta(days=due_days)
        
        request = AdditionalInfoRequest(
            request_id=request_id,
            application_id=application_id,
            requested_at=requested_at,
            due_date=due_date,
            items=required_items,
            status="pending"
        )
        
        # Store request
        if application_id not in self.info_requests:
            self.info_requests[application_id] = []
        self.info_requests[application_id].append(request)
        
        # Format items for notification
        items_text = "\n".join([
            f"• {item.get('name', 'Item')}: {item.get('description', '')}"
            for item in required_items
        ])
        
        # Send notification
        await self._send_notification(
            application_id=application_id,
            notification_type=NotificationType.ADDITIONAL_INFO_REQUIRED,
            priority=NotificationPriority.URGENT,
            title="Additional Information Required",
            message=f"Your application requires additional information. "
                   f"Please provide the following by {due_date.strftime('%d %B %Y')}:\n\n"
                   f"{items_text}\n\n"
                   f"Failure to provide this information may result in application rejection.",
            action_required=True,
            action_details={
                "request_id": request_id,
                "due_date": due_date.isoformat(),
                "items": required_items
            }
        )
        
        return request

    async def get_additional_info_requests(
        self,
        application_id: str,
        status: Optional[str] = None
    ) -> List[AdditionalInfoRequest]:
        """
        Get additional information requests for an application.
        
        Args:
            application_id: Application identifier
            status: Optional filter by status (pending, submitted, expired)
            
        Returns:
            List of AdditionalInfoRequest objects
        """
        requests = self.info_requests.get(application_id, [])
        
        if status:
            requests = [r for r in requests if r.status == status]
        
        return requests

    async def submit_additional_info(
        self,
        request_id: str,
        application_id: str,
        submitted_data: Dict[str, Any]
    ) -> AdditionalInfoRequest:
        """
        Submit additional information in response to a request.
        
        Args:
            request_id: Request identifier
            application_id: Application identifier
            submitted_data: Data being submitted
            
        Returns:
            Updated AdditionalInfoRequest
            
        Validates: Requirement 6.4 (handle additional information requests)
        """
        requests = self.info_requests.get(application_id, [])
        request = next((r for r in requests if r.request_id == request_id), None)
        
        if not request:
            raise ValueError(f"Request {request_id} not found for application {application_id}")
        
        if request.status != "pending":
            raise ValueError(f"Request {request_id} is not pending (status: {request.status})")
        
        # Update request
        request.status = "submitted"
        request.submitted_at = datetime.now()
        
        # Send confirmation notification
        await self._send_notification(
            application_id=application_id,
            notification_type=NotificationType.STATUS_UPDATE,
            priority=NotificationPriority.MEDIUM,
            title="Additional Information Submitted",
            message="Your additional information has been submitted successfully. "
                   "Your application will now continue processing.",
            action_required=False
        )
        
        return request

    async def get_notifications(
        self,
        application_id: str,
        unread_only: bool = False
    ) -> List[Notification]:
        """
        Get notifications for an application.
        
        Args:
            application_id: Application identifier
            unread_only: If True, return only unread notifications
            
        Returns:
            List of Notification objects
        """
        notifications = self.notifications.get(application_id, [])
        
        if unread_only:
            notifications = [n for n in notifications if not n.read]
        
        return notifications

    async def mark_notification_read(
        self,
        application_id: str,
        notification_id: str
    ) -> bool:
        """
        Mark a notification as read.
        
        Args:
            application_id: Application identifier
            notification_id: Notification identifier
            
        Returns:
            True if marked successfully, False otherwise
        """
        notifications = self.notifications.get(application_id, [])
        
        for notification in notifications:
            if notification.notification_id == notification_id:
                notification.read = True
                return True
        
        return False

    async def _send_notification(
        self,
        application_id: str,
        notification_type: NotificationType,
        priority: NotificationPriority,
        title: str,
        message: str,
        action_required: bool,
        action_details: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        Internal method to create and send a notification.
        
        Returns:
            Created Notification
        """
        import uuid
        
        notification = Notification(
            notification_id=str(uuid.uuid4()),
            application_id=application_id,
            notification_type=notification_type,
            priority=priority,
            title=title,
            message=message,
            created_at=datetime.now(),
            read=False,
            action_required=action_required,
            action_details=action_details
        )
        
        # Store notification
        if application_id not in self.notifications:
            self.notifications[application_id] = []
        self.notifications[application_id].append(notification)
        
        # Notify subscribers (in production, this would publish to message queue)
        await self._notify_subscribers(application_id, notification)
        
        return notification

    async def _notify_subscribers(
        self,
        application_id: str,
        notification: Notification
    ):
        """
        Notify subscribers about new notification.
        In production, this would publish to a message queue or webhook.
        """
        subscribers = self.notification_subscribers.get(application_id, [])
        
        for subscriber in subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(notification)
                else:
                    subscriber(notification)
            except Exception as e:
                # Log error but don't fail notification creation
                print(f"Error notifying subscriber: {e}")

    def subscribe_to_notifications(
        self,
        application_id: str,
        callback: callable
    ):
        """
        Subscribe to notifications for an application.
        
        Args:
            application_id: Application identifier
            callback: Callback function to receive notifications
        """
        if application_id not in self.notification_subscribers:
            self.notification_subscribers[application_id] = []
        
        self.notification_subscribers[application_id].append(callback)

    def unsubscribe_from_notifications(
        self,
        application_id: str,
        callback: callable
    ):
        """
        Unsubscribe from notifications for an application.
        
        Args:
            application_id: Application identifier
            callback: Callback function to remove
        """
        if application_id in self.notification_subscribers:
            try:
                self.notification_subscribers[application_id].remove(callback)
            except ValueError:
                pass

    async def send_outcome_notification(
        self,
        application_id: str,
        outcome_type: OutcomeType,
        rejection_reason: Optional[RejectionReason] = None,
        specific_details: Optional[List[str]] = None,
        scheme_name: Optional[str] = None,
        benefit_amount: Optional[str] = None
    ) -> OutcomeExplanation:
        """
        Send notification about application outcome with clear explanation.
        
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
        # Generate outcome explanation
        explanation = self.outcome_system.generate_outcome_explanation(
            application_id=application_id,
            outcome_type=outcome_type,
            rejection_reason=rejection_reason,
            specific_details=specific_details,
            scheme_name=scheme_name,
            benefit_amount=benefit_amount
        )
        
        # Store explanation
        self.outcome_explanations[application_id] = explanation
        
        # Determine notification type and priority
        if outcome_type == OutcomeType.APPROVED:
            notification_type = NotificationType.APPROVAL
            priority = NotificationPriority.HIGH
            title = "Application Approved!"
        elif outcome_type == OutcomeType.REJECTED:
            notification_type = NotificationType.REJECTION
            priority = NotificationPriority.HIGH
            title = "Application Decision"
        else:
            notification_type = NotificationType.STATUS_UPDATE
            priority = NotificationPriority.HIGH
            title = "Application Partially Approved"
        
        # Format message with explanation
        message = f"{explanation.primary_reason}\n\n{explanation.detailed_explanation}\n\n"
        
        if explanation.supporting_details:
            message += "Details:\n"
            for detail in explanation.supporting_details:
                message += f"• {detail}\n"
            message += "\n"
        
        message += "Next Steps:\n"
        for step in explanation.next_steps:
            message += f"• {step}\n"
        
        # Add appeal/resubmission info
        if explanation.appeal_eligible and explanation.appeal_deadline:
            message += f"\nAppeal Deadline: {explanation.appeal_deadline.strftime('%d %B %Y')}"
        
        if explanation.resubmission_allowed:
            message += "\nResubmission: Allowed with corrections"
        
        # Send notification
        await self._send_notification(
            application_id=application_id,
            notification_type=notification_type,
            priority=priority,
            title=title,
            message=message,
            action_required=explanation.appeal_eligible or explanation.resubmission_allowed,
            action_details={
                "outcome_type": outcome_type.value,
                "appeal_eligible": explanation.appeal_eligible,
                "resubmission_allowed": explanation.resubmission_allowed,
                "contact_info": explanation.contact_info
            }
        )
        
        return explanation

    async def get_outcome_explanation(
        self,
        application_id: str
    ) -> Optional[OutcomeExplanation]:
        """
        Get outcome explanation for an application.
        
        Args:
            application_id: Application identifier
            
        Returns:
            OutcomeExplanation if found, None otherwise
        """
        return self.outcome_explanations.get(application_id)

    async def get_appeal_guidance(
        self,
        application_id: str
    ) -> Optional[AppealGuidance]:
        """
        Get appeal guidance for a rejected application.
        
        Args:
            application_id: Application identifier
            
        Returns:
            AppealGuidance if application is rejected and appeal is possible
            
        Validates: Requirement 6.5 (appeal guidance)
        """
        explanation = self.outcome_explanations.get(application_id)
        
        if not explanation or explanation.outcome_type != OutcomeType.REJECTED:
            return None
        
        # Extract rejection reason from explanation
        # In a real system, this would be stored separately
        rejection_reason = self._infer_rejection_reason(explanation)
        
        guidance = self.outcome_system.generate_appeal_guidance(
            application_id=application_id,
            rejection_date=explanation.outcome_date,
            rejection_reason=rejection_reason
        )
        
        return guidance

    async def get_resubmission_guidance(
        self,
        application_id: str,
        specific_corrections: Optional[List[Dict[str, str]]] = None
    ) -> Optional[ResubmissionGuidance]:
        """
        Get resubmission guidance for a rejected application.
        
        Args:
            application_id: Application identifier
            specific_corrections: Specific corrections needed
            
        Returns:
            ResubmissionGuidance if application is rejected, None otherwise
            
        Validates: Requirement 6.5 (resubmission guidance)
        """
        explanation = self.outcome_explanations.get(application_id)
        
        if not explanation or explanation.outcome_type != OutcomeType.REJECTED:
            return None
        
        # Extract rejection reason from explanation
        rejection_reason = self._infer_rejection_reason(explanation)
        
        guidance = self.outcome_system.generate_resubmission_guidance(
            application_id=application_id,
            rejection_reason=rejection_reason,
            specific_corrections=specific_corrections
        )
        
        return guidance

    def _infer_rejection_reason(self, explanation: OutcomeExplanation) -> RejectionReason:
        """
        Infer rejection reason from explanation.
        In production, this would be stored explicitly.
        """
        primary = explanation.primary_reason.lower()
        
        if "incomplete" in primary or "missing" in primary:
            return RejectionReason.INCOMPLETE_DOCUMENTS
        elif "ineligible" in primary or "eligibility" in primary:
            return RejectionReason.INELIGIBLE
        elif "duplicate" in primary:
            return RejectionReason.DUPLICATE_APPLICATION
        elif "invalid" in primary or "incorrect" in primary:
            return RejectionReason.INVALID_INFORMATION
        elif "criteria" in primary:
            return RejectionReason.MISSING_CRITERIA
        elif "expired" in primary:
            return RejectionReason.EXPIRED_DOCUMENTS
        elif "technical" in primary:
            return RejectionReason.TECHNICAL_ERROR
        else:
            return RejectionReason.OTHER
