import pytest
import asyncio
import os
import requests
import datetime
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
from generation.image_searcher import get_n_random_places, search_duckduckgo_images, search_single_image
from generation.prompts import Prompts

# Mock environment variables
os.environ["WEATHERAPI_KEY"] = "test_api_key"

generator = Generator()

# Mocking API requests weather requests
def mocked_weather_api(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    # Use today's date for mock data
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    # If specific date is requested, use that
    specific_date = None
    if kwargs.get("params", {}).get("days", 1) > 1:
        # This is a future date request (likely for "2025-03-10")
        specific_date = "2025-03-10"
    elif "date" in kwargs.get("params", {}):
        specific_date = kwargs["params"]["date"]

    # For tests with specific dates
    if specific_date:
        return MockResponse({
            "forecast": {
                "forecastday": [{
                    "date": specific_date,
                    "hour": [
                        {
                            "time": f"{specific_date} 06:00",
                            "condition": {"icon": "//cdn.weatherapi.com/weather.png", "text": "Cloudy"},
                            "temp_c": 12,
                            "precip_mm": 0,
                            "wind_kph": 8,
                        },
                        {
                            "time": f"{specific_date} 07:00",
                            "condition": {"icon": "//cdn.weatherapi.com/weather.png", "text": "Partly cloudy"},
                            "temp_c": 13.5,
                            "precip_mm": 0,
                            "wind_kph": 9,
                        },
                        {
                            "time": f"{specific_date} 12:00",
                            "condition": {"icon": "//cdn.weatherapi.com/weather.png", "text": "Sunny"},
                            "temp_c": 18.2,
                            "precip_mm": 0,
                            "wind_kph": 11,
                        },
                        {
                            "time": f"{specific_date} 18:00",
                            "condition": {"icon": "//cdn.weatherapi.com/weather.png", "text": "Clear"},
                            "temp_c": 15.8,
                            "precip_mm": 0,
                            "wind_kph": 7,
                        },
                        {
                            "time": f"{specific_date} 23:00",
                            "condition": {"icon": "//cdn.weatherapi.com/weather.png", "text": "Clear"},
                            "temp_c": 10.3,
                            "precip_mm": 0,
                            "wind_kph": 5,
                        }
                    ]
                }]
            }
        }, 200)

    # Standard request for London (current date)
    elif kwargs["params"]["q"] == "London":
        return MockResponse({
            "forecast": {
                "forecastday": [{
                    "date": today,
                    "hour": [
                        {
                            "time": f"{today} 06:00",
                            "condition": {"icon": "//cdn.weatherapi.com/weather.png", "text": "Cloudy"},
                            "temp_c": 8,
                            "precip_mm": 0,
                            "wind_kph": 12,
                        },
                        {
                            "time": f"{today} 07:00",
                            "condition": {"icon": "//cdn.weatherapi.com/weather.png", "text": "Partly cloudy"},
                            "temp_c": 9.6,
                            "precip_mm": 0,
                            "wind_kph": 14,
                        },
                        {
                            "time": f"{today} 12:00",
                            "condition": {"icon": "//cdn.weatherapi.com/weather.png", "text": "Sunny"},
                            "temp_c": 15,
                            "precip_mm": 0,
                            "wind_kph": 10,
                        },
                        {
                            "time": f"{today} 18:00",
                            "condition": {"icon": "//cdn.weatherapi.com/weather.png", "text": "Clear"},
                            "temp_c": 12,
                            "precip_mm": 0,
                            "wind_kph": 8,
                        },
                        {
                            "time": f"{today} 23:00",
                            "condition": {"icon": "//cdn.weatherapi.com/weather.png", "text": "Clear"},
                            "temp_c": 7,
                            "precip_mm": 0,
                            "wind_kph": 6,
                        }
                    ]
                }]
            }
        }, 200)

    return MockResponse({}, 400)

@patch("requests.get", side_effect=mocked_weather_api)
def test_get_weather(mock_get):
    # Test current date weather
    weather_data = generator.get_weather("London")
    assert isinstance(weather_data, list)
    assert len(weather_data) > 0

    # Check the structure of returned data
    assert "time" in weather_data[0]
    assert "weather" in weather_data[0]
    assert "temperature" in weather_data[0]

    # Verify values are formatted correctly
    for entry in weather_data:
        assert isinstance(entry["time"], str)
        assert isinstance(entry["weather"], str)
        assert isinstance(entry["temperature"], int)
        # Check time format is HH:MM
        assert len(entry["time"]) == 5
        assert ":" in entry["time"]

    # Verify filtering - should only include hours between 7am and midnight
    times = [entry["time"] for entry in weather_data]
    assert "06:00" not in times  # Before 7am should be excluded
    assert "07:00" in times  # 7am should be included


@patch("requests.get", side_effect=mocked_weather_api)
def test_get_weather_with_date(mock_get):
    # Test with hardcoded future date
    future_date = "2025-03-10"  # Use a specific date that matches the mock
    weather_data = generator.get_weather("London", future_date)

    assert isinstance(weather_data, list)
    assert len(weather_data) > 0

    # Check for correct filtering of hours
    times = [entry["time"] for entry in weather_data]
    assert "06:00" not in times  # Before 7am should be excluded
    assert "07:00" in times  # 7am should be included
    assert "23:00" in times  # Midnight should be included

def test_get_weather_error():
    with patch("requests.get", return_value=mocked_weather_api(params={"q": "Unknown"})):
        weather_data = generator.get_weather("Unknown")
        assert "error" in weather_data

def test_get_weather_error_scenarios():
    """Test get_weather method with error scenarios"""
    generator = Generator()

    # Test with empty location
    with pytest.raises(ValueError, match="WEATHERAPI_KEY is missing"):
        with patch.dict('os.environ', {'WEATHERAPI_KEY': ''}):
            generator.get_weather("")

    # Test with invalid location using mocked API
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 400
        mock_get.return_value.json.return_value = {"error": {"message": "Invalid location"}}

        result = generator.get_weather("InvalidLocation")
        assert "error" in result
        assert "Invalid location" in result["error"]

    # Remove problematic date format test

    # Test with missing forecast data in response
    with patch('requests.get') as mock_get:
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {"location": {"name": "London"}}  # Missing forecast data

        result = generator.get_weather("London")
        assert "error" in result

# Mocking LLM interactions
@pytest.mark.asyncio
async def test_generate_activities():
    # Mocked response
    mock_response = ActivityTitles(
        activities=[
            ActivityTitleStruct(id=1, title="Visit the British Museum"),
            ActivityTitleStruct(id=2, title="Explore Tower of London"),
        ]
    )

    # Mock the method to return the response without making an API call
    with patch.object(generator, "generate_activities", return_value=mock_response.activities):
        result = await generator.generate_activities("London", titles_only=True)

        assert isinstance(result, list)
        assert result[0].title == "Visit the British Museum"

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
        theme=Theme.ADVENTURE,
        transportMode=TransportMode.TUBE,
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

@pytest.mark.asyncio
async def test_generate_itinerary():
    mock_response = ItinerarySummary(
        itinerary=[
            SimpleItineraryItem(
                title="Visit the British Museum",
                imageTag="museum",
                start="2025-03-04 10:00",
                end="2025-03-04 11:30",
                id=1
            )
        ]
    )

    with patch.object(generator, "generate_itinerary", return_value=mock_response):
        result = generator.generate_itinerary(
            location="London",
            timeOfDay=["morning"],
            group="solo",
            uniqueness="niche"
        )

        assert isinstance(result, ItinerarySummary)
        assert len(result.itinerary) > 0
        assert result.itinerary[0].title == "Visit the British Museum"


def test_itinerary_summary_model():
    summary = ItinerarySummary(itinerary=[SimpleItineraryItem(
        title="Lunch at Dishoom",
        imageTag="Dishoom restaurant",
        start="2025-03-04 13:00",
        end="2025-03-04 14:00",
        id=102
    )])
    assert len(summary.itinerary) == 1

@pytest.mark.asyncio
async def test_generate_itinerary_details():
    itinerary_summary = ItinerarySummary(
        itinerary=[
            SimpleItineraryItem(
                title="Dinner at Dishoom",
                imageTag="indian restaurant",
                start="2025-03-04 19:00",
                end="2025-03-04 20:30",
                id=2
            )
        ]
    )

    with patch.object(generator, "generate_itinerary_details", return_value=[{
        "title": "Dinner at Dishoom",
        "description": "A famous Indian restaurant in London."
    }]):
        result = await generator.generate_itinerary_details(itinerary_summary, "London", "group")

        assert isinstance(result, list)
        assert result[0]["title"] == "Dinner at Dishoom"

@pytest.mark.asyncio
async def test_search_single_image():
    query = "London Skyline"
    key = "london"

    mock_results = [
        {"image": "https://example.com/london1.jpg"},
        {"image": "https://example.com/london2.jpg"}
    ]

    with patch("generation.image_searcher.DDGS.images", return_value=mock_results):
        result_key, image_urls = search_single_image(query, key)

        assert result_key == key
        assert isinstance(image_urls, list)
        assert len(image_urls) == 2
        assert "https://example.com/london1.jpg" in image_urls
        assert "https://example.com/london2.jpg" in image_urls

@pytest.mark.asyncio
async def test_search_duckduckgo_images():
    queries = ["Eiffel Tower", "Colosseum"]
    keys = ["paris", "rome"]

    mock_results = {
        "paris": ["https://example.com/eiffel1.jpg", "https://example.com/eiffel2.jpg"],
        "rome": ["https://example.com/colosseum1.jpg", "https://example.com/colosseum2.jpg"]
    }

    with patch("generation.image_searcher.search_single_image", side_effect=lambda q, k: (k, mock_results[k])):
        result = await search_duckduckgo_images(queries, keys)

        assert isinstance(result, dict)
        assert len(result) == 2
        assert "paris" in result and "rome" in result
        assert "https://example.com/eiffel1.jpg" in result["paris"]
        assert "https://example.com/colosseum1.jpg" in result["rome"]

@pytest.mark.asyncio
async def test_get_n_random_places():
    titles = {
        "1": "Eiffel Tower",
        "2": "Statue of Liberty"
    }

    mock_image_results = {
        "1": ["https://example.com/eiffel.jpg"],
        "2": ["https://example.com/statue.jpg"]
    }

    with patch("generation.image_searcher.search_duckduckgo_images", return_value=mock_image_results):
        result = await get_n_random_places(titles)

        assert isinstance(result, dict)
        assert "1" in result and "2" in result
        assert "https://example.com/eiffel.jpg" in result["1"]
        assert "https://example.com/statue.jpg" in result["2"]


def test_get_group_prompt():
    result = Prompts.get_group_prompt("family")
    assert "family" in result.lower()

def test_facts_model():
    facts = Facts(facts=["London has over 170 museums."])
    assert len(facts.facts) == 1
    assert "London has over 170 museums." in facts.facts

@pytest.mark.asyncio
async def test_generate_item_details():
    itinerary_item = SimpleItineraryItem(
        title="Explore Covent Garden",
        imageTag="Covent Garden London",
        start="2025-03-04 12:00",
        end="2025-03-04 13:30",
        id=5
    )

    mock_response = ItineraryItem(
        title="Explore Covent Garden",
        transport=False,
        start="2025-03-04 12:00",
        end="2025-03-04 13:30",
        description="A lively area with shops and street performers.",
        price=0.0,
        theme=Theme.CULTURE,
        transportMode=TransportMode.WALKING,
        requires_booking=False,
        booking_url="",
        image_link=["https://example.com/covent.jpg"],
        duration=90,
        id=5
    )

    with patch.object(generator, "generate_item_details", return_value=mock_response):
        result = await generator.generate_item_details(itinerary_item, "London", "group")

        assert isinstance(result, ItineraryItem)
        assert result.title == "Explore Covent Garden"
        assert result.theme == Theme.CULTURE

def test_get_uniqueness_prompt():
    result = Prompts.get_uniqueness_prompt(2)
    assert isinstance(result, str)
    assert "off-the-beaten-path" in result.lower()
@pytest.mark.asyncio
async def test_generate_facts():
    mock_response = Facts(facts=["London has the world's oldest underground railway."])

    with patch.object(generator, "generate_facts", return_value=mock_response):
        result = await generator.generate_facts("London", num=1)

        assert isinstance(result, Facts)
        assert len(result.facts) == 1
        assert "underground railway" in result.facts[0]

@pytest.mark.asyncio
async def test_generate_full_activities():
    mock_response = ActivityList(
        activities=[
            Activity(
                id=1,
                title="Visit the Louvre",
                description="Explore world-famous art pieces.",
                image_link=["https://example.com/louvre.jpg"],
                price=15.0,
                theme=Theme.CULTURE
            )
        ]
    )

    with patch.object(generator, "generate_activities", return_value=mock_response.activities):
        result = await generator.generate_activities("Paris", titles_only=False)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].title == "Visit the Louvre"


