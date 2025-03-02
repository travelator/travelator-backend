import folium
import requests
import os
import webbrowser
import polyline
from folium import LayerControl

GOOGLE_MAPS_API_KEY = "AIzaSyB0DWNypHqqZoKOuNzuLDo39Tm22zJzMg8"  # Replace with your key
# 🚖 Taxi Fare Estimates for Different Cities
TAXI_FARES = {
    "New York City": {"base_fare": 3.00, "per_km": 1.50},
    "London": {"base_fare": 3.20, "per_km": 2.00},
    "San Francisco": {"base_fare": 3.50, "per_km": 2.25},
}

# 🎟️ Public Transport Fares
PUBLIC_TRANSIT_FARES = {
    "New York City": {"bus": 2.75, "subway": 2.75},
    "London": {"bus": 1.75, "subway": 2.40},
    "San Francisco": {"bus": 3.00, "subway": 3.50},
}


# 🚗 Fetch Google Directions and Extract Bus/Subway Data
def get_google_directions(origin, destination, mode="transit"):
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{origin[0]},{origin[1]}",
        "destination": f"{destination[0]},{destination[1]}",
        "mode": mode,
        "departure_time": "now",
        "key": GOOGLE_MAPS_API_KEY,
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data.get("status") != "OK":
        return None

    routes = []
    for route in data["routes"]:
        legs = route["legs"][0]
        polyline_data = route["overview_polyline"]["points"]
        decoded_polyline = polyline.decode(polyline_data)
        duration = legs["duration"]["text"]
        distance_km = legs["distance"]["value"] / 1000  # Convert meters to km

        # 🛠 **Fix: Check if 'summary' exists, otherwise use "Multiple Roads"**
        summary = route.get("summary", "Multiple Roads")

        # Extract transit details (bus/subway info)
        transit_steps = []
        for step in legs["steps"]:
            if "transit_details" in step:
                line_name = step["transit_details"]["line"]["short_name"]
                transit_type = step["transit_details"]["line"]["vehicle"]["type"]
                departure_time = step["transit_details"]["departure_time"]["text"]

                transit_steps.append(
                    {
                        "line": line_name,
                        "type": transit_type,
                        "departure": departure_time,
                    }
                )

        routes.append(
            {
                "polyline": decoded_polyline,
                "duration": duration,
                "summary": summary,  # ✅ Now always exists
                "distance_km": distance_km,
                "transit_steps": transit_steps,
            }
        )

    return routes


# 🚖 Calculate Taxi Fare
def calculate_taxi_fare(city, distance_km):
    rates = TAXI_FARES.get(city, {"base_fare": 3.00, "per_km": 1.50})
    return round(rates["base_fare"] + (rates["per_km"] * distance_km), 2)


# 🎯 Create Map with Styled Popups
def create_itinerary_map(city, itinerary):
    if not itinerary:
        return None

    start_location = itinerary[0].get("location")
    if not start_location:
        return None

    itinerary_map = folium.Map(location=start_location, zoom_start=13)

    # **Route Layers Per Mode + Segment**
    route_layers = {}

    for i in range(len(itinerary) - 1):
        start = itinerary[i]
        end = itinerary[i + 1]

        for mode, color in [
            ("driving", "red"),
            ("transit", "blue"),
            ("walking", "green"),
        ]:
            route_data = get_google_directions(start["location"], end["location"], mode)
            if route_data:
                route = route_data[0]
                layer_name = f"{mode.capitalize()} | {start['name']} → {end['name']}"

                if layer_name not in route_layers:
                    route_layers[layer_name] = folium.FeatureGroup(
                        name=layer_name, overlay=True
                    )

                folium.PolyLine(route["polyline"], color=color, weight=3.5).add_to(
                    route_layers[layer_name]
                )

                # **Styled Popup**
                popup_info = f"""
                <div style="width: 250px; font-size: 14px;">
                    <b style="font-size: 16px;">{mode.capitalize()} Route</b>
                    <br>🕒 <b>Duration:</b> {route['duration']}
                    <br>📍 <b>Route:</b> {route['summary']}
                """

                if mode == "transit":
                    popup_info += f"""
                    <br><br><b>💰 Fares:</b>
                    <table style="width: 100%; font-size: 14px;">
                        <tr><td>Subway:</td><td>${PUBLIC_TRANSIT_FARES[city]['subway']}</td></tr>
                        <tr><td>Bus:</td><td>${PUBLIC_TRANSIT_FARES[city]['bus']}</td></tr>
                    </table>
                    """

                    for step in route["transit_steps"]:
                        transit_icon = (
                            "🚍 Bus" if step["type"] == "BUS" else "🚇 Subway"
                        )
                        popup_info += f"""
                        <br>{transit_icon}: <b>{step['line']}</b>
                        (Departs at {step['departure']})
                        """

                elif mode == "driving":
                    taxi_fare = calculate_taxi_fare(city, route["distance_km"])
                    popup_info += f"<br>🚖 <b>Estimated Taxi Fare:</b> ${taxi_fare}"

                popup_info += "</div>"

                folium.Marker(
                    route["polyline"][len(route["polyline"]) // 2],
                    popup=folium.Popup(popup_info, max_width=300),
                    icon=folium.Icon(color=color, icon="info-sign"),
                ).add_to(route_layers[layer_name])

    for layer in route_layers.values():
        layer.add_to(itinerary_map)

    LayerControl(collapsed=False).add_to(itinerary_map)

    return itinerary_map


# 🚀 Main Function
def main():
    city = "New York City"
    itinerary = [
        {"name": "Empire State Building", "location": [40.748817, -73.985428]},
        {"name": "Times Square", "location": [40.758896, -73.985130]},
        {"name": "Brooklyn Bridge", "location": [40.706086, -73.996864]},
        {"name": "Statue of Liberty", "location": [40.689247, -74.044502]},
    ]

    itinerary_map = create_itinerary_map(city, itinerary)
    if itinerary_map:
        map_filename = "styled_popup_map.html"
        itinerary_map.save(map_filename)
        webbrowser.open(f"file://{os.path.abspath(map_filename)}")


if __name__ == "__main__":
    main()
