from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Optional
from mailjet_rest import Client
import asyncio
from functools import partial
from core.services.token_service import TokenService
from core.handlers.env_handler import env

BASE_URL = env.state["base_url"]
SENDER_EMAIL = env.state["sender"]
MAILJET_API_KEY = env.mailjet["api_key"]
MAILJET_SECRET_KEY = env.mailjet["secret_key"]

class EmailService(TokenService):
    def __init__(self):
        self.mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_SECRET_KEY), version='v3.1')
        self.env = Environment(
            loader=FileSystemLoader(Path("templates")),
            autoescape=select_autoescape(["html"])
        )

    async def send_welcome_email(self,
        email: str,
        preferences_token: str,
        name: Optional[str] = None,
    ):
        """Send welcome email using the template"""
        try:
            # Load template
            preferences_url = f"https://devarno.com/preferences?token={preferences_token}"
            template = self.env.get_template("welcome-email.html")
                        
            # Prepare template variables
            template_vars = {
                "name": name or email,
                "base_url": BASE_URL,
                "banner_text": "Welcome to the journey",
                "preferences_url": preferences_url,
            }
            
            # Render template
            html_content = template.render(**template_vars)
            
            # Prepare email data
            data = {
                'Messages': [{
                    "From": {"Email": SENDER_EMAIL, "Name": "Devarno"},
                    "To": [{"Email": email, "Name": name or email}],
                    "Subject": "Welcome to the journey",
                    "HTMLPart": html_content,
                    "TextPart": f"""
                    Hello {name or 'there'},

                    Thanks for joining this indie dev journey!
                    
                    You can updated your email preferences at:
                    {preferences_url}
                    
                    If you have any questions, just reply to this email.
                    
                    Best regards,
                    Alex
                    """
                }]
            }
            
            # Send email asynchronously
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, partial(self.mailjet.send.create, data=data))
            return response
            
        except Exception as e:
            print(f"Error sending welcome email: {str(e)}")
            # You might want to log this error or handle it differently
            raise
        
    async def send_unsubscribe_confirmation_email(self,
        email: str,
        preferences_token: str,
        name: Optional[str] = None,
    ):
        """Send unsubscribe confirmation email"""
        try:
            preferences_url = f"https://devarno.com/preferences?token={preferences_token}"
            template = self.env.get_template("unsubscribe-email.html")
            template_vars = {    
                "name": name or email,
                "base_url": BASE_URL,                
                "banner_text": "See you again soon",
                "preferences_url": preferences_url,
            }
            html_content = template.render(**template_vars)
            data = {
                'Messages': [
                    {
                        "From": {
                            "Email": SENDER_EMAIL,
                            "Name": "Devarno"
                        },
                        "To": [{"Email": email, "Name":name}],
                        "Subject": "Unsubscribe Confirmation",
                        "HTMLPart": html_content,
                        "TextPart": f"""
                            Hello {name},
                            
                            This email confirms that you have been unsubscribed from Devarno.com updates and notifications.
                            
                            If you unsubscribed by mistake, you can resubscribe at:
                            {preferences_url}
                            
                            Best regards,
                            The Team
                        """
                    }
                ]
            }
            
            # Send email asynchronously
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, partial(self.mailjet.send.create, data=data))
            
        except Exception as e:
            print(f"Error sending unsubscribe confirmation: {str(e)}")
            # Log the error but don't raise - we don't want to break the unsubscribe flow
            # Consider adding proper error logging here
            
    async def send_verify_email(self, 
        email: str,
        verification_token: str,
        name: Optional[str] = None,
    ):
        """Send email verification link using the template"""
        try:
            verification_url = f"https://devarno.com/verify?token={verification_token}"
            template = self.env.get_template("verify-email.html")
            template_vars = {
                "name": name or email,
                "base_url": BASE_URL,
                "verification_url": verification_url,
                "banner_text": "Verify Your Email Address",
            }
            html_content = template.render(**template_vars)
            data = {
                'Messages': [{
                    "From": {"Email": SENDER_EMAIL, "Name": "Devarno"},
                    "To": [{"Name": name or email, "Email": email}],
                    "Subject": "Verify Your Email Address",
                    "HTMLPart": html_content,
                    "TextPart": f"""
                    Hi {name or 'there'},

                    Thank you for signing up with Devarno! Please verify your email address by clicking the link below:

                    {verification_url}

                    If you didn’t sign up, you can safely ignore this email.

                    Cheers,
                    Alex
                    """
                }]
            }
            
            # Send the email asynchronously
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, partial(self.mailjet.send.create, data=data))
            
        except Exception as e:
            print(f"Error sending verification email: {str(e)}")
            # Log or handle the error as needed
            raise

def new_email_service() -> EmailService:
    """EmailService factory"""
    return EmailService()