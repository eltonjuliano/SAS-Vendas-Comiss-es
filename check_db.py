from services.supabase_client import supabase

try:
    res = supabase.table("profiles").select("*").limit(1).execute()
    if res.data:
        prof = res.data[0]
        print("Profile Data Keys:", list(prof.keys()))
        print("cycle_start_date:", prof.get("cycle_start_date"))
        print("cycle_end_date:", prof.get("cycle_end_date"))
    else:
        print("No profiles found")
except Exception as e:
    print("Error:", e)
