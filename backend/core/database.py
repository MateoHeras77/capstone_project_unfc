import os
from supabase import create_client, Client
from typing import Optional
from dotenv import load_dotenv

# Load env vars from the root .env
load_dotenv()

# These would typically come from environment variables
SUPABASE_URL: Optional[str] = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: Optional[str] = os.environ.get("SUPABASE_KEY")

def get_supabase_client() -> Client:
    """Initializes and returns the Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        # For boilerplate/setup, we might not have these yet
        print("Warning: SUPABASE_URL or SUPABASE_KEY not set.")
        # Returning a dummy or raising error depending on usage
        
    return create_client(SUPABASE_URL, SUPABASE_KEY)
