import requests
#from supabase import create_client

LLM_API_URL ="https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=AIzaSyDv7vJSFv4BhSq1G9ykI5Ik3WOZ74xbYu4"
#SUPABASE_URL = "https://your-supabase-url.supabase.co"
#SUPABASE_KEY = "your-supabase-key"
#supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
    LLM_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    API_KEY = "AIzaSyDv7vJSFv4BhSq1G9ykI5Ik3WOZ74xbYu4"
    
    url = f"{LLM_API_URL}?key={API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": query_text
            }]
        }]
    }
    
    response = requests.post(url, json=payload)
    return response.json() if response.status_code == 200 else None

if __name__ == "__main__":

    user_data = {'trip_duration' : "2 days", 'location' : "London", 'budget' : "£1000", 'preferences' : {"shopping" : 1, "sightseeing" : 1, "dining" : 1, "preferences" : {"shopping" : 1, "sightseeing" : 1, "dining" : 1}}}
    preferred_activities = ','.join([k for k, v in user_data['preferences'].items() if v == 1])
    
    query_text = (
        f"Generate a {user_data['trip_duration']} travel itinerary for {user_data['location']}"
        f" with a {user_data['budget']} budget. The user prefers {preferred_activities}. "
        f"Consider weather condition and real-time events and restrict the returned response to 5 activities per day and in JSON format with the time, location and cost of the activity listed"
    )

    response = send_query_to_LLM(query_text)
    print(response)    
