from fastapi import APIRouter, Cookie
from .request_models import ItineraryRequest
from generation.generation import Generator
from generation.image_searcher import get_n_random_places
from generation.activity_links import get_activity_links
from generation.utils import weather_to_str
import asyncio
import json

router = APIRouter()
generator = Generator()


@router.post("/itinerary")
async def get_itinerary(request: ItineraryRequest, searchConfig: str = Cookie(None)):
    # Unpack request parameters
    city = request.city
    preferences = request.preferences
    itinerary = request.itinerary
    feedback = request.feedback

    # Look for cookie data on search parameters
    try:
        cookie_data = json.loads(searchConfig)
    except Exception:
        cookie_data = {}

    timeOfDay = cookie_data.get("timeOfDay", None)
    group = cookie_data.get("group", None)
    uni = cookie_data.get("uniqueness", None)
    date = cookie_data.get("date", None)

    # Get weather before generating itinerary
    weather = weather_to_str(generator.get_weather(city, date))

    # Get itinerary response and titles
    itinerary_response = generator.generate_itinerary(
        city,
        timeOfDay,
        group,
        preferences=preferences,
        uniqueness=uni,
        prior_itinerary=itinerary,
        feedback=feedback,
        weather=weather,
    )
    titles_dict = {item.id: item.imageTag for item in itinerary_response.itinerary}

    # Get itinerary details and images
    detailed_itinerary, image_dict, activity_links = await asyncio.gather(
        generator.generate_itinerary_details(itinerary_response, city, group, weather),
        get_n_random_places(titles_dict),  # This will run concurrently
        get_activity_links(titles_dict, city),
    )

    # update images in response
    for item in detailed_itinerary:
        item["image_link"] = image_dict.get(item["id"], [])
        if activity_links is not None:
            item["booking_url"] = activity_links.get(item["id"], None)
        else:
            item["booking_url"] = None

    # ensure item sorted by start
    return {"itinerary": detailed_itinerary}