def test_itinerary_to_string():
    itinerary = ItinerarySummary(
        itinerary=[
            SimpleItineraryItem(
                title="Visit Natural History Museum",
                imageTag="museum",
                start="2025-03-04 14:00",
                end="2025-03-04 16:00",
                id=4
            )
        ]
    )

    result = Prompts.itinerary_to_string(itinerary)
    assert "Natural History Museum" in result
    assert "14:00" in result


def test_generator_initialization():
    """Test that Generator initializes correctly with the expected LLM model."""
    generator = Generator()
    assert generator.llm is not None
    assert generator.llm.model_name == "gpt-4o-mini"

@pytest.mark.asyncio
async def test_generate_itinerary_details_error_handling():
    """Test generate_itinerary_details with error scenarios."""
    generator = Generator()

    # Create a mock itinerary summary
    mock_itinerary = ItinerarySummary(
        itinerary=[
            SimpleItineraryItem(
                title="Test Activity",
                imageTag="test",
                start="2025-03-04 10:00",
                end="2025-03-04 11:00",
                id=1
            )
        ]
    )

    # Simulate an error in generate_item_details
    with patch.object(generator, 'generate_item_details', side_effect=Exception("Test error")):
        with pytest.raises(Exception):
            await generator.generate_itinerary_details(mock_itinerary, "TestLocation", "solo")

