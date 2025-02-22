import os
import requests
from dotenv import load_dotenv

# Load API Keys (if needed)
load_dotenv()

# OpenTripMap API Key
OPENTRIPMAP_API_KEY = os.getenv("OPENTRIPMAP_API_KEY")

# OpenTripMap Base URL
OPENTRIPMAP_BASE_URL = "https://api.opentripmap.com/0.1/en/places/"

# List of Cities
CITIES = ["London", "New York", "Tokyo", "Paris", "Berlin"]


### **1. Fetch Places from OpenTripMap API**
def fetch_places_opentripmap(city):
    """Fetches top 20 high-rated tourist attractions from OpenTripMap API."""
    url = f"{OPENTRIPMAP_BASE_URL}geoname"
    params = {"name": city, "apikey": OPENTRIPMAP_API_KEY}

    city_data = requests.get(url, params=params).json()

    if "lat" not in city_data or "lon" not in city_data:
        print(f"❌ No coordinates found for {city}.")
        return []

    lat, lon = city_data["lat"], city_data["lon"]

    url_places = f"{OPENTRIPMAP_BASE_URL}radius"
    params = {
        "radius": 10000,  # 10km search radius
        "lon": lon,
        "lat": lat,
        "kinds": "interesting_places",
        "format": "json",
        "limit": 20,  # Limit results
        "apikey": OPENTRIPMAP_API_KEY,
    }

    response = requests.get(url_places, params=params)

    if response.status_code != 200:
        print(f"❌ Failed to fetch places for {city}. Status Code: {response.status_code}")
        return []

    places = response.json()

    # Filter out places with no names
    places = [p for p in places if "name" in p and p["name"].strip()]

    print(f"✅ Found {len(places)} places in {city}.")  # Debugging
    return places


### **2. Generate Descriptions with Hugging Face Inference API**
def generate_description_with_huggingface(place_name, city):
    """Generates a short description using Hugging Face's free Inference API."""
    url = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b"


    headers = {"Content-Type": "application/json"}  # No API key required

    prompt = f"Write a short 3-4 sentence description of {place_name}, a famous tourist attraction in {city}. Focus on why it's interesting."

    data = {"inputs": prompt, "parameters": {"max_length": 200}}

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()[0]["generated_text"].strip()
    else:
        print(f"❌ Hugging Face API error: {response.status_code}, {response.text}")
        return "Description not available."


### **3. Process & Fetch Places**
def fetch_tourist_places(city):
    """Fetches top 20 high-rated places and uses Hugging Face to generate descriptions."""
    places_data = fetch_places_opentripmap(city)

    final_places = []
    for place in places_data:
        place_name = place.get("name", "Unknown Place")

        # Generate description using Hugging Face
        description = generate_description_with_huggingface(place_name, city)

        place_info = {
            "city": city,
            "name": place_name,
            "description": description,
            "category": place.get("kinds", "").split(",")[0],
            "price": "Free" if place.get("rate", 0) in [0, 1] else "Paid",
            "latitude": place.get("point", {}).get("lat"),
            "longitude": place.get("point", {}).get("lon"),
            "rating": place.get("rate", 0),
        }
        final_places.append(place_info)

    return final_places


### **4. Run the Pipeline and Print Results**
def run_pipeline():
    """Runs the entire data pipeline for fetching and processing places."""
    for city in CITIES:
        print(f"\n🔍 Fetching activities for {city}...")
        places_data = fetch_tourist_places(city)

        if places_data:
            print(f"\n🎉 Found {len(places_data)} places for {city}. Here are the top 5:\n")
            for place in places_data[:5]:
                print(f"🏛 {place['name']}")
                print(f"   ⭐ Rating: {place['rating']}")
                print(f"   📖 Description: {place['description'][:200]}...")  # Limit text preview
                print("-" * 60)
        else:
            print(f"❌ No tourist places found for {city}.")


if __name__ == "__main__":
    run_pipeline()

