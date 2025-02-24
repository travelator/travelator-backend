from pydantic import BaseModel
from typing import List


class ActivityRequest(BaseModel):
    city: str
    timeOfDay: List[str]
    group: str


class ItineraryRequest(BaseModel):
    city: str
