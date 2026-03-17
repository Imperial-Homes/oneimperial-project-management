"""Notification service for Project Management."""

import logging
import httpx
from typing import Optional
from uuid import UUID
from app.config import settings

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending in-app notifications via the central hub."""
    
    def __init__(self):
        """Initialize notification service with hub settings."""
        self.base_url = settings.NOTIFICATION_SERVICE_URL

    def send_notification(
        self,
        user_id: UUID,
        title: str,
        message: str,
        type: str = "info",
        link: Optional[str] = None
    ) -> bool:
        """Send an in-app notification via the central hub."""
        try:
            payload = {
                "user_id": str(user_id),
                "title": title,
                "message": message,
                "type": type,
                "link": link
            }
            
            response = httpx.post(
                self.base_url,
                json=payload,
                timeout=httpx.Timeout(5.0, connect=2.0)
            )
            
            if response.status_code == 201:
                logger.info(f"Notification sent successfully to user {user_id}")
                return True
            else:
                logger.error(f"Failed to send notification. Status: {response.status_code}, Body: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False

# Create a singleton instance
notification_service = NotificationService()
