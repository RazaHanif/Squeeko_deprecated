import os

async def verify_token(token: str) -> bool:
    # Placeholder - validate with JWT
    # For testing can use fixed string
    return token.replace("Bearer ", "") == os.getenv("TEST_ACCESS_TOKEN", "dev-token")
