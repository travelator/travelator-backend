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
        self.llm = ChatOpenAI(model="gpt-4o-mini")

    # Fetch Live weather data
    @staticmethod
    def get_weather(location, date=None):
        """
        Fetches hourly weather forecast for a given location and date using WeatherAPI.

        Args:
            location (str): The location to get weather for
            date (str, optional): The date in YYYY-MM-DD format. Defaults to None (current day).

        Returns:
            list: List of dictionaries containing hourly weather data from 7am to midnight
                  Each dict has keys: time (str), weather (str), temperature (int)
        """
        API_KEY = os.getenv("WEATHERAPI_KEY")  # Load from .env
        if not API_KEY:
            raise ValueError("WEATHERAPI_KEY is missing from environment variables!")

        url = "http://api.weatherapi.com/v1/forecast.json"

        # If a date is provided, we need to calculate days in the future
        # WeatherAPI allows forecast up to 14 days
        days_param = 1
        if date:
            # Calculate days difference between today and requested date
            today = datetime.now().date()
            requested_date = datetime.strptime(date, "%Y-%m-%d").date()
            days_diff = (requested_date - today).days

            # Ensure the requested date is within API limits (0-14 days)
            if days_diff < 0:
                return {"error": "Cannot retrieve weather for past dates"}
            elif days_diff > 14:
                return {"error": "Weather forecast is only available up to 14 days in the future"}
            else:
                days_param = days_diff + 1  # Need at least this many days to include the requested date

        params = {
            "key": API_KEY,
            "q": location,

            "aqi": "no",
            "days": days_param,
            "hour": "0-23"  # Get all hours
        }

        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code != 200 or "forecast" not in data:
            return {"error": f"Weather API error: {data.get('error', {}).get('message', 'Unexpected API response')}"}

        # Get the forecast for the requested date (or today if no date)
        target_date = date if date else datetime.now().strftime("%Y-%m-%d")

        # Find the forecast for the target date
        forecast_day = None
        for day in data["forecast"]["forecastday"]:
            if day["date"] == target_date:
                forecast_day = day
                break

        if not forecast_day:
            return {"error": f"Weather forecast for {target_date} not available"}

        hourly_data = forecast_day["hour"]

        # Filter hours between 7am and midnight
        filtered_hours = []
        for hour_entry in hourly_data:
            hour_time_obj = datetime.strptime(hour_entry["time"], "%Y-%m-%d %H:%M")
            hour = hour_time_obj.hour

            if 7 <= hour <= 23:  # From 7am to midnight (23:00)
                filtered_hours.append({
                    "time": hour_time_obj.strftime("%H:%M"),  # Format as HH:MM
                    "weather": hour_entry["condition"]["text"],
                    "temperature": int(round(hour_entry["temp_c"]))  # Round to nearest integer
                })

        return filtered_hours

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

        response = await structured_model.ainvoke(messages)

        return response.model_dump()["activities"]

    # Generate itinerary item details
    def generate_itinerary(
            self,
            location,
            timeOfDay,
            group,
            uniqueness,
            preferences=None,
            prior_itinerary=None,
            feedback=None,
    ):
        structured_model = self.llm.with_structured_output(ItinerarySummary)

        # Fetch hourly weather data
        weather_data = self.get_weather(location)

        if "error" in weather_data:
            weather_string = "Weather data is currently unavailable."
            weather_data = {}  # Avoid breaking code later
        else:
            weather_string = "Weather data is included per event."

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

        response = structured_model.invoke(messages)

        # **Integrate Weather Data into Itinerary Response**
        for event in response.itinerary:
            # Convert event time to nearest hour format: 'YYYY-MM-DD HH:00'
            event_time_obj = datetime.strptime(event.start_time, "%Y-%m-%d %H:%M")
            event_hour_str = event_time_obj.strftime("%Y-%m-%d %H:00")

            weather_info = weather_data.get(event_hour_str, None)

            if weather_info:
                event.weather = {
                    "icon": weather_info["icon"],  # Icon URL
                    "description": weather_info["description"],  # Weather condition
                    "temperature": weather_info["temperature"],  # Temperature
                }
            else:
                event.weather = {
                    "icon": None,
                    "description": "Weather data unavailable",
                    "temperature": None,
                }

        return response

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
                f"Bear in mind the user is travelling {Prompts.get_group_prompt(group)}"
            ),
            HumanMessage(
                f"Generate full details for the following activity: {itineraryItem.title}"
                f"The activity will start at {itineraryItem.start} and finish at {itineraryItem.end}"
                f"The item has id {itineraryItem.id} - you must keep this id."
            ),
        ]

        response = await structured_model.ainvoke(messages)

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

    async def swap_activity(
        self,
        activity: str,
        location: str,
        group: str,
        uniqueness: int,
        itinerary: FullItinerary,
        feedback: str,
    ) -> ItineraryItem:
        # set model
        structured_model = self.llm.with_structured_output(ItineraryItem)

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
            ),
            SystemMessage(prior_itinerary_str),
            HumanMessage(
                f"Generate a new activity to replace the following activity: {Prompts.activity_to_string(activity)}."
            ),
        ]

        response = await structured_model.ainvoke(messages)
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

        response = await structured_model.ainvoke(messages)

        return response.facts


"""async def main():
    start = time.time()

    generator = Generator()

    print(await generator.generate_facts("London", num=3))

    print(f"Model took {time.time() - start} seconds to run.")

asyncio.run(main())"""
