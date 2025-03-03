from fastapi import APIRouter, Cookie
from .request_models import ItineraryRequest
from generation.generation import Generator
from generation.image_searcher import get_n_random_places
from generation.activity_links import get_activity_links
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
    detailed_itinerary, image_dict, activity_links = await asyncio.gather(
        generator.generate_itinerary_details(itinerary_response, city, group),
        get_n_random_places(titles_dict),  # This will run concurrently
        get_activity_links(titles_dict),
    )

    # update images in response
    for item in detailed_itinerary:
        item["image_link"] = image_dict.get(item["id"], [])
        item["booking_url"] = activity_links.get(item["id"], None)

    # ensure item sorted by start
    detailed_itinerary.sort(key=lambda item: item["start"])

    return {"itinerary": detailed_itinerary}
