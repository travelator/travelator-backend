import folium
from folium import plugins
import os
import webbrowser


def create_itinerary_map(city, itinerary):
    """
    Creates a map with markers for each activity and lines connecting them in order.
    """
    if not itinerary:
        print("No itinerary data provided.")
        return None

    # Get the first activity's location as a starting point
    start_location = itinerary[0].get("location", None)
    if not start_location:
        print(" No location data available.")
        return None

    # Initialize the map centered on the first activity
    itinerary_map = folium.Map(location=start_location, zoom_start=13)

    coordinates = []  # To store activity locations for route plotting

    for activity in itinerary:
        name = activity.get("name", "Unknown Activity")
        description = activity.get("description", "No description available.")
        location = activity.get("location", None)

        if location:
            coordinates.append(location)
            folium.Marker(
                location=location,
                popup=f"<b>{name}</b><br>{description}",
                tooltip=name,
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(itinerary_map)

    # Draw lines connecting the activities in order
    if len(coordinates) > 1:
        folium.PolyLine(coordinates, color="blue", weight=2.5, opacity=0.8).add_to(itinerary_map)

    # Add layer controls and zoom capability
    plugins.Fullscreen().add_to(itinerary_map)
    plugins.LocateControl().add_to(itinerary_map)

    return itinerary_map


# Example usage with fake test data
def main():
    city = "Test City"
    itinerary = [
        {"name": "Central Park", "description": "A large urban park with scenic spots.",
         "location": [40.785091, -73.968285]},
        {"name": "Empire State Building", "description": "Iconic skyscraper with panoramic views.",
         "location": [40.748817, -73.985428]},
        {"name": "Times Square", "description": "Lively commercial and entertainment hub.",
         "location": [40.758896, -73.985130]},
        {"name": "Brooklyn Bridge", "description": "Famous suspension bridge connecting Manhattan and Brooklyn.",
         "location": [40.706086, -73.996864]},
        {"name": "Statue of Liberty", "description": "Symbol of freedom and democracy.",
         "location": [40.689247, -74.044502]}
    ]

    itinerary_map = create_itinerary_map(city, itinerary)
    if itinerary_map:
        map_filename = "test_itinerary_map.html"
        itinerary_map.save(map_filename)
        print(f"✅ Test itinerary map saved as '{map_filename}'")
        file_path = os.path.abspath(map_filename)
        webbrowser.open(f"file://{file_path}")


if __name__ == "__main__":
    main()
