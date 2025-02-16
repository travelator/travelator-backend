import requests
from supabase import create_client

LLM_API_URL =""
SUPABASE_URL = "https://your-supabase-url.supabase.co"
SUPABASE_KEY = "your-supabase-key"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_user_preferences(user_id):
    """Fetch user preferences from the database"""
    response = supabase.table("preferences").select("*").eq("user_id", user_id).execute()
    if response.data:
        return response.data[0]  # Return first match
    return None

def format_query(user_data):
    "Format user data into a structured query for the LLM"
    preferred_activities = ','.join([k for k, v in user_data['preferences'].items() if v == 1])

    query_text = (
        f"Generate a {user_data['trip_duration']} travel itinerary for {user_data['location']}"
        f" with a {user_data['budget']} budget. The user prefers {preferred_activities}. "
        f"Consider weather condition and real-time events"
    )
    return query_text

def send_query_to_LLM(query_text):
    """Send query to LLM"""
    payload = {"query": query_text}
    response = requests.post(LLM_API_URL, json=payload)
    return response.json() if response.status_code == 200 else None