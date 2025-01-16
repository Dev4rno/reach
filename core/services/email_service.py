from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Optional
from mailjet_rest import Client
import asyncio
from functools import partial
from core.services.token_service import TokenService
from jinja2 import Template
from core.handlers.env_handler import env

BASE_URL = env.state["base_url"]
SENDER_EMAIL = env.state["sender"]
MAILJET_API_KEY = env.mailjet["api_key"]
MAILJET_SECRET_KEY = env.mailjet["secret_key"]

class EmailService(TokenService):
    def __init__(self):
        super().__init__()
        auth = (MAILJET_API_KEY, MAILJET_SECRET_KEY)
        self.mailjet = Client(auth=auth, version='v3.1')
        self.templates_dir = Path("templates")
        self.welcome_template_path = self.templates_dir / "welcome-email.html"
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

    async def send_welcome_email(self, email: str, uid: str, name: Optional[str] = None):
        """Send welcome email using the template"""
        try:
            # Load template
            template = self.env.get_template("welcome-email.html")
            
            # Generate unsubscribe token (assuming this function exists)
            unsubscribe_token = await self.generate_reach_token(uid)
            
            # Prepare template variables
            template_vars = {
                "name": name or email,
                "base_url": BASE_URL,
                "banner_text": "Welcome to the journey",
                "unsubscribe_token": unsubscribe_token,
            }
            
            # Render template
            html_content = template.render(**template_vars)
            
            # Prepare email data
            data = {
                'Messages': [{
                    "From": {
                        "Email": SENDER_EMAIL,
                        "Name": "Devarno"
                    },
                    "To": [{"Email": email, "Name": name or email}],
                    "Subject": "Thanks for signing up",
                    "HTMLPart": html_content,
                    "TextPart": f"""
                    Hello {name or 'there'},

                    Thanks for joining this indie dev journey!
                    
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
        
    async def send_unsubscribe_confirmation_email(self, email: str, uid: str, name: Optional[str] = None):
        """Send unsubscribe confirmation email"""
        try:
            # Load unsubscribe template
            template = self.env.get_template("unsubscribe-email.html")

            # Generate resubscribe token
            resubscribe_token = await self.generate_reach_token(uid)
            template_vars = {    
                "name": name or email,
                "base_url": BASE_URL,                
                "banner_text": "See you again soon",
                "resubscribe_token": resubscribe_token,
            }
            
            # Render template
            html_content = template.render(**template_vars)

            # Prepare email data
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
                            https://devarno.com/resubscribe?token={resubscribe_token}
                            
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
            
def new_email_service() -> EmailService:
    return EmailService()