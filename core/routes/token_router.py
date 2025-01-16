
# Example usage in FastAPI routes:
@app.post("/generate-unsubscribe")
async def generate_unsubscribe_link(email: str):
    """Generate an unsubscribe link for testing"""
    token = await token_service.generate_unsubscribe_token(
        email,
        additional_data={"user_id": "123"}  # optional additional data
    )
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    unsubscribe_url = f"{base_url}/unsubscribe?token={token}"
    return {"unsubscribe_url": unsubscribe_url}

@app.get("/verify-token/{token}")
async def verify_token(token: str):
    """Verify an unsubscribe token"""
    email = await token_service.verify_unsubscribe_token(token)
    return {"email": email}