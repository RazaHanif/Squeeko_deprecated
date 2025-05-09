import os

TEST_TOKEN = "BEARER test_123"

async def verify_token(auth_header: str | None) -> bool:
    """ 
    Verifies the auth token from the header
    """
    
    if auth_header is None:
        return False
    
    # --- Simple Test Token Check
    if auth_header == TEST_TOKEN:
        print("INFO: Test token accepted")
        return True
        
    if auth_header.startswith("Bearer "):
        real_token = auth_header.split(" ")[1]
        print(f"INFO: Real token verifcation not implmented: {real_token}")
        return False
    
    print("WARNING: Invalid auth token")
    return False
