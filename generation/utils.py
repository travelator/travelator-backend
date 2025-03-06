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


def weather_to_str(weather) -> str:
    if weather is None:
        return None
    return " ".join(
        f"{entry['time']}: {entry['weather'].strip()} {entry['temperature']}°C"
        for entry in weather
    )
