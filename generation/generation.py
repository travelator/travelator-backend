from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from .generation_models import (
    ActivityList,
    ActivityTitles,
    ItineraryItem,
    SimpleItineraryItem,
    ItinerarySummary,
    Facts,
    FullItinerary,
)
import asyncio
from .prompts import Prompts
import os
import requests
from datetime import datetime

load_dotenv()


class Generator:
    def __init__(self):
        self.llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
        self.weather_api_key = os.getenv("WEATHER_API_KEY", None)
        self.weather_url = "http://api.weatherapi.com/v1/forecast.json"
        self.num_retries = 3

    # Fetch Live weather data
    def get_weather(self, location, date=None):
        """
        Fetches hourly weather forecast for a given location and date using WeatherAPI.

        Args:
            location (str): The location to get weather for
            date (str, optional): The date in YYYY-MM-DD format. Defaults to None (current day).

        Returns:
            list: List of dictionaries containing hourly weather data from 7am to midnight
                  Each dict has keys: time (str), weather (str), temperature (int)
        """
        if date is None:
            return None

        if self.weather_api_key is None:
            print(
                "Weather API key not found. Please set the WEATHER_API_KEY environment variable."
            )
            return None

        # Calculate days difference between today and requested date
        today = datetime.now().date()
        requested_date = datetime.strptime(date, "%Y-%m-%d").date()
        days_diff = (requested_date - today).days

        # Ensure the requested date is within API limits (0-14 days)
        if days_diff < 0:
            print("Cannot retrieve weather for past dates")
            return None
        elif days_diff > 14:
            return None

        # WeatherAPI allows forecast up to 14 days
        days_param = days_diff + 1

        params = {
            "key": self.weather_api_key,
            "q": location,
            "aqi": "no",
            "days": days_param,
            "hour": "0-23",  # Get all hours
        }

        response = requests.get(self.weather_url, params=params)
        data = response.json()

        if response.status_code != 200 or "forecast" not in data:
            print("Error fetching weather information")
            return None

        # Find the forecast for the target date
        forecast_day = None
        for day in data["forecast"]["forecastday"]:
            if day["date"] == date:
                forecast_day = day
                break

        if not forecast_day:
            return None

        hourly_data = forecast_day["hour"]

        # Filter hours between 7am and midnight
        filtered_hours = []
        for hour_entry in hourly_data:
            hour_time_obj = datetime.strptime(hour_entry["time"], "%Y-%m-%d %H:%M")
            hour = hour_time_obj.hour

            if 7 <= hour <= 23:  # From 7am to midnight (23:00)
                filtered_hours.append(
                    {
                        "time": hour_time_obj.strftime("%H:%M"),  # Format as HH:MM
                        "weather": hour_entry["condition"]["text"],
                        "temperature": int(
                            round(hour_entry["temp_c"])
                        ),  # Round to nearest integer
                    }
                )

        return filtered_hours

    async def invoke_with_retries(self, mdl, messages, retries):
        try:
            return await mdl.ainvoke(messages)
        except Exception as e:
            if retries > 1:
                print(f"Error invoking model: {e}. Retries left: {retries - 1}")
                return await self.invoke_with_retries(messages, retries - 1)
            raise  # Let the last failure propagate

    # Generate activities
    async def generate_activities(
        self,
        location,
        titles_only=False,
        uniqueness=None,
        titles=None,
        timeOfDay=None,
        group=None,
    ):
        num_activities = 6

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
            human_prompt += (
                f" The user is travelling {Prompts.get_group_prompt(group)}."
            )

        if timeOfDay is not None:
            human_prompt += f" The user wants an itinerary for these parts of the day: {', '.join(timeOfDay)}."

        if uniqueness is not None:
            human_prompt += Prompts.get_uniqueness_prompt(uniqueness)

        # set prompting messages
        messages = [
            SystemMessage(
                "You are an AI travel agent that needs to suggest possible itinerary activities to a user based on a given location."
                "Your writing style should match a travel blogger, it should be casual."
                "You must provide all details in the schema requested."
                "Wherever possible, you must include specific venues (e.g. 'Dinner at the Grove' and not just 'Dinner at a local restaurant')"
            ),
            HumanMessage(human_prompt),
        ]

        response = await self.invoke_with_retries(
            structured_model, messages, self.num_retries
        )

        return response.model_dump()["activities"]

    # Generate itinerary item details
    async def generate_itinerary(
        self,
        location,
        timeOfDay=None,
        group=None,
        uniqueness=None,
        preferences=None,
        prior_itinerary=None,
        feedback=None,
        weather=None,
    ):
        structured_model = self.llm.with_structured_output(ItinerarySummary)

        if weather is not None:
            # Fetch hourly weather data
            weather_string = f"Consider the following weather information available for the day in formulating the itinerary: ${weather}"
        else:
            weather_string = ""

        if preferences is not None:
            preference_string = (
                f"The user has already been shown some activities that they could like or dislike within the given location."
                f"The user 'liked' the following activities: {', '.join(preferences.liked)}"
                f"The user 'disliked' the following activities: {', '.join(preferences.disliked)}"
                "Consider what these preferences imply about the user when generating the itinerary."
            )
        else:
            preference_string = ""

        if prior_itinerary is not None:
            prior_itinerary_str = f"The user has already been shown the following itinerary:\n{Prompts.itinerary_to_string(prior_itinerary)}"
            if feedback is not None:
                prior_itinerary_str += f"The user provided feedback on the itinerary: {feedback}. Update the itinerary based on the user's feedback. Keep as close as possible to the original itinerary as you can while addressing the user's feedback."
                prior_itinerary_str += "Above all, you must make sure your response addresses the user's feedback - remove and change items as needed to achieve this."

        else:
            prior_itinerary_str = ""

        if timeOfDay is None:
            timeOfDay = ["morning", "afternoon", "evening"]

        # set prompting messages
        messages = [
            SystemMessage(
                "You are an AI travel agent that needs to suggest possible itinerary activities to a user based on a given location."
                "You must provide all details in the schema requested."
                f"The user is travelling {Prompts.get_group_prompt(group)}."
                f"The user wants an itinerary for these parts of the day: {', '.join(timeOfDay)}"
                f"{Prompts.get_uniqueness_prompt(uniqueness)}"
                "You MUST include steps in the itinerary for travel between locations."
                "When suggesting restaurants, you MUST provide specific restaurant names, cuisine type, and a brief description."
                "Example: Instead of 'Have a rooftop dinner,' say 'Enjoy an Italian fine dining experience at Aqua Shard, a rooftop restaurant with panoramic views of London.'"
                "You must generate these travel steps as items in the itinerary so the user knows how to get between different events, and include start and end times for travel."
                f"\n\n{weather_string}"
            ),
            SystemMessage(preference_string),
            SystemMessage(prior_itinerary_str),
            HumanMessage(
                f"Generate a full day itinerary for the user in the following location: {location}."
                "Explicitly include travel steps in the itinerary. For example, the title of an activity step could be 'Take the tube from Waterloo to Oxford Circus'"
            ),
        ]

        response = await self.invoke_with_retries(
            structured_model, messages, self.num_retries
        )

        return response

    # Generate details for all items asynchronously
    async def generate_item_details(
        self,
        itineraryItem: SimpleItineraryItem,
        location: str,
        group: str,
        weather: str = None,
    ) -> ItineraryItem:
        # set model
        structured_model = self.llm.with_structured_output(ItineraryItem)

        if weather is not None:
            # Fetch hourly weather data
            weather_string = f"Consider the following weather information available for the day in formulating the itinerary: ${weather}"
        else:
            weather_string = ""

        # set prompting messages
        messages = [
            SystemMessage(
                f"You are an AI travel agent preparing an itinerary for a user travelling to {location}."
                "Your writing style should match a travel blogger, it should be casual."
                "You must provide full details in the schema requested for the given activity."
                f"Bear in mind the user is travelling {Prompts.get_group_prompt(group)}"
                f"\n\n{weather_string}"
            ),
            HumanMessage(
                f"Generate full details for the following activity: {itineraryItem.title}"
                f"The activity will start at {itineraryItem.start} and finish at {itineraryItem.end}"
                f"The item has id {itineraryItem.id} - you must keep this id."
            ),
        ]

        response = await self.invoke_with_retries(
            structured_model, messages, self.num_retries
        )

        return response.model_dump()

    async def generate_itinerary_details(
        self, itinerary: ItinerarySummary, location: str, group: str, weather: str
    ):
        # create tasks for each item
        itinerary_items = itinerary.itinerary
        tasks = [
            self.generate_item_details(item, location, group, weather)
            for item in itinerary_items
        ]
        responses = await asyncio.gather(*tasks)
        return responses

    async def swap_activity(
        self,
        activity: str,
        location: str,
        group: str,
        uniqueness: int,
        itinerary: FullItinerary,
        feedback: str,
        weather: str = None,
    ) -> ItineraryItem:
        # set model
        structured_model = self.llm.with_structured_output(ItineraryItem)

        if weather is not None:
            # Fetch hourly weather data
            weather_string = f"Consider the following weather information available for the day in formulating the itinerary: ${weather}"
        else:
            weather_string = ""

        prior_itinerary_str = (
            f"The user is planning has been shown the following itinerary:\n{Prompts.itinerary_to_string(itinerary)}"
            "The user now wants to swap out a single activity on the itinerary for something else."
            f"You will be told what activity to swap, and you should swap it considering the following feedback: {feedback}"
        )

        # set prompting messages
        messages = [
            SystemMessage(
                f"You are an AI travel agent preparing an itinerary for a user travelling to {location}."
                "The user has already been provided with an itinerary and is now fine tuning it."
                "The user now wants to swap out a single activity on the itinerary for something else."
                "You must propose an alternative activity to the user with the exact same timings, also considering that it should be geographically near the current activity."
                f"The user is travelling {Prompts.get_group_prompt(group)}."
                f"{Prompts.get_uniqueness_prompt(uniqueness)}"
                "Provide your response as a new activity with the same timings."
                f"Above all, you must make sure your response takes into account the following user feedback: {feedback}."
                f"\n\n{weather_string}"
            ),
            SystemMessage(prior_itinerary_str),
            HumanMessage(
                f"Generate a new activity to replace the following activity: {Prompts.activity_to_string(activity)}."
            ),
        ]

        response = await self.invoke_with_retries(
            structured_model, messages, self.num_retries
        )
        return response

    async def generate_facts(self, location: str, num: int = 1):
        """Generates some interesting facts about a given location"""
        # set model
        structured_model = self.llm.with_structured_output(Facts)

        # make num bounded between 1 and 5
        num = max(1, min(num, 5))

        # set prompting messages
        messages = [
            SystemMessage(
                f"You must provide {num} interesting facts for a given location that will be good for a loading screen."
                "Here is an example for London: 'London is home to the world's first underground railway system, the Tube, which opened in 1863'"
            ),
            HumanMessage(
                f"Generate {num} interesting facts for the following location: {location}"
            ),
        ]

        response = await self.invoke_with_retries(
            structured_model, messages, self.num_retries
        )

        return response.facts
