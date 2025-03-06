from .generation_models import FullItinerary, ItineraryItem


def get_activity_from_id(itinerary: FullItinerary, activityId: int) -> ItineraryItem:
    items = itinerary.itinerary

    for item in items:
        if item.id == activityId:
            return item

    return None


def swap_activity(
    itinerary: FullItinerary, replaceId: int, new_activity: ItineraryItem
) -> FullItinerary:
    items = itinerary.itinerary

    for i, item in enumerate(items):
        if item.id == replaceId:
            items[i] = new_activity
            break

    return itinerary
