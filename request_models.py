from pydantic import BaseModel
from typing import List
from generation_models import FullItinerary


class ActivityRequest(BaseModel):
    city: str
    timeOfDay: List[str]
    group: str
    uniqueness: int


class Preferences(BaseModel):
    liked: List[str]
    disliked: List[str]


class ItineraryRequest(BaseModel):
    city: str
    preferences: Preferences = None
    itinerary: FullItinerary = None
    feedback: str = None
