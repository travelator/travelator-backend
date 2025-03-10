from pydantic import BaseModel
from typing import List, Optional
from generation.generation_models import FullItinerary


class ActivityRequest(BaseModel):
    city: str
    timeOfDay: List[str]
    group: str
    uniqueness: int
    date: Optional[str] = None


class Preferences(BaseModel):
    liked: List[str]
    disliked: List[str]


class ItineraryRequest(BaseModel):
    city: str
    preferences: Preferences = None
    itinerary: FullItinerary = None
    feedback: str = None


class SwapRequest(BaseModel):
    city: str
    activityId: int
    itinerary: FullItinerary
    feedback: str = None
