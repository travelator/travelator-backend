import os
import json
from langchain.llms import OpenAI  # Assuming OpenAI API usage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize LangChain LLM
llm = OpenAI(api_key=OPENAI_API_KEY)

# Predefined list of popular cities
CITIES = [
    "London (United Kingdom)", "New York (United States)", "Paris (France)", "Tokyo (Japan)",
    "Los Angeles (United States)", "Berlin (Germany)", "Toronto (Canada)", "Sydney (Australia)",
    "Madrid (Spain)", "Rome (Italy)", "Chicago (United States)", "Dubai (UAE)", "Hong Kong (China)",
    "Singapore (Singapore)", "Bangkok (Thailand)", "Amsterdam (Netherlands)", "Istanbul (Turkey)",
    "Seoul (South Korea)", "San Francisco (United States)", "Barcelona (Spain)"
]


def generate_activities_for_swiping(city):
    """
    Generates a list of activities for the user to swipe on using OpenAI.
    """
    prompt = f"""
    List 15 unique tourist activities in {city}.
    Each activity should have:
    - Name
    - Short description
    - Price (Free, $, $$, $$$)
    - Category (e.g., Adventure, Culture, Family, Food, Relaxation)
    - Ideal time of day (Morning, Afternoon, Evening)

    Return as JSON format:
    [
      {{
        "name": "Activity Name",
        "description": "Short description",
        "price": "Free / $ / $$ / $$$",
        "category": "Category",
        "time_of_day": "Morning / Afternoon / Evening"
      }},
      ...
    ]
    """

    try:
        response = llm.invoke(prompt)
        activities = json.loads(response)
        return activities if isinstance(activities, list) else []
    except Exception as e:
        print(f"❌ OpenAI Error: {e}")
        return []


def generate_itinerary_from_likes(city, liked_activities):
    """
    Generates an itinerary based on the activities the user liked.
    """
    prompt = f"""
    Create a personalized itinerary for {city} based on these user preferences:
    {json.dumps(liked_activities)}

    Generate a schedule for a single day, balancing the chosen activities with similar ones.
    Each itinerary item should have:
    - Name
    - Description
    - Start time
    - Duration
    - If booking is required, provide a placeholder link.

    Return as JSON format:
    [
      {{
        "name": "Activity Name",
        "description": "Short description",
        "start_time": "HH:MM AM/PM",
        "duration": "X hours",
        "booking_required": true/false,
        "booking_link": "URL if applicable"
      }},
      ...
    ]
    """
    try:
        response = llm.invoke(prompt)
        itinerary = json.loads(response)
        return itinerary if isinstance(itinerary, list) else []
    except Exception as e:
        print(f"❌ OpenAI Error: {e}")
        return []


def handle_user_selection():
    """
    Handles the two-step process:
    1. Lets user select a city from a predefined list.
    2. Generates activities for swiping.
    3. Accepts user likes and generates an itinerary.
    """
    print("\n🌍 Available cities:")
    for idx, city in enumerate(CITIES, 1):
        print(f"{idx}. {city}")

    while True:
        try:
            choice = int(input("\nEnter the number of the city you want to explore: "))
            if 1 <= choice <= len(CITIES):
                city = CITIES[choice - 1]
                break
            else:
                print("❌ Invalid choice. Please enter a number from the list.")
        except ValueError:
            print("❌ Please enter a valid number.")

    print(f"\n🔍 Generating activities for swiping in {city}...\n")
    activities = generate_activities_for_swiping(city)

    if activities:
        liked_activities = []
        for activity in activities:
            print(f"🏛 {activity['name']} | {activity['price']} | {activity['category']}")
            print(f"   📖 {activity['description']}")
            print(f"   ⏰ Best time: {activity['time_of_day']}")
            print("-" * 60)

            user_input = input("Do you like this activity? (yes/no): ").strip().lower()
            if user_input == "yes":
                liked_activities.append(activity)

        if liked_activities:
            print("\n✅ You liked the following activities:")
            for a in liked_activities:
                print(f"⭐ {a['name']}")

            print("\n🔍 Generating final itinerary based on your preferences...\n")
            itinerary = generate_itinerary_from_likes(city, liked_activities)

            if itinerary:
                print(f"🎉 Here is your customized itinerary for {city}:\n")
                for place in itinerary:
                    print(f"🏛 {place['name']}")
                    print(f"   📖 {place['description']}")
                    print(f"   ⏰ Start time: {place['start_time']} | Duration: {place['duration']}")
                    print(f"   🔗 Booking: {'Yes' if place['booking_required'] else 'No'}")
                    if place['booking_required']:
                        print(f"   👉 {place['booking_link']}")
                    print("-" * 60)
            else:
                print(f"❌ Could not generate an itinerary for {city}.")
        else:
            print("❌ No activities were liked, so no itinerary was generated.")
    else:
        print(f"❌ No activities found for {city}.")


if __name__ == "__main__":
    handle_user_selection()
