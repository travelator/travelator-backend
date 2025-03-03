from fastapi import APIRouter, Response
from .request_models import ActivityRequest
from generation.generation import Generator
from generation.image_searcher import get_n_random_places
import asyncio
import json
from datetime import timedelta

router = APIRouter()
generator = Generator()


@router.post("/activities")
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
