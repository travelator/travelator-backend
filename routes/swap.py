from fastapi import APIRouter, Cookie
from .request_models import SwapRequest
from generation.generation import Generator
from generation.utils import get_activity_from_id, swap_activity
from generation.image_searcher import get_n_random_places
from generation.activity_links import get_activity_links
from generation.utils import weather_to_str
import json
import asyncio

router = APIRouter()
generator = Generator()


@router.post("/swap")
async def swap(request: SwapRequest, searchConfig: str = Cookie(None)):
    # Unpack request parameters
    city = request.city
    activityId = request.activityId
    itinerary = request.itinerary
    feedback = request.feedback

    # Look for cookie data on search parameters
    try:
        cookie_data = json.loads(searchConfig)
    except json.JSONDecodeError:
        cookie_data = {}

    group = cookie_data.get("group", None)
    uni = cookie_data.get("uniqueness", None)
    date = cookie_data.get("date", None)

    # get activity from itinerary
    activity = get_activity_from_id(itinerary, activityId)

    # Get weather before generating activity
    weather = weather_to_str(generator.get_weather(city, date))

    # get new activity
    new_activity = await generator.swap_activity(
        activity=activity,
        location=city,
        group=group,
        uniqueness=uni,
        itinerary=itinerary,
        feedback=feedback,
        weather=weather,
    )

    # get image for new activity
    title_dict = {new_activity.id: new_activity.title}
    image_link, booking_link = await asyncio.gather(
        get_n_random_places(title_dict), get_activity_links(title_dict, city)
    )

    # update image in response
    new_activity.image_link = image_link.get(new_activity.id, [])

    if booking_link is None:
        new_activity.booking_url = ""
    else:
        new_activity.booking_url = booking_link.get(new_activity.id, None)

    # replace old with new activity
    new_itinerary = swap_activity(itinerary, activityId, new_activity)
    json_response = new_itinerary.model_dump()["itinerary"]

    return {"itinerary": json_response}