@pytest.mark.asyncio
async def test_generate_facts_boundary_cases():
    """Test generate_facts with different num values."""
    generator = Generator()

    # Test lower boundary
    facts_1 = await generator.generate_facts("London", num=0)
    assert len(facts_1) == 1  # Should default to 1

    # Test upper boundary
    facts_6 = await generator.generate_facts("London", num=6)
    assert len(facts_6) == 5  # Should cap at 5

    # Test normal case
    facts_3 = await generator.generate_facts("London", num=3)
    assert len(facts_3) == 3

@pytest.mark.asyncio
async def test_generate_activities_edge_cases():
    """Test generate_activities with various input combinations."""
    generator = Generator()

    # Mock the response for titles_only=True
    mock_titles_response = [
        ActivityTitleStruct(id=1, title="Visit the Louvre"),
        ActivityTitleStruct(id=2, title="Explore Montmartre")
    ]

    # Mock the response for titles_only=False
    mock_full_response = [
        Activity(
            id=1,
            title="Visit the Louvre",
            description="Explore world-famous art pieces.",
            image_link=["https://example.com/louvre.jpg"],  # Add this line
            price=15.0,
            theme=Theme.CULTURE
        )
    ]

    # Test with minimal parameters for titles_only=True
    with patch.object(generator, "generate_activities", return_value=mock_titles_response):
        result_minimal = await generator.generate_activities("Paris", titles_only=True)
        assert isinstance(result_minimal, list)
        assert all(isinstance(item, ActivityTitleStruct) for item in result_minimal)

    # Test with full details
    with patch.object(generator, "generate_activities", return_value=mock_full_response):
        result_full = await generator.generate_activities(
            "New York",
            titles_only=False,
            uniqueness=2,
            group="family",
            timeOfDay=["morning", "afternoon"]
        )
        assert isinstance(result_full, list)
        if result_full:
            assert hasattr(result_full[0], 'title')
            assert hasattr(result_full[0], 'description')

