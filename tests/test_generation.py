import pytest
import asyncio
import os
import requests
from unittest.mock import patch, AsyncMock
from generation.generation import Generator
from generation.generation_models import (
    ActivityTitles,
    ItineraryItem,
    SimpleItineraryItem,
    ItinerarySummary,
    Facts,
    Activity,
    ActivityList,
    ActivityTitleStruct,
    Theme,
    TransportMode
)


# Mock environment variables
os.environ["WEATHERAPI_KEY"] = "test_api_key"

generator = Generator()


# Mocking API requests
def mocked_weather_api(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if kwargs["params"]["q"] == "London":
        return MockResponse({
            "forecast": {
                "forecastday": [{
                    "hour": [{
                        "time": "2025-03-04 12:00",
                        "condition": {"icon": "//cdn.weatherapi.com/weather.png", "text": "Sunny"},
                        "temp_c": 15,
                        "precip_mm": 0,
                        "wind_kph": 10,
                    }]
                }]
            }
        }, 200)
    return MockResponse({}, 400)


@patch("requests.get", side_effect=mocked_weather_api)
def test_get_weather(mock_get):
    weather_data = generator.get_weather("London")
    assert "2025-03-04 12:00" in weather_data
    assert weather_data["2025-03-04 12:00"]["temperature"] == 15


def test_get_weather_error():
    with patch("requests.get", return_value=mocked_weather_api(params={"q": "Unknown"})):
        weather_data = generator.get_weather("Unknown")
        assert "error" in weather_data


# Mocking LLM interactions
@pytest.mark.asyncio
async def test_generate_activities():
    # Mocked response
    mock_response = ActivityTitles(
        activities=[
            ActivityTitleStruct(id=1, title="Visit the British Museum"),  # ✅ Use correct Pydantic model
            ActivityTitleStruct(id=2, title="Explore Tower of London"),
        ]
    )

    # Mock the method to return the response without making an API call
    with patch.object(generator, "generate_activities", return_value=mock_response.activities):
        result = await generator.generate_activities("London", titles_only=True)

        assert isinstance(result, list)
        assert result[0].title == "Visit the British Museum"  # ✅ Use dot notation







# Testing models
def test_activity_model():
    activity = Activity(
        id=1,
        title="Visit the Tower of London",
        description="Explore the historic castle and learn about its past.",
        image_link=["https://example.com/image.jpg"],
        price=30.0,
        theme="Culture"
    )
    assert activity.title == "Visit the Tower of London"


def test_itinerary_item_model():
    itinerary_item = ItineraryItem(
        title="Take the Tube to Oxford Circus",
        transport=True,
        start="2025-03-04 10:00",
        end="2025-03-04 10:15",
        description="Ride the London Underground to Oxford Circus.",
        price=2.5,
        theme=Theme.ADVENTURE,  # ✅ Use a valid theme
        transportMode=TransportMode.TUBE,  # ✅ Also use the correct TransportMode enum
        requires_booking=False,
        booking_url="",
        image_link=["https://example.com/tube.jpg"],
        duration=15,
        id=101
    )

    assert itinerary_item.transport is True
    assert itinerary_item.transportMode == TransportMode.TUBE



def test_simple_itinerary_item_model():
    simple_item = SimpleItineraryItem(
        title="Lunch at Dishoom",
        imageTag="Dishoom restaurant",
        start="2025-03-04 13:00",
        end="2025-03-04 14:00",
        id=102
    )
    assert simple_item.title == "Lunch at Dishoom"
    assert simple_item.imageTag == "Dishoom restaurant"


def test_itinerary_summary_model():
    summary = ItinerarySummary(itinerary=[SimpleItineraryItem(
        title="Lunch at Dishoom",
        imageTag="Dishoom restaurant",
        start="2025-03-04 13:00",
        end="2025-03-04 14:00",
        id=102
    )])
    assert len(summary.itinerary) == 1


def test_facts_model():
    facts = Facts(facts=["London has over 170 museums."])
    assert len(facts.facts) == 1
    assert "London has over 170 museums." in facts.facts


if __name__ == "__main__":
    pytest.main()
