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
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from core.services.email_service import EmailService, new_email_service
from core.services.user_service import new_user_service, UserService
from core.services.token_service import new_token_service, TokenService, TokenPermission
from core.clients.mongo_client import MongoClient
from core.base.models import User, EmailPreferences
from fastapi.templating import Jinja2Templates
from core.repositories.user_repository import UserRepository
from core.handlers.env_handler import env
from slowapi.middleware import SlowAPIMiddleware
from functools import lru_cache
from api_analytics.fastapi import Analytics
# import redis

# Redis
REDIS_URL = f"redis://{env.redis['username']}:{env.redis['password']}@{env.redis['host']}:{env.redis['port']}"

# Env
NODE_ENV = env.state["node_env"]
BASE_URL = env.state["base_url"]
SECRET_KEY = env.jwt["secret"]
ALGORITHM = env.jwt["algorithm"]
CLIENT_LOCAL = env.state["client_local"]
CLIENT_PROD = env.state["client_prod"]
ALLOW_HEADERS = env.auth["allow_headers"]
ALLOW_ORIGINS = env.auth["allow_origins"]
TEMPLATE_BASE = CLIENT_PROD if NODE_ENV == "production" else CLIENT_LOCAL
ANALYTICS_KEY = env.state["analytics_key"]
RATE_LIMITED = env.state["rate_limited"] == "True"

def get_client_ip(request: Request):
    real_ip = request.headers.get("x-real-ip")
    forwarded_for = request.headers.get("x-forwarded-for")
    client_ip = get_remote_address(request)
    
    # print(f"DEBUG IP INFO:\nX-Real-IP: {real_ip}\nX-Forwarded-For: {forwarded_for}\nClient Host: {client_ip}")
    
    if forwarded_for:
        return forwarded_for.split(",")[0]
    if real_ip:
        return real_ip
    return client_ip

# Allowed origins
origins = [TEMPLATE_BASE]
for prod_url in ALLOW_ORIGINS:
    origins.append(prod_url)
    
# print("ALLOWED ORIGINS: ", origins)

@lru_cache
def get_token_service() -> TokenService:
    return new_token_service(SECRET_KEY, ALGORITHM)

@lru_cache
def get_email_service() -> EmailService:
    return new_email_service()

def get_user_service() -> UserService:
    user_repository = UserRepository(app.db["users"])
    return new_user_service(user_repository)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongo_client
    mongo_client = MongoClient()
    db = await mongo_client.ping()
    app.db = db
    yield
    await mongo_client.close()

limiter = Limiter(
    key_func=get_client_ip,
    # key_func=get_client_ip,
    # storage_uri=REDIS_URL,
    # strategy="fixed-window",
    enabled=RATE_LIMITED
)

app = FastAPI(title="Credentials Storage API", lifespan=lifespan)

# Rate limiting configuration
# limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_headers=ALLOW_HEADERS,
    allow_credentials=True,
    allow_methods=["GET", "PUT", "POST", "OPTIONS"],
)

# Static files
# https://fastapi.tiangolo.com/tutorial/static-files/
app.mount("/static", StaticFiles(directory="static"), name="static")

# https://fastapi.tiangolo.com/advanced/templates/
templates = Jinja2Templates(directory="templates")

# Analytics
# https://pypi.org/project/fastapi-analytics/
app.add_middleware(Analytics, api_key=ANALYTICS_KEY)

@app.get("/")
@limiter.limit("3/minute", per_method=True)
async def root_endpoint(request: Request):
    return JSONResponse(content={
        "ping": "pong",
        "message": "Devarno Reach Server pinged successfully :)",
    })


# @app.get("/debug-ratelimit")
# async def debug_ratelimit(request: Request):
#     ip = get_client_ip(request)
    
#     # Connect to Redis to check the keys
#     r = redis.Redis.from_url(REDIS_URL)
    
#     # Get all keys related to rate limiting
#     rate_limit_keys = r.keys("rate-limit:*")
    
#     return JSONResponse({
#         "current_ip": ip,
#         "rate_limit_keys": [key.decode() for key in rate_limit_keys],
#         "headers": dict(request.headers)
#     })