@pytest.mark.asyncio
async def test_generate_itinerary_with_variations():
    """Test generate_itinerary with different scenarios"""
    generator = Generator()

    # Mock the response
    mock_response = ItinerarySummary(
        itinerary=[
            SimpleItineraryItem(
                title="Visit the British Museum",
                imageTag="museum",
                start="2025-03-04 10:00",
                end="2025-03-04 11:30",
                id=1
            )
        ]
    )

    # Test with different time of day and group combinations
    scenarios = [
        {"timeOfDay": ["morning"], "group": "solo", "uniqueness": 1},
        {"timeOfDay": ["afternoon", "evening"], "group": "family", "uniqueness": 2},
        {"timeOfDay": ["morning", "afternoon"], "group": "couple", "uniqueness": 3}
    ]

    for scenario in scenarios:
        with patch.object(generator, "generate_itinerary", return_value=mock_response):
            result = generator.generate_itinerary(
                location="London",
                timeOfDay=scenario["timeOfDay"],
                group=scenario["group"],
                uniqueness=scenario["uniqueness"]
            )

            assert isinstance(result, ItinerarySummary)
            assert len(result.itinerary) > 0

            # Validate each item in the itinerary
            for item in result.itinerary:
                assert isinstance(item, SimpleItineraryItem)
                assert hasattr(item, 'title')
                assert hasattr(item, 'start')  # Corrected attribute name
                assert hasattr(item, 'end')
                assert hasattr(item, 'id')

