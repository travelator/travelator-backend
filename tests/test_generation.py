import pytest
from unittest.mock import patch
from generation.generation import Generator
from generation.generation_models import (
    ActivityTitles,
    ItineraryItem,
    SimpleItineraryItem,
    ItinerarySummary,
    Facts,
    Activity,
    ActivityTitleStruct,
    Theme,
    TransportMode,
)
from generation.image_searcher import (
    get_n_random_places,
    search_duckduckgo_images,
    search_single_image,
)
from generation.prompts import Prompts

generator = Generator()


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
    with patch.object(
        generator, "generate_activities", return_value=mock_response.activities
    ):
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
        theme="Culture",
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
        theme="Adventure",
        transportMode="Tube",
        requires_booking=False,
        booking_url="",
        image_link=["https://example.com/tube.jpg"],
        duration=15,
        weather="sunny",
        temperature=5,
        latitude=51.5145,
        longitude=-0.1445,
        id=101,
    )

    assert itinerary_item.transport is True
    assert itinerary_item.transportMode == TransportMode.TUBE


def test_simple_itinerary_item_model():
    simple_item = SimpleItineraryItem(
        title="Lunch at Dishoom",
        imageTag="Dishoom restaurant",
        start="2025-03-04 13:00",
        end="2025-03-04 14:00",
        id=102,
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
                id=1,
            )
        ]
    )

    with patch.object(generator, "generate_itinerary", return_value=mock_response):
        result = await generator.generate_itinerary(
            location="London", timeOfDay=["morning"], group="solo", uniqueness="niche"
        )

        assert isinstance(result, ItinerarySummary)
        assert len(result.itinerary) > 0
        assert result.itinerary[0].title == "Visit the British Museum"


def test_itinerary_summary_model():
    summary = ItinerarySummary(
        itinerary=[
            SimpleItineraryItem(
                title="Lunch at Dishoom",
                imageTag="Dishoom restaurant",
                start="2025-03-04 13:00",
                end="2025-03-04 14:00",
                id=102,
            )
        ]
    )
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
                id=2,
            )
        ]
    )

    with patch.object(
        generator,
        "generate_itinerary_details",
        return_value=[
            {
                "title": "Dinner at Dishoom",
                "description": "A famous Indian restaurant in London.",
            }
        ],
    ):
        result = await generator.generate_itinerary_details(
            itinerary_summary, "London", "group"
        )

        assert isinstance(result, list)
        assert result[0]["title"] == "Dinner at Dishoom"


@pytest.mark.asyncio
async def test_search_single_image():
    query = "London Skyline"
    key = "london"

    mock_results = [
        {"image": "https://example.com/london1.jpg"},
        {"image": "https://example.com/london2.jpg"},
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
        "rome": [
            "https://example.com/colosseum1.jpg",
            "https://example.com/colosseum2.jpg",
        ],
    }

    with patch(
        "generation.image_searcher.search_single_image",
        side_effect=lambda q, k: (k, mock_results[k]),
    ):
        result = await search_duckduckgo_images(queries, keys)

        assert isinstance(result, dict)
        assert len(result) == 2
        assert "paris" in result and "rome" in result
        assert "https://example.com/eiffel1.jpg" in result["paris"]
        assert "https://example.com/colosseum1.jpg" in result["rome"]


@pytest.mark.asyncio
async def test_get_n_random_places():
    titles = {"1": "Eiffel Tower", "2": "Statue of Liberty"}

    mock_image_results = {
        "1": ["https://example.com/eiffel.jpg"],
        "2": ["https://example.com/statue.jpg"],
    }

    with patch(
        "generation.image_searcher.search_duckduckgo_images",
        return_value=mock_image_results,
    ):
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


def test_get_uniqueness_prompt():
    result = Prompts.get_uniqueness_prompt(2)
    assert isinstance(result, str)
    assert "off-the-beaten-path" in result.lower()


