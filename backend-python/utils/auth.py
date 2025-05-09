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
        
        
    
