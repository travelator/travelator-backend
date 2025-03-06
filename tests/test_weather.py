import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import os
from generation.generation import Generator


# Set up the mock API key in environment variables
@pytest.fixture(autouse=True)
def set_up_environment():
    os.environ["WEATHER_API_KEY"] = "mock_api_key"
    yield
    del os.environ["WEATHER_API_KEY"]


# Helper function to get a date 14 days from now
def get_future_date(days_ahead):
    return (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")


# Test when no weather data is returned (invalid API response)
@patch("requests.get")
def test_get_weather_no_data(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {}

    generator = Generator()
    result = generator.get_weather("London", get_future_date(1))  # 1 day from now
    assert result is None, "Expected None when no forecast data is returned"


# Test for invalid weather API key
@patch("requests.get")
def test_get_weather_invalid_api_key(mock_get):
    os.environ["WEATHER_API_KEY"] = "abc"  # No API key

    generator = Generator()
    result = generator.get_weather("London", get_future_date(1))
    assert result is None, "Expected None when no API key is provided"


# Test for successful weather data retrieval
@patch("requests.get")
def test_get_weather_success(mock_get):
    # Mocking a valid response from the Weather API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "forecast": {
            "forecastday": [
                {
                    "date": get_future_date(1),  # 1 day from now
                    "hour": [
                        {
                            "time": f"{get_future_date(1)} 07:00",
                            "condition": {"text": "Clear"},
                            "temp_c": 22,
                        },
                        {
                            "time": f"{get_future_date(1)} 08:00",
                            "condition": {"text": "Sunny"},
                            "temp_c": 24,
                        },
                        # More hourly data can be added here...
                    ],
                }
            ]
        }
    }
    mock_get.return_value = mock_response

    generator = Generator()
    result = generator.get_weather("London", get_future_date(1))  # 1 day from now

    # Check the expected structure of the result
    assert isinstance(result, list)
    assert len(result) > 0
    assert result[0]["time"] == "07:00"
    assert result[0]["weather"] == "Clear"
    assert result[0]["temperature"] == 22


# Test for weather data beyond 14 days (should return None)
@patch("requests.get")
def test_get_weather_out_of_range(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {}

    generator = Generator()
    result = generator.get_weather("London", get_future_date(15))  # 15 days from now
    assert result is None, "Expected None when requesting weather data beyond 14 days"


# Test for weather data in the past (should return None)
@patch("requests.get")
def test_get_weather_past_date(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {}

    generator = Generator()
    result = generator.get_weather("London", get_future_date(-1))  # 1 day in the past
    assert (
        result is None
    ), "Expected None when trying to fetch weather data for past dates"
