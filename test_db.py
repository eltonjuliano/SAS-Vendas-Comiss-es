import os
import sys
from dotenv import load_dotenv

load_dotenv()

from services.supabase_client import supabase

try:
    res = supabase.table("profiles").select("cycle_start_day").limit(1).execute()
    print("CURRENT VAL:", res.data)
    
    # Try updating to string
    if res.data:
        prof_id = supabase.auth.get_user().user.id if hasattr(supabase.auth, 'get_user') else None
        # Actually I can't update without auth. Let's just print type.
        print("Done")
except Exception as e:
    print("Error:", e)
