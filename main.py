import uvicorn
from fastapi import FastAPI, Response, Cookie
from generation import Generator
from request_models import ActivityRequest, ItineraryRequest
from fastapi.middleware.cors import CORSMiddleware
from image_searcher import get_n_random_places
from datetime import timedelta
import json
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

app = FastAPI()
generator = Generator()
environment = os.getenv("environment", "dev")

# Allow CORS for the React app's origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "https://voya-trips.com",
        "https://www.voya-trips.com",
        os.getenv("DATABASE_API_URL"),
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)


@app.post("/activities")
async def get_activities(request: ActivityRequest, response: Response):
    # Unpack request parameters
    city = request.city
    timeOfDay = request.timeOfDay
    group = request.group
    uni = request.uniqueness

    # get user preferences for setting cookie
    userPreferences = json.dumps(request.model_dump())

    # set cookie with parameters
    response.set_cookie(
        key="searchConfig",  # Cookie name
        value=userPreferences,  # JSON string value
        max_age=timedelta(days=1),  # Cookie expiration
        httponly=False,  # Prevent JS access
        secure=True,
        samesite="None",
    )

    # Activity titles is a list of string representing different activity titles
    activity_titles = await generator.generate_activities(
        city, titles_only=True, timeOfDay=timeOfDay, group=group, uniqueness=uni
    )
    titles_dict = {item["id"]: item["title"] for item in activity_titles}

    activity_response, image_dict = await asyncio.gather(
        generator.generate_activities(
            city,
            titles=activity_titles,
            timeOfDay=timeOfDay,
            group=group,
            uniqueness=uni,
        ),
        get_n_random_places(titles_dict),
    )

    # update images in response
    for item in activity_response:
        item["image_link"] = image_dict.get(item["id"], [])

    return {"activities": activity_response}


@app.post("/itinerary")
async def get_itinerary(request: ItineraryRequest, searchConfig: str = Cookie(None)):
    # Unpack request parameters
    city = request.city
    preferences = request.preferences
    itinerary = request.itinerary
    feedback = request.feedback

    # Look for cookie data on search parameters
    try:
        cookie_data = json.loads(searchConfig)
    except:
        cookie_data = {}

    timeOfDay = cookie_data.get("timeOfDay", None)
    group = cookie_data.get("group", None)
    uni = cookie_data.get("uniqueness", None)

    # Get itinerary response and titles
    itinerary_response = generator.generate_itinerary(
        city,
        timeOfDay,
        group,
        preferences=preferences,
        uniqueness=uni,
        prior_itinerary=itinerary,
        feedback=feedback,
    )
    titles_dict = {item.id: item.imageTag for item in itinerary_response.itinerary}

    # Get itinerary details and images
    detailed_itinerary, image_dict = await asyncio.gather(
        generator.generate_itinerary_details(itinerary_response, city, group),
        get_n_random_places(titles_dict),  # This will run concurrently
    )

    # update images in response
    for item in detailed_itinerary:
        item["image_link"] = image_dict.get(item["id"], [])

    # ensure item sorted by start
    detailed_itinerary.sort(key=lambda item: item["start"])

    return {"itinerary": detailed_itinerary}


@app.get("/facts")
async def get_facts(location: str, num: int):
    # Get facts for the location
    facts = await generator.generate_facts(location, num)

    return {"facts": facts}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
