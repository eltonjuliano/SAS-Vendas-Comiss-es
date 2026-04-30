import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

try:
    # Try fetching a profile
    res = supabase.table("profiles").select("*").limit(1).execute()
    print("Profile schema/data:")
    print(res.data)
except Exception as e:
    print(e)
