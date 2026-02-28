"""
Application Tracker Service - Main API
Provides endpoints for government portal integration, application submission,
and status tracking.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Optional, Any, List
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
import os
import logging
import json
import re
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": "application-tracker",
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

app = FastAPI(
    title="Application Tracker Service",
    description="Government portal integration, application submission, and status tracking for Gram Sahayak",
    version="1.0.0",
)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Initialize services
portal_integration = GovernmentPortalIntegration()
lifecycle_manager = LifecycleManager()


def sanitize_string(value: str) -> str:
    """Remove HTML tags and limit length for input sanitization."""
    if not value:
        return value
    clean = re.sub(r'<[^>]+>', '', value)
    return clean[:10000]


class AuthenticationRequest(BaseModel):
    """Request model for portal authentication"""
    portal_type: PortalType
    credentials: Dict[str, str] = Field(
        ...,
        description="Portal credentials (format varies by portal type)"
    )


class SubmissionRequest(BaseModel):
    """Request model for application submission"""
    portal_type: PortalType
    application_data: Dict[str, Any] = Field(
        ...,
        description="Complete application form data"
    )
    credentials: Dict[str, str] = Field(
        ...,
        description="Portal authentication credentials"
    )


class StatusRequest(BaseModel):
    """Request model for status check"""
    portal_type: PortalType
    application_id: str = Field(
        ...,
        description="Application identifier from portal"
    )
    credentials: Dict[str, str] = Field(
        ...,
        description="Portal authentication credentials"
    )


class MonitoringRequest(BaseModel):
    """Request model for status monitoring"""
    portal_type: PortalType
    application_id: str
    credentials: Dict[str, str]
    check_interval: Optional[int] = Field(
        3600,
        description="Interval between status checks in seconds"
    )


class AdditionalInfoRequestModel(BaseModel):
    """Request model for creating additional info request"""
    application_id: str
    required_items: List[Dict[str, Any]] = Field(
        ...,
        description="List of required information/documents"
    )
    due_days: Optional[int] = Field(
        7,
        description="Number of days to provide information"
    )


class AdditionalInfoSubmission(BaseModel):
    """Request model for submitting additional information"""
    request_id: str
    application_id: str
    submitted_data: Dict[str, Any] = Field(
        ...,
        description="Data being submitted"
    )


class NotificationMarkRead(BaseModel):
    """Request model for marking notification as read"""
    application_id: str
    notification_id: str


@app.post("/portal/authenticate")
async def authenticate_portal(request: AuthenticationRequest):
    """
    Authenticate with a government portal and obtain access token.
    
    Validates: Requirement 6.1 (secure API connections)
    """
    try:
        result = await portal_integration.authenticate_portal(
            request.portal_type,
            request.credentials
        )
        return result
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/application/submit")
async def submit_application(request: SubmissionRequest):
    """
    Submit an application to a government portal.
    
    Validates: Requirement 6.1 (application submission automation)
    Validates: Requirement 6.2 (confirmation numbers and expected timelines)
    """
    try:
        result = await portal_integration.submit_application(
            request.portal_type,
            request.application_data,
            request.credentials
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Submission failed")
            )
        
        # Create timeline for the application
        scheme_type = request.application_data.get("scheme_type")
        timeline = await lifecycle_manager.create_timeline(
            confirmation_number=result["confirmation_number"],
            application_id=result["application_id"],
            portal_type=request.portal_type.value,
            scheme_type=scheme_type
        )
        
        # Add timeline information to response
        result["timeline"] = {
            "expected_completion": timeline.expected_completion.isoformat(),
            "estimated_days": timeline.estimated_days,
            "milestones": timeline.milestones
        }
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/application/status")
async def get_application_status(request: StatusRequest):
    """
    Retrieve current application status from government portal.
    
    Validates: Requirement 6.3 (status tracking from government systems)
    Validates: Requirement 6.2 (status update notifications)
    """
    try:
        result = await portal_integration.get_application_status(
            request.portal_type,
            request.application_id,
            request.credentials
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to fetch status")
            )
        
        # Send status notification
        await lifecycle_manager.send_status_notification(
            application_id=request.application_id,
            status=result["status"],
            status_description=result["status_description"],
            next_steps=result.get("next_steps", [])
        )
        
        # Get timeline if available
        timeline = await lifecycle_manager.get_timeline(request.application_id)
        if timeline:
            result["timeline"] = {
                "confirmation_number": timeline.confirmation_number,
                "expected_completion": timeline.expected_completion.isoformat(),
                "estimated_days": timeline.estimated_days,
                "milestones": timeline.milestones
            }
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/application/monitor")
async def monitor_application(request: MonitoringRequest):
    """
    Set up monitoring for application status with periodic checks.
    
    Validates: Requirement 6.3 (status tracking and monitoring system)
    """
    try:
        result = await portal_integration.monitor_application_status(
            request.portal_type,
            request.application_id,
            request.credentials,
            request.check_interval
        )
        return result
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/portals/supported")
async def get_supported_portals():
    """
    Get list of supported government portals.
    """
    return {
        "portals": [
            {
                "type": portal.value,
                "name": portal.name,
                "description": f"{portal.value.upper()} government portal"
            }
            for portal in PortalType
        ]
    }


@app.get("/status/types")
async def get_status_types():
    """
    Get list of possible application status types.
    """
    return {
        "statuses": [
            {
                "value": status.value,
                "name": status.name,
                "description": portal_integration._get_status_description(status)
            }
            for status in ApplicationStatus
        ]
    }


@app.get("/application/{application_id}/timeline")
async def get_timeline(application_id: str):
    """
    Get timeline for an application.
    
    Validates: Requirement 6.2 (confirmation numbers and expected timelines)
    """
    try:
        timeline = await lifecycle_manager.get_timeline(application_id)
        
        if not timeline:
            raise HTTPException(
                status_code=404,
                detail=f"Timeline not found for application {application_id}"
            )
        
        return {
            "success": True,
            "timeline": {
                "confirmation_number": timeline.confirmation_number,
                "application_id": timeline.application_id,
                "submitted_at": timeline.submitted_at.isoformat(),
                "expected_completion": timeline.expected_completion.isoformat(),
                "estimated_days": timeline.estimated_days,
                "milestones": timeline.milestones,
                "last_updated": timeline.last_updated.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/application/{application_id}/notifications")
async def get_notifications(application_id: str, unread_only: bool = False):
    """
    Get notifications for an application.
    
    Validates: Requirement 6.2 (status update notifications)
    """
    try:
        notifications = await lifecycle_manager.get_notifications(
            application_id,
            unread_only=unread_only
        )
        
        return {
            "success": True,
            "application_id": application_id,
            "count": len(notifications),
            "notifications": [
                {
                    "notification_id": n.notification_id,
                    "type": n.notification_type.value,
                    "priority": n.priority.value,
                    "title": n.title,
                    "message": n.message,
                    "created_at": n.created_at.isoformat(),
                    "read": n.read,
                    "action_required": n.action_required,
                    "action_details": n.action_details
                }
                for n in notifications
            ]
        }
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/application/notification/read")
async def mark_notification_read(request: NotificationMarkRead):
    """
    Mark a notification as read.
    """
    try:
        success = await lifecycle_manager.mark_notification_read(
            request.application_id,
            request.notification_id
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Notification not found"
            )
        
        return {
            "success": True,
            "message": "Notification marked as read"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/application/additional-info/request")
async def create_additional_info_request(request: AdditionalInfoRequestModel):
    """
    Create a request for additional information.
    
    Validates: Requirement 6.4 (notify users and guide next steps)
    """
    try:
        info_request = await lifecycle_manager.create_additional_info_request(
            application_id=request.application_id,
            required_items=request.required_items,
            due_days=request.due_days
        )
        
        return {
            "success": True,
            "request": {
                "request_id": info_request.request_id,
                "application_id": info_request.application_id,
                "requested_at": info_request.requested_at.isoformat(),
                "due_date": info_request.due_date.isoformat(),
                "items": info_request.items,
                "status": info_request.status
            }
        }
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/application/{application_id}/additional-info/requests")
async def get_additional_info_requests(
    application_id: str,
    status: Optional[str] = None
):
    """
    Get additional information requests for an application.
    
    Validates: Requirement 6.4 (additional information request handling)
    """
    try:
        requests = await lifecycle_manager.get_additional_info_requests(
            application_id,
            status=status
        )
        
        return {
            "success": True,
            "application_id": application_id,
            "count": len(requests),
            "requests": [
                {
                    "request_id": r.request_id,
                    "requested_at": r.requested_at.isoformat(),
                    "due_date": r.due_date.isoformat(),
                    "items": r.items,
                    "status": r.status,
                    "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None
                }
                for r in requests
            ]
        }
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/application/additional-info/submit")
async def submit_additional_info(request: AdditionalInfoSubmission):
    """
    Submit additional information in response to a request.
    
    Validates: Requirement 6.4 (handle additional information requests)
    """
    try:
        info_request = await lifecycle_manager.submit_additional_info(
            request_id=request.request_id,
            application_id=request.application_id,
            submitted_data=request.submitted_data
        )
        
        return {
            "success": True,
            "message": "Additional information submitted successfully",
            "request": {
                "request_id": info_request.request_id,
                "status": info_request.status,
                "submitted_at": info_request.submitted_at.isoformat() if info_request.submitted_at else None
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "application-tracker"
    }


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await portal_integration.close()



class OutcomeNotificationRequest(BaseModel):
    """Request model for sending outcome notification"""
    application_id: str
    outcome_type: OutcomeType
    rejection_reason: Optional[RejectionReason] = None
    specific_details: Optional[List[str]] = None
    scheme_name: Optional[str] = None
    benefit_amount: Optional[str] = None


@app.post("/application/outcome/notify")
async def send_outcome_notification(request: OutcomeNotificationRequest):
    """
    Send notification about application outcome with clear explanation.
    
    Validates: Requirement 6.5 (inform users with clear explanations)
    """
    try:
        explanation = await lifecycle_manager.send_outcome_notification(
            application_id=request.application_id,
            outcome_type=request.outcome_type,
            rejection_reason=request.rejection_reason,
            specific_details=request.specific_details,
            scheme_name=request.scheme_name,
            benefit_amount=request.benefit_amount
        )
        
        return {
            "success": True,
            "application_id": request.application_id,
            "outcome": {
                "type": explanation.outcome_type.value,
                "date": explanation.outcome_date.isoformat(),
                "primary_reason": explanation.primary_reason,
                "detailed_explanation": explanation.detailed_explanation,
                "supporting_details": explanation.supporting_details,
                "next_steps": explanation.next_steps,
                "appeal_eligible": explanation.appeal_eligible,
                "appeal_deadline": explanation.appeal_deadline.isoformat() if explanation.appeal_deadline else None,
                "resubmission_allowed": explanation.resubmission_allowed,
                "contact_info": explanation.contact_info
            }
        }
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/application/{application_id}/outcome")
async def get_outcome_explanation(application_id: str):
    """
    Get outcome explanation for an application.
    
    Validates: Requirement 6.5 (clear explanations for outcomes)
    """
    try:
        explanation = await lifecycle_manager.get_outcome_explanation(application_id)
        
        if not explanation:
            raise HTTPException(
                status_code=404,
                detail=f"No outcome found for application {application_id}"
            )
        
        return {
            "success": True,
            "application_id": application_id,
            "outcome": {
                "type": explanation.outcome_type.value,
                "date": explanation.outcome_date.isoformat(),
                "primary_reason": explanation.primary_reason,
                "detailed_explanation": explanation.detailed_explanation,
                "supporting_details": explanation.supporting_details,
                "next_steps": explanation.next_steps,
                "appeal_eligible": explanation.appeal_eligible,
                "appeal_deadline": explanation.appeal_deadline.isoformat() if explanation.appeal_deadline else None,
                "resubmission_allowed": explanation.resubmission_allowed,
                "contact_info": explanation.contact_info
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/application/{application_id}/appeal-guidance")
async def get_appeal_guidance(application_id: str):
    """
    Get appeal guidance for a rejected application.
    
    Validates: Requirement 6.5 (appeal guidance)
    """
    try:
        guidance = await lifecycle_manager.get_appeal_guidance(application_id)
        
        if not guidance:
            raise HTTPException(
                status_code=404,
                detail=f"No appeal guidance available for application {application_id}"
            )
        
        return {
            "success": True,
            "application_id": application_id,
            "appeal_guidance": {
                "eligibility": guidance.eligibility.value,
                "appeal_deadline": guidance.appeal_deadline.isoformat() if guidance.appeal_deadline else None,
                "appeal_process": guidance.appeal_process,
                "required_documents": guidance.required_documents,
                "submission_methods": guidance.submission_methods,
                "estimated_timeline": guidance.estimated_timeline,
                "contact_info": guidance.contact_info,
                "tips": guidance.tips
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/application/{application_id}/resubmission-guidance")
async def get_resubmission_guidance(application_id: str):
    """
    Get resubmission guidance for a rejected application.
    
    Validates: Requirement 6.5 (resubmission guidance)
    """
    try:
        guidance = await lifecycle_manager.get_resubmission_guidance(application_id)
        
        if not guidance:
            raise HTTPException(
                status_code=404,
                detail=f"No resubmission guidance available for application {application_id}"
            )
        
        return {
            "success": True,
            "application_id": application_id,
            "resubmission_guidance": {
                "resubmission_allowed": guidance.resubmission_allowed,
                "waiting_period": guidance.waiting_period,
                "corrections_needed": guidance.corrections_needed,
                "resubmission_process": guidance.resubmission_process,
                "documents_to_update": guidance.documents_to_update,
                "estimated_timeline": guidance.estimated_timeline,
                "tips": guidance.tips
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