@app.post("/register")
@limiter.limit("3/minute")
async def register_user(
    request: Request,
    user: User,
    source: str,
    user_service: UserService = Depends(get_user_service),
    email_service: EmailService = Depends(get_email_service),
    token_service: TokenService = Depends(get_token_service),
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
            
        new_user = await user_service.create_user(user.email, user.name, source)
        if new_user.email:
            preferences_token = await token_service.generate_reach_token(
                uid=new_user.uid,
                permission=TokenPermission.ChangePreferences,
            )
            await email_service.send_welcome_email(
                email=new_user.email, 
                name=new_user.name,
                preferences_token=preferences_token,
            )
            verification_token = await token_service.generate_reach_token(
                uid=new_user.uid,
                email=new_user.email, # add updated email
                permission=TokenPermission.VerifyEmail,
            )
            await email_service.send_verify_email(
                name=new_user.name,
                email=new_user.email,
                verification_token=verification_token,
            )

        return JSONResponse(content={
            "message": f"Thanks for subscribing! We're excited to have you!",
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error storing credentials: {str(e)}"
        )


@app.put("/preferences")
@limiter.limit("3/minute")
async def update_email_preferences(
    request: Request,
    token: str,
    user: User,
    token_service: TokenService = Depends(get_token_service),
    user_service: UserService = Depends(get_user_service),
    email_service: EmailService = Depends(get_email_service),
):
    """Update email preferences"""
    
    # Verify permissions
    verified = await token_service.verify_reach_token(
        token=token,
        permissions=[TokenPermission.ChangePreferences],
    )
    if not verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    
    # Get current user data
    current_user_data = await user_service.get_user(verified["uid"])
    if not current_user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    is_new_email = False
    
    # Update user data
    updated_user = await user_service.update_user(verified["uid"], user.name, user.email, user.preferences.model_dump())
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Preferences endpoint failed",
        )
    
    # Check if email has changed
    if not current_user_data.email == updated_user.email:
        is_new_email = True
        await user_service.reset_email_verification(updated_user.uid)
        verification_token = await token_service.generate_reach_token(
            uid=updated_user.uid,
            email=updated_user.email, # add updated email
            permission=TokenPermission.VerifyEmail,
        )
        await email_service.send_verify_email(updated_user.email, verification_token, updated_user.name)

    # Check if user is unsubscribed
    if not updated_user.preferences.content and not updated_user.preferences.marketing and not updated_user.preferences.product:
        await email_service.send_unsubscribe_confirmation_email(updated_user.email, token, updated_user.name)

    return JSONResponse(content={
        "message": f'Preferences updated! {"Please check your inbox." if is_new_email else "You're all set!"}',
    })

@app.put("/unsubscribe")
@limiter.limit("3/minute")
async def unsubscribe(
    request: Request,
    token: str,
    token_service: TokenService = Depends(get_token_service),
    email_service: EmailService = Depends(new_email_service),
    user_service: UserService = Depends(get_user_service),

):
    """Handle unsubscribe requests"""
    
    # Verify permissions
    verified = await token_service.verify_reach_token(
        token=token,
        permissions=[TokenPermission.ChangePreferences],
    )
    if not verified:
        raise HTTPException(status_code=400, detail="Invalid reach token")
    
    # Check if already unsubscribed
    user_data = await user_service.get_user(identifier=verified["uid"])
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if not user_data.preferences.marketing and not user_data.preferences.content and not user_data.preferences.product:
        return JSONResponse(content={
            "message": "You're already unsubscribed! Bye for now :(",
        })
    
    # Unsubscribe user
    user = await user_service.unsubscribe_user(verified["uid"])
    if not user:
        raise HTTPException(status_code=500, detail="User not found")
    
    # Email/response
    await email_service.send_unsubscribe_confirmation_email(user.email, token, user.name)
    return JSONResponse(content={
        "message": "You've been unsubscribed! Bye for now :(",
    })

@app.get("/verify")
@limiter.limit("3/minute")
async def verify_email(
    request: Request,
    token: str,
    user_service: UserService = Depends(get_user_service),
    token_service: TokenService = Depends(get_token_service),
):
    try:
        verified = await token_service.verify_reach_token(
                token=token,
            permissions=[TokenPermission.VerifyEmail],
        )
        
        if not verified:
            raise HTTPException(status_code=400, detail="Invalid reach token")
        
        user = await user_service.get_user(identifier=verified["uid"])
        if not user:
            raise HTTPException(status_code=500, detail="User not found")
        
        # Verify updated email
        if not "email" in verified or not verified["email"] == user.email or not "uid" in verified or not verified["uid"] == user.uid:
            raise HTTPException(status_code=401, detail="Invalid permissions")
        
        if user.emailVerified:
            raise HTTPException(status_code=401, detail="Email is already verified")
        
        await user_service.confirm_email_verified(user.uid)
        return JSONResponse(content={
            "message": "Email verified! You're all set!",
        })
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/user")
@limiter.limit("3/minute")
async def get_user_controller(
    request: Request,
    token: str,
    user_service: UserService = Depends(get_user_service),
    token_service: TokenService = Depends(get_token_service),
):
    try:
        verified = await token_service.verify_reach_token(
            token=token,
            permissions=[
                TokenPermission.ChangePreferences,
                TokenPermission.VerifyEmail,
            ],
        )
        if not verified:
            raise HTTPException(status_code=400, detail="Invalid reach token")
        return await user_service.get_user(identifier=verified["uid"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user data: {e}")


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
            "banner_text": "Welcome to the journey",
            "preferences_url": f"{TEMPLATE_BASE}/preferences/foo_token",
            "unsubscribe_url": f"{TEMPLATE_BASE}/unsubscribe/foo_token"

        }
    )

@app.get("/template/unsubscribe", response_class=HTMLResponse)
@limiter.limit("3/minute")
async def test_unsubscribe_email(request: Request):
    """Test endpoint to preview the product email template"""
    return templates.TemplateResponse(
        "unsubscribe-email.html",
        {
            "request": request,
            "banner_text": "See you again soon",
            "base_url": BASE_URL,
            "name": "Penelope",
            "preferences_url": f"{TEMPLATE_BASE}/preferences?token=foo_token",
        }
    )
    
@app.get("/template/verify-email", response_class=HTMLResponse)
@limiter.limit("3/minute")
async def test_verify_email_template(request: Request):
    """Test endpoint to preview the verify email template"""
    return templates.TemplateResponse(
        "verify-email.html",
        {
            "request": request,
            "banner_text": "Verify Your Email Address",
            "base_url": BASE_URL,
            "name": "Rosstipher",
            "verification_url": f"{TEMPLATE_BASE}/verify?token=foo_token",
        }
    )

@app.get("/template/product", response_class=HTMLResponse)
@limiter.limit("3/minute")
async def test_product_update(request: Request):
    """Render a product update email with mock data"""
    return templates.TemplateResponse(
        "product-email.html", 
        {
            "request": request,
            "name": "Alex",
            "banner_text": "Product Update",
            "base_url": BASE_URL,
            "feature_one": "Improved User Dashboard",
            "feature_two": "Seamless Integration with Third-Party Tools",
            "changelog_url": f"{TEMPLATE_BASE}/changelog",
            "feedback_url": f"{TEMPLATE_BASE}/feedback",
        },
    )