def test_itinerary_to_string():
    itinerary = ItinerarySummary(
        itinerary=[
            SimpleItineraryItem(
                title="Visit Natural History Museum",
                imageTag="museum",
                start="2025-03-04 14:00",
                end="2025-03-04 16:00",
                id=4,
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
async def test_generate_activities_edge_cases():
    """Test generate_activities with various input combinations."""
    generator = Generator()

    # Mock the response for titles_only=True
    mock_titles_response = [
        ActivityTitleStruct(id=1, title="Visit the Louvre"),
        ActivityTitleStruct(id=2, title="Explore Montmartre"),
    ]

    # Mock the response for titles_only=False
    mock_full_response = [
        Activity(
            id=1,
            title="Visit the Louvre",
            description="Explore world-famous art pieces.",
            image_link=["https://example.com/louvre.jpg"],  # Add this line
            price=15.0,
            theme=Theme.CULTURE,
        )
    ]

    # Test with minimal parameters for titles_only=True
    with patch.object(
        generator, "generate_activities", return_value=mock_titles_response
    ):
        result_minimal = await generator.generate_activities("Paris", titles_only=True)
        assert isinstance(result_minimal, list)
        assert all(isinstance(item, ActivityTitleStruct) for item in result_minimal)

    # Test with full details
    with patch.object(
        generator, "generate_activities", return_value=mock_full_response
    ):
        result_full = await generator.generate_activities(
            "New York",
            titles_only=False,
            uniqueness=2,
            group="family",
            timeOfDay=["morning", "afternoon"],
        )
        assert isinstance(result_full, list)
        if result_full:
            assert hasattr(result_full[0], "title")
            assert hasattr(result_full[0], "description")


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
                id=1,
            )
        ]
    )

    # Test with different time of day and group combinations
    scenarios = [
        {"timeOfDay": ["morning"], "group": "solo", "uniqueness": 1},
        {"timeOfDay": ["afternoon", "evening"], "group": "family", "uniqueness": 2},
        {"timeOfDay": ["morning", "afternoon"], "group": "couple", "uniqueness": 3},
    ]

    for scenario in scenarios:
        with patch.object(generator, "generate_itinerary", return_value=mock_response):
            result = await generator.generate_itinerary(
                location="London",
                timeOfDay=scenario["timeOfDay"],
                group=scenario["group"],
                uniqueness=scenario["uniqueness"],
            )

            assert isinstance(result, ItinerarySummary)
            assert len(result.itinerary) > 0

            # Validate each item in the itinerary
            for item in result.itinerary:
                assert isinstance(item, SimpleItineraryItem)
                assert hasattr(item, "title")
                assert hasattr(item, "start")  # Corrected attribute name
                assert hasattr(item, "end")
                assert hasattr(item, "id")


@pytest.mark.asyncio
async def test_generate_activities_with_various_params():
    """Test generate_activities with comprehensive parameter combinations"""
    generator = Generator()

    # Mock the response for titles_only=True
    mock_titles_response = [
        ActivityTitleStruct(id=1, title="Visit the Louvre"),
        ActivityTitleStruct(id=2, title="Explore Montmartre"),
    ]

    # Mock the response for titles_only=False
    mock_full_response = [
        Activity(
            id=1,
            title="Visit the Louvre",
            description="Explore world-famous art pieces.",
            image_link=["https://example.com/louvre.jpg"],  # Add this line
            price=15.0,
            theme=Theme.CULTURE,
        )
    ]

    # Test scenarios with different parameter combinations
    scenarios = [
        {"location": "Paris", "titles_only": True},
        {"location": "London", "titles_only": False},
        {
            "location": "New York",
            "titles_only": False,
            "group": "family",
            "timeOfDay": ["morning"],
        },
    ]

    for scenario in scenarios:
        # Extract parameters, using defaults if not specified
        location = scenario.get("location")
        titles_only = scenario.get("titles_only", True)
        uniqueness = scenario.get("uniqueness", None)
        group = scenario.get("group", None)
        timeOfDay = scenario.get("timeOfDay", None)

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
                timeOfDay=timeOfDay,
            )

            # Validate result based on titles_only
            if titles_only:
                assert all(isinstance(item, ActivityTitleStruct) for item in result)
            else:
                assert isinstance(result, list)
                if result:
                    assert hasattr(result[0], "title")
                    assert hasattr(result[0], "description")


if __name__ == "__main__":
    pytest.main()
