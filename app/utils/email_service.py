"""Email service using Mailgun API for Project Management notifications."""

import logging
from typing import Optional
import requests

from app.config import Settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via Mailgun."""
    
    def __init__(self):
        """Initialize email service with Mailgun settings."""
        self.settings = Settings()
        self.api_key = self.settings.MAILGUN_API_KEY
        self.domain = self.settings.MAILGUN_DOMAIN
        self.from_email = self.settings.MAILGUN_FROM_EMAIL
        self.from_name = self.settings.MAILGUN_FROM_NAME
        self.base_url = f"https://api.mailgun.net/v3/{self.domain}/messages"
    
    def is_configured(self) -> bool:
        """Check if Mailgun is properly configured."""
        return bool(self.api_key and self.domain)
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email via Mailgun.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.error("Mailgun is not configured. Please set MAILGUN_API_KEY and MAILGUN_DOMAIN.")
            return False
        
        try:
            data = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": to_email,
                "subject": subject,
                "html": html_content,
            }
            
            if text_content:
                data["text"] = text_content
            
            response = requests.post(
                self.base_url,
                auth=("api", self.api_key),
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email to {to_email}. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False
    
    def send_task_assigned_email(
        self,
        to_email: str,
        assignee_name: str,
        task_title: str,
        project_name: str,
        due_date: str,
        priority: str,
        task_url: str
    ) -> bool:
        """Send task assignment notification."""
        subject = f"New Task Assigned: {task_title}"
        
        priority_colors = {
            "low": "#28a745",
            "medium": "#ffc107",
            "high": "#fd7e14",
            "critical": "#dc3545"
        }
        priority_color = priority_colors.get(priority.lower(), "#6c757d")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1a73e8; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }}
                .task-details {{ background-color: #fff; padding: 20px; margin: 20px 0; border-left: 4px solid #1a73e8; border-radius: 3px; }}
                .priority {{ display: inline-block; padding: 5px 15px; background-color: {priority_color}; color: white; border-radius: 3px; font-weight: bold; }}
                .button {{ display: inline-block; padding: 12px 30px; background-color: #1a73e8; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📋 New Task Assigned</h1>
                </div>
                <div class="content">
                    <h2>Hello {assignee_name},</h2>
                    
                    <p>You have been assigned a new task in the <strong>{project_name}</strong> project.</p>
                    
                    <div class="task-details">
                        <h3>{task_title}</h3>
                        <p><strong>Project:</strong> {project_name}</p>
                        <p><strong>Due Date:</strong> {due_date}</p>
                        <p><strong>Priority:</strong> <span class="priority">{priority.upper()}</span></p>
                    </div>
                    
                    <p>Click the button below to view the task details:</p>
                    <a href="{task_url}" class="button">View Task</a>
                    
                    <p>Best regards,<br><strong>Project Management Team</strong></p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 OneImperial. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        New Task Assigned
        
        Hello {assignee_name},
        
        You have been assigned a new task in the {project_name} project.
        
        Task Details:
        - Title: {task_title}
        - Project: {project_name}
        - Due Date: {due_date}
        - Priority: {priority.upper()}
        
        View task: {task_url}
        
        Best regards,
        Project Management Team
        """
        
        return self.send_email(to_email, subject, html_content, text_content)


# Create a singleton instance
email_service = EmailService()
