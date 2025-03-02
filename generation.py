from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from generation_models import (
    ActivityList,
    ActivityTitles,
    ItineraryItem,
    SimpleItineraryItem,
    ItinerarySummary,
)
import asyncio
from typing import List
import requests
import os

load_dotenv()


class Generator:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini")

    # Prompt formatting based on group
    def get_group_prompt(self, group: str):
        if group == "solo":
            return "alone"
        elif group == "couples":
            return "as a couple with their partner"
        else:
            return f"with {group}"

    # Fetch Live weather data
    @staticmethod
    def get_weather(location):
        """
        Fetches current weather conditions for a given location using WeatherAPI.
        """
        API_KEY = os.getenv("WEATHERAPI_KEY")  # Load from .env
        url = f"http://api.weatherapi.com/v1/current.json"

        params = {
            "key": API_KEY,
            "q": location,
            "aqi": "no"  # Exclude air quality data for a faster response
        }

        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code != 200:
            return {"error": f"Weather API error: {data.get('error', {}).get('message', 'Unknown error')}"}

        return {
            "description": data["current"]["condition"]["text"],  # Weather description
            "temperature": data["current"]["temp_c"],  # Temperature in Celsius
            "rain": data["current"].get("precip_mm", 0),  # Rainfall in mm
            "wind_speed": data["current"]["wind_kph"]  # Wind speed in km/h
        }

    # Generate activities
    async def generate_activities(
        self, location, titles_only=False, titles=None, timeOfDay=None, group=None
    ):
        num_activities = 5

        if titles_only:
            structured_model = self.llm.with_structured_output(ActivityTitles)
        else:
            structured_model = self.llm.with_structured_output(ActivityList)

        if titles is not None:
            activity_str = "\n".join(
                [f"id: {i['id']}, title: {i['title']}" for i in titles]
            )
            human_prompt = f"Generate full details for the following activities, and stick to the given IDs: {activity_str}"
        else:
            human_prompt = f"Generate {num_activities} activities that could make for an interesting activity in the following location: {location}."

        if group is not None:
            human_prompt += f" The user is travelling {self.get_group_prompt(group)}."

        if timeOfDay is not None:
            human_prompt += f" The user wants an itinerary for these parts of the day: {', '.join(timeOfDay)}."

        # set prompting messages
        messages = [
            SystemMessage(
                "You are an AI travel agent that needs to suggest possible itinerary activities to a user based on a given location."
                "Your writing style should match a travel blogger, it should be casual."
                "You must provide all details in the schema requested."
            ),
            HumanMessage(human_prompt),
        ]

        response = await structured_model.ainvoke(messages)

        return response.model_dump()["activities"]

    # Generate itinerary item details
    def generate_itinerary(self, location, timeOfDay, group, preferences=None):
        structured_model = self.llm.with_structured_output(ItinerarySummary)

        # Fetch live weather data
        weather = Generator.get_weather(location)
        weather_desc = weather["description"]
        rain_level = weather["rain"]
        temp = weather["temperature"]

        # Adjust prompt based on weather
        weather_note = f"The current weather in {location} is {weather_desc}, with a temperature of {temp}°C."
        if rain_level > 5:
            weather_note += " It is currently raining, so avoid outdoor activities."
        elif rain_level == 0:
            weather_note += " The weather is clear, so outdoor activities are preferred."

        # Adjust preference string
        if preferences is not None:
            preference_string = (
                f"The user has already been shown some activities that they could like or dislike within the given location."
                f"The user 'liked' the following activities: {', '.join(preferences.liked)}"
                f"The user 'disliked' the following activities: {', '.join(preferences.disliked)}"
                "Consider what these preferences imply about the user when generating the itinerary."
            )
        else:
            preference_string = ""

        # Update LLM prompt
        messages = [
            SystemMessage(
                "You are an AI travel agent that needs to suggest possible itinerary activities to a user based on a given location."
                "You must provide all details in the schema requested."
                f"The user is travelling {self.get_group_prompt(group)}."
                f"The user wants an itinerary for these parts of the day: {', '.join(timeOfDay)}"
                "You MUST include steps in the itinerary for travel between locations."
                "You must generate these travel steps as items in the itinerary so the user knows how to get between different events, and include start and end times"
            ),
            SystemMessage(weather_note),  # 🌦️ Inject weather into prompt
            SystemMessage(preference_string),  # 🎯 Inject user preferences
            HumanMessage(
                f"Generate a full day itinerary for the user in the following location: {location}."
                "Explicitly include travel steps in the itinerary. For example, the title of an activity step could be 'Take the tube from Waterloo to Oxford Circus'"
            ),
        ]

        response = structured_model.invoke(messages)
        return response.model_dump()["itinerary"]

    # Generate details for all items asynchronously
    async def generate_item_details(
        self,
        itineraryItem: SimpleItineraryItem,
        location: str,
        group: str,
    ) -> ItineraryItem:
        # set model
        structured_model = self.llm.with_structured_output(ItineraryItem)

        # set prompting messages
        messages = [
            SystemMessage(
                f"You are an AI travel agent preparing an itinerary for a user travelling to {location}."
                "Your writing style should match a travel blogger, it should be casual."
                "You must provide full details in the schema requested for the given activity."
                f"Bear in mind the user is travelling {self.get_group_prompt(group)}"
            ),
            HumanMessage(
                f"Generate full details for the following activity: {itineraryItem.title}"
                f"The activity will start at {itineraryItem.start} and finish at {itineraryItem.end}"
                f"The item has id {itineraryItem.id} - you must keep this id."
            ),
        ]

        response = await structured_model.ainvoke(messages)
        print(response.model_dump())
        return response.model_dump()

    async def generate_itinerary_details(
        self, itinerary: ItinerarySummary, location: str, group: str
    ):
        # create tasks for each item
        itinerary_items = itinerary.itinerary
        tasks = [
            self.generate_item_details(item, location, group)
            for item in itinerary_items
        ]
        responses = await asyncio.gather(*tasks)
        return responses


"""
start = time.time()

generator = Generator()

print(generator.generate_activities("London"))

print(f"Model took {time.time() - start} seconds to run.")"""
