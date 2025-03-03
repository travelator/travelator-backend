import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain.llms import OpenAI  # Assuming OpenAI API usage
from dotenv import load_dotenv
import sqlalchemy as db

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize LangChain LLM
llm = OpenAI(api_key=OPENAI_API_KEY)

# Database setup
engine = db.create_engine("sqlite:///database.db")  # Using SQLite for simplicity
metadata = db.MetaData()
activities_table = db.Table(
    "activities",
    metadata,
    db.Column("id", db.Integer, primary_key=True),
    db.Column("city", db.String(100)),
    db.Column("name", db.String(200)),
    db.Column("description", db.Text),
    db.Column("price", db.String(10)),
    db.Column("category", db.String(50)),
    db.Column("time_of_day", db.String(20)),
)
metadata.create_all(engine)


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


@app.route("/activities", methods=["GET"])
def get_activities():
    city = request.args.get("city", "London")
    activities = generate_activities_for_swiping(city)
    return jsonify(activities)


@app.route("/itinerary", methods=["POST"])
def create_itinerary():
    data = request.json
    city = data.get("city", "London")
    liked_activities = data.get("liked_activities", [])
    itinerary = generate_itinerary_from_likes(city, liked_activities)
    return jsonify(itinerary)


if __name__ == "__main__":
    app.run(debug=True)
