import requests
from dotenv import load_dotenv
import os

load_dotenv()


def format_query(true_data, false_data, preferences):
    """Format user data into a structured query for the LLM"""

    # Convert lists to comma-separated strings
    true_string = ", ".join(true_data) if true_data else "nothing specific"
    false_string = ", ".join(false_data) if false_data else "nothing specific"

    # Extract user preferences with default values
    trip_duration = preferences.get("trip_duration", "unspecified duration")
    location = preferences.get("location", "an unspecified location")
    budget = preferences.get("budget", "an unspecified budget")

    query_text = (
        f"Generate a {trip_duration} travel itinerary for {location} "
        f"with a {budget} budget."
        f"The user liked: {true_string}."
        f"The user disliked: {false_string}."
        f"Consider weather conditions and real-time events. "
        f"Restrict the response to 5 activities per day in JSON format with time, location, and cost of each activity."
    )

    return query_text


def send_query_to_LLM(query_text):
    """Send query to LLM"""
    API_KEY = os.getenv("GEMINI_API_KEY")
    LLM_API_URL = os.getenv("LLM_API_URL")
    if not API_KEY:
        raise ValueError(
            "Missing API key. Set GEMINI_API_KEY in environment variables."
        )

    url = f"{LLM_API_URL}?key={API_KEY}"
    payload = {"contents": [{"parts": [{"text": query_text}]}]}

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None


def get_prompt(choices, preferences):
    """Generate a query and fetch response from LLM"""
    true_data = choices.get("true", [])
    false_data = choices.get("false", [])

    if not (true_data or false_data):
        return "Error: No user preferences provided."

    query = format_query(true_data, false_data, preferences)
    response = send_query_to_LLM(query)

    return response or "Error retrieving response."


if __name__ == "__main__":
    choices = {
        "true": ["big ben", "hyde park", "london eye"],
        "false": ["london bridge", "tower of london"],
    }
    preferences = {
        "location": "london",
        "budget": "£1000",
        "trip_duration": "2 days",
    }

    r = get_prompt(choices, preferences)
    print(r)
