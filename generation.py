from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from dotenv import load_dotenv
from generation_models import ActivityList, FullItinerary, ActivityTitles
import time

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
            human_prompt = f"Generate full details for the following activities: {', '.join(titles)}"
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

    def generate_itinerary(self, location):
        structured_model = self.llm.with_structured_output(FullItinerary)

        # set prompting messages
        messages = [
            SystemMessage(
                "You are an AI travel agent that needs to suggest possible itinerary activities to a user based on a given location."
                "You must provide all details in the schema requested."
            ),
            HumanMessage(
                f"Generate a full day itinerary that could make for an interesting activity in the following location: {location}."
                "Make sure you provide all travel steps between each venue."
            ),
        ]

        response = structured_model.invoke(messages)

        return response.model_dump()["itinerary"]


"""start = time.time()

generator = Generator()

print(generator.generate_activities("London"))

print(f"Model took {time.time() - start} seconds to run.")"""
