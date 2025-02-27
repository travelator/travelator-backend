from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from generation_models import (
    ActivityList,
    FullItinerary,
    ActivityTitles,
    ItineraryItem,
    SimpleItineraryItem,
    ItinerarySummary,
)
import asyncio
from typing import List

load_dotenv()


class Generator:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini")

    def generate_activities(self, location, titles_only=False, titles=None):
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

        # set prompting messages
        messages = [
            SystemMessage(
                "You are an AI travel agent that needs to suggest possible itinerary activities to a user based on a given location."
                "You must provide all details in the schema requested."
            ),
            HumanMessage(human_prompt),
        ]

        response = structured_model.invoke(messages)

        return response.model_dump()["activities"]
    
    def get_group_prompt(self, group:str):
        if (group == "solo"):
            return "alone"
        elif (group == "couples"):
            return "as a couple with their partner"
        else:
            return f"with {group}"

    def generate_itinerary(self, location, timeOfDay, group):
        structured_model = self.llm.with_structured_output(ItinerarySummary)

        # set prompting messages
        messages = [
            SystemMessage(
                "You are an AI travel agent that needs to suggest possible itinerary activities to a user based on a given location."
                "You must provide all details in the schema requested."
                f"The user is travelling {self.get_group_prompt(group)}."
                f"The user wants an itinerary for these parts of the day: {', '.join(timeOfDay)}"
                "You MUST include steps in the itinerary for travel between locations." 
                "You must generate these travel steps as items in the itinerary so the user knows how to get between different events."
            ),
            HumanMessage(
                f"Generate a full day itinerary for the user in the following location: {location}."
                "Explicitly include travel steps in the itinerary. For example, the title of an activity step could be 'Take the tube from Waterloo to Oxford Circus'"
            ),
        ]

        response = structured_model.invoke(messages)

        return response
    
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

        return response.model_dump()

    async def generate_itinerary_details(
        self, 
        itinerary: ItinerarySummary, 
        location: str, 
        group: str
    ):    
        # create tasks for each item
        itinerary_items = itinerary.itinerary
        tasks = [self.generate_item_details(item, location, group) for item in itinerary_items]
        responses = await asyncio.gather(*tasks)
        return responses

"""
start = time.time()

generator = Generator()

print(generator.generate_activities("London"))

print(f"Model took {time.time() - start} seconds to run.")"""