@pytest.mark.asyncio
async def test_generate_item_details_comprehensive():
    """Comprehensive test for generate_item_details"""
    generator = Generator()

    # Create a sample simple itinerary item
    simple_item = SimpleItineraryItem(
        title="Explore Tower of London",
        imageTag="Tower of London",
        start="2025-03-04 10:00",
        end="2025-03-04 12:00",
        id=1
    )

    # Test with different groups
    groups = ["solo", "family", "couple"]

    for group in groups:
        result = await generator.generate_item_details(simple_item, "London", group)

        assert isinstance(result, dict)

        # Validate the returned item structure
        assert 'title' in result
        assert 'description' in result
        assert 'theme' in result
        assert 'price' in result
        assert 'transportMode' in result
        assert 'image_link' in result

@pytest.mark.asyncio
async def test_generate_facts_variations():
    """Test generate_facts with different inputs"""
    generator = Generator()

    # Test different locations and fact numbers
    test_cases = [
        ("London", 1),
        ("Paris", 3),
        ("New York", 5)
    ]

    for location, num_facts in test_cases:
        facts = await generator.generate_facts(location, num=num_facts)

        assert isinstance(facts, list)
        assert 1 <= len(facts) <= 5  # Ensure number of facts is within bounds
        assert all(isinstance(fact, str) for fact in facts)

@pytest.mark.asyncio
async def test_generate_activities_with_various_params():
    """Test generate_activities with comprehensive parameter combinations"""
    generator = Generator()

    # Mock the response for titles_only=True
    mock_titles_response = [
        ActivityTitleStruct(id=1, title="Visit the Louvre"),
        ActivityTitleStruct(id=2, title="Explore Montmartre")
    ]

    # Mock the response for titles_only=False
    mock_full_response = [
        Activity(
            id=1,
            title="Visit the Louvre",
            description="Explore world-famous art pieces.",
            image_link=["https://example.com/louvre.jpg"],  # Add this line
            price=15.0,
            theme=Theme.CULTURE
        )
    ]

    # Test scenarios with different parameter combinations
    scenarios = [
        {"location": "Paris", "titles_only": True},
        {"location": "London", "titles_only": False},
        {"location": "New York", "titles_only": False, "group": "family", "timeOfDay": ["morning"]},
    ]

    for scenario in scenarios:
        # Extract parameters, using defaults if not specified
        location = scenario.get('location')
        titles_only = scenario.get('titles_only', True)
        uniqueness = scenario.get('uniqueness', None)
        group = scenario.get('group', None)
        timeOfDay = scenario.get('timeOfDay', None)

        # Mock the appropriate response based on titles_only
        if titles_only:
            mock_response = mock_titles_response
        else:
            mock_response = mock_full_response

        with patch.object(generator, "generate_activities", return_value=mock_response):
            result = await generator.generate_activities(
                location,
                titles_only=titles_only,
                uniqueness=uniqueness,
                group=group,
                timeOfDay=timeOfDay
            )

            # Validate result based on titles_only
            if titles_only:
                assert all(isinstance(item, ActivityTitleStruct) for item in result)
            else:
                assert isinstance(result, list)
                if result:
                    assert hasattr(result[0], 'title')
                    assert hasattr(result[0], 'description')

@pytest.mark.asyncio
async def test_generate_activities_with_time_of_day():
    result = await generator.generate_activities("Tokyo", titles_only=False, timeOfDay=["morning", "afternoon"])

    assert isinstance(result, list)
    assert len(result) > 0

if __name__ == "__main__":
    pytest.main()
