from pydantic import BaseModel
from typing import List


class ActivityRequest(BaseModel):
    city: str
    timeOfDay: List[str]
    group: str


class Preferences(BaseModel):
    liked: List[str]
    disliked: List[str]


class ItineraryRequest(BaseModel):
    city: str
    preferences: Preferences
