"""Email service using Mailgun API for Project Management notifications."""

import logging
from typing import Optional
import httpx
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

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
            
            for _attempt in Retrying(
                retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=4),
                reraise=True,
            ):
                with _attempt:
                    response = httpx.post(
                        self.base_url,
                        auth=("api", self.api_key),
                        data=data,
                        timeout=httpx.Timeout(10.0, connect=5.0),
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
    
    def send_task_due_soon_email(
        self,
        to_email: str,
        assignee_name: str,
        task_title: str,
        project_name: str,
        due_date: str,
        hours_remaining: int,
        task_url: str
    ) -> bool:
        """Send task due soon reminder."""
        subject = f"⏰ Task Due Soon: {task_title}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #ffc107; color: #333; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }}
                .reminder {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 20px; margin: 20px 0; }}
                .task-details {{ background-color: #fff; padding: 20px; margin: 20px 0; border-left: 4px solid #ffc107; }}
                .button {{ display: inline-block; padding: 12px 30px; background-color: #ffc107; color: #333; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⏰ Task Due Soon</h1>
                </div>
                <div class="content">
                    <h2>Hello {assignee_name},</h2>
                    
                    <div class="reminder">
                        <strong>Reminder:</strong> Your task is due in <strong>{hours_remaining} hours</strong>!
                    </div>
                    
                    <div class="task-details">
                        <h3>Task Details:</h3>
                        <p><strong>Task:</strong> {task_title}</p>
                        <p><strong>Project:</strong> {project_name}</p>
                        <p><strong>Due Date:</strong> {due_date}</p>
                    </div>
                    
                    <p>Please ensure you complete this task before the deadline.</p>
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
        Task Due Soon
        
        Hello {assignee_name},
        
        Reminder: Your task is due in {hours_remaining} hours!
        
        Task Details:
        - Task: {task_title}
        - Project: {project_name}
        - Due Date: {due_date}
        
        Please ensure you complete this task before the deadline.
        
        View task: {task_url}
        
        Best regards,
        Project Management Team
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_task_overdue_email(
        self,
        to_email: str,
        assignee_name: str,
        task_title: str,
        project_name: str,
        due_date: str,
        days_overdue: int,
        task_url: str
    ) -> bool:
        """Send task overdue alert."""
        subject = f"🚨 Task Overdue: {task_title}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }}
                .urgent {{ background-color: #f8d7da; border-left: 4px solid #dc3545; padding: 20px; margin: 20px 0; }}
                .button {{ display: inline-block; padding: 12px 30px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 Task Overdue</h1>
                </div>
                <div class="content">
                    <h2>Hello {assignee_name},</h2>
                    
                    <div class="urgent">
                        <strong>⚠️ URGENT:</strong> Your task is <strong>{days_overdue} {"day" if days_overdue == 1 else "days"} overdue</strong>!
                        <p><strong>Task:</strong> {task_title}</p>
                        <p><strong>Project:</strong> {project_name}</p>
                        <p><strong>Was Due:</strong> {due_date}</p>
                    </div>
                    
                    <p>This task requires immediate attention. Please complete it as soon as possible or update the status.</p>
                    <a href="{task_url}" class="button">Update Task</a>
                    
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
        Task Overdue - URGENT
        
        Hello {assignee_name},
        
        URGENT: Your task is {days_overdue} {"day" if days_overdue == 1 else "days"} overdue!
        
        Task: {task_title}
        Project: {project_name}
        Was Due: {due_date}
        
        This task requires immediate attention.
        
        Update task: {task_url}
        
        Best regards,
        Project Management Team
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    # TODO: Future Notifications to Implement
    # - send_project_created_email() - Notify all team members
    # - send_project_status_changed_email() - Update to stakeholders
    # - send_project_deadline_approaching_email() - 7 days before deadline
    # - send_task_completed_email() - Notify project manager
    # - send_task_comment_added_email() - Notify task participants
    # - send_variation_requested_email() - Notify approver
    # - send_variation_approved_email() - Notify requester
    # - send_variation_rejected_email() - Notify requester with reason
    # See EMAIL_NOTIFICATIONS_TODO.md for full details
    
    def send_project_milestone_reached_email(
        self,
        to_email: str,
        team_member_name: str,
        project_name: str,
        milestone_name: str,
        completion_date: str,
        project_url: str
    ) -> bool:
        """Send project milestone celebration email."""
        subject = f"🎉 Milestone Achieved: {milestone_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }}
                .celebration {{ background-color: #e3f2fd; border-left: 4px solid #667eea; padding: 30px; margin: 20px 0; text-align: center; }}
                .emoji {{ font-size: 48px; margin: 20px 0; }}
                .button {{ display: inline-block; padding: 12px 30px; background-color: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0; font-size: 36px;">🎉 Milestone Achieved! 🎉</h1>
                </div>
                <div class="content">
                    <h2>Hello {team_member_name},</h2>
                    
                    <div class="celebration">
                        <div class="emoji">🎊 🎈 ✨ 🏆</div>
                        <h3 style="color: #667eea; font-size: 24px;">{milestone_name}</h3>
                        <p style="font-size: 18px; margin: 20px 0;">
                            <strong>Project:</strong> {project_name}
                        </p>
                        <p style="font-size: 16px;">
                            <strong>Completed:</strong> {completion_date}
                        </p>
                    </div>
                    
                    <p style="font-size: 16px;">
                        Congratulations on reaching this important milestone! Your hard work and dedication 
                        have brought the project one step closer to completion.
                    </p>
                    
                    <p style="font-size: 16px;">
                        Keep up the excellent work!
                    </p>
                    
                    <a href="{project_url}" class="button">View Project</a>
                    
                    <p style="text-align: center;">
                        Best regards,<br><strong>Project Management Team</strong>
                    </p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 OneImperial. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Milestone Achieved!
        
        Hello {team_member_name},
        
        Congratulations! The project has reached an important milestone.
        
        Milestone: {milestone_name}
        Project: {project_name}
        Completed: {completion_date}
        
        Your hard work and dedication have brought the project one step closer to completion.
        
        Keep up the excellent work!
        
        View project: {project_url}
        
        Best regards,
        Project Management Team
        """
        
        return self.send_email(to_email, subject, html_content, text_content)


# Create a singleton instance
email_service = EmailService()
