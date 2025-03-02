from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from generation_models import (
    ActivityList,
    ActivityTitles,
    ItineraryItem,
    SimpleItineraryItem,
    ItinerarySummary,
    Facts,
)
import asyncio
from typing import List
import prompts

load_dotenv()


class Generator:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini")

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
                f" The user is travelling {prompts.get_group_prompt(group)}."
            )

        if timeOfDay is not None:
            human_prompt += f" The user wants an itinerary for these parts of the day: {', '.join(timeOfDay)}."

        if uniqueness is not None:
            human_prompt += prompts.get_uniqueness_prompt(uniqueness)

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
    def generate_itinerary(
        self, location, timeOfDay, group, uniqueness, preferences=None, prior_itinerary=None, feedback=None
    ):
        structured_model = self.llm.with_structured_output(ItinerarySummary)

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
            prior_itinerary_str = f"The user has already been shown the following itinerary:\n{prompts.itinerary_to_string(prior_itinerary)}"
            if feedback is not None:
                prior_itinerary_str += f"The user provided feedback on the itinerary: {feedback}. Update the itinerary based on the user's feedback. Keep as close as possible to the original itinerary as you can while addressing the user's feedback."
        else:
            prior_itinerary_str = ""

        # set prompting messages
        messages = [
            SystemMessage(
                "You are an AI travel agent that needs to suggest possible itinerary activities to a user based on a given location."
                "You must provide all details in the schema requested."
                f"The user is travelling {prompts.get_group_prompt(group)}."
                f"The user wants an itinerary for these parts of the day: {', '.join(timeOfDay)}"
                f"{prompts.get_uniqueness_prompt(uniqueness)}"
                "You MUST include steps in the itinerary for travel between locations."
                "You must generate these travel steps as items in the itinerary so the user knows how to get between different events, and include start and end times for travel."
            ),
            SystemMessage(preference_string),
            SystemMessage(prior_itinerary_str),
            HumanMessage(
                f"Generate a full day itinerary for the user in the following location: {location}."
                "Explicitly include travel steps in the itinerary. For example, the title of an activity step could be 'Take the tube from Waterloo to Oxford Circus'"
            ),
        ]

        response = structured_model.invoke(messages)

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
                f"Bear in mind the user is travelling {prompts.get_group_prompt(group)}"
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


"""
start = time.time()

generator = Generator()

print(generator.generate_activities("London"))

print(f"Model took {time.time() - start} seconds to run.")"""
