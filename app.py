# Testing Checklist:

# Database:

#  Records are properly created
#  Unique constraints work
#  Email preferences are stored


# Rate Limiting:

#  Limits are enforced
#  Error messages are clear
#  Counter resets after time period


# Emails:

#  Welcome emails are sent
#  Templates render correctly
#  Unsubscribe links work
#  Preferences can be updated


# Error Handling:

#  Duplicate entries are prevented
#  Invalid formats are caught
#  Missing required fields are caught
#  Clear error messages are returned


from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.responses import HTMLResponse

from fastapi.responses import JSONResponse

from motor.motor_asyncio import AsyncIOMotorClient
# from typing import Optional
import os
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from core.services.email_service import EmailService, new_email_service
from core.services.user_service import new_user_service, UserService
from core.clients.mongo_client import MongoClient
from mailjet_rest import Client
from core.base.models import User, EmailPreferences
from fastapi.templating import Jinja2Templates
from core.repositories.user_repository import UserRepository

from core.handlers.env_handler import env

BASE_URL = env.state["base_url"]


# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongo_client
    mongo_client = MongoClient()
    db = await mongo_client.ping()
    app.db = db
    yield
    await mongo_client.close()
    
    
# Initialize FastAPI app
app = FastAPI(title="Credentials Storage API", lifespan=lifespan)

# Static files
# https://fastapi.tiangolo.com/tutorial/static-files/
app.mount("/static", StaticFiles(directory="static"), name="static")

# https://fastapi.tiangolo.com/advanced/templates/
templates = Jinja2Templates(directory="templates")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        name="exception.html",
        context={"request": request, "detail": exc},
        status_code=status.HTTP_400_BAD_REQUEST,
    )
    
# Add these to your existing FastAPI app
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
NODE_ENV = os.getenv("NODE_ENV", "development")
ALGORITHM = "HS256"

# Rate limiting configuration
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")
COLLECTION_NAME = "users"

@app.get("/")
@limiter.limit("3/minute")
async def root_endpoint(request: Request):
    return JSONResponse(content={
        "ping": "pong",
        "message": "Devarno Reach Server pinged successfully :)"
    })

async def handle_user_service() -> UserService:
    """Handle UserService initialisation within app context"""
    user_repository = UserRepository(app.db["users"])
    user_service = new_user_service(user_repository)
    return user_service



@app.post("/register", response_model=User)
@limiter.limit("5/minute")
async def register_user(
    request: Request,
    user: User,
    user_service: UserService = Depends(handle_user_service),
    email_service: EmailService = Depends(new_email_service),
):
    """
    Register user in MongoDB and send welcome email if new user.
    Rate limited to 5 requests per minute per IP address.
    At least one identifier (email or atproto_did) must be provided.
    """
    try:
        existing_user = await user_service.get_user(identifier=user.email)
        if existing_user:
            if existing_user.preferences.model_dump() == EmailPreferences().model_dump():
                return JSONResponse(content={
                    "message": f"You're already on our list! Stay tuned for updates.",
                })
            else:
                _ = await user_service.resubscribe_user(existing_user.uid)
                return JSONResponse(content={
                    "message": "Welcome back! You've been successfully resubscribed.",
                })
            
        new_user = await user_service.create_user(
            email=user.email,
            name=user.name,
            source=user.source,
        )
        
        if new_user.email:
            await email_service.send_welcome_email(new_user.email, new_user.uid, new_user.name)
            
        return JSONResponse(content={
            "message": f"Thanks for subscribing! We're excited to have you!",
        })
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error storing credentials: {str(e)}"
        )


@app.put("/preferences/{uid}")
@limiter.limit("5/minute")
async def update_email_preferences(
    request: Request,
    token: str,
    uid: str,
    user: User,
    user_service: UserService = Depends(handle_user_service),
    email_service: EmailService = Depends(new_email_service),

):
    """Update email preferences"""
    user_uid = await email_service.verify_reach_token(token, uid)
    if not user_uid:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = await user_service.update_user(uid, user.name, user.email, user.preferences.model_dump())
    if not user:
        raise HTTPException(status_code=400, detail="Preferences endpoint failed")
    return JSONResponse(content={
        "message": "Preferences updated! You're all set!",
    })


@app.put("/unsubscribe/{uid}")
@limiter.limit("5/minute")
async def unsubscribe(
    request: Request,
    uid: str,
    token: str,
    email_service: EmailService = Depends(new_email_service),
    user_service: UserService = Depends(handle_user_service),

):
    """Handle unsubscribe requests"""
    user_uid = await email_service.verify_reach_token(token, uid)
    if not user_uid:
        raise HTTPException(status_code=400, detail="Invalid reach token")
    user = await user_service.unsubscribe_user(user_uid)
    if not user:
        raise HTTPException(status_code=500, detail="Could not unsubscribe, try again later")
    await email_service.send_unsubscribe_confirmation_email(user.email, user.uid, user.name)
    return JSONResponse(content={
        "message": "You've been unsubscribed! Bye for now.",
    })

@app.get("/template/welcome", response_class=HTMLResponse)
@limiter.limit("3/minute")
async def test_welcome_email(request: Request):
    """Test endpoint to preview the welcome email template"""
    return templates.TemplateResponse(
        "welcome-email.html",
        {
            "request": request,
            "name": "Freddy",
            "base_url": BASE_URL,
            "unsubscribe_token": "#",
        }
    )

@app.get("/template/product", response_class=HTMLResponse)
async def test_product_email(request: Request):
    """Test endpoint to preview the product email template"""
    return templates.TemplateResponse(
        "product-email.html",
        {
            "request": request,
            "base_url": BASE_URL,
            "name": "Felipe",
            "unsubscribe_token": "#",
        }
    )

@app.get("/template/unsubscribe", response_class=HTMLResponse)
async def test_unsubscribe_email(request: Request):
    """Test endpoint to preview the product email template"""
    return templates.TemplateResponse(
        "unsubscribe-email.html",
        {
            "request": request,
            "banner_text": "See you again soon",
            "base_url": BASE_URL,
            "name": "Felipe",
            "resubscribe_token": "#",
        }
    )
    