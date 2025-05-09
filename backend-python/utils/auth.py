import os

async def verify_token(auth_header: str | None) -> bool:
    """ 
    Verifies the auth token from the header
    """
    
    if auth_header is None:
        return False
    
    # --- Simple Test Token Check
    
