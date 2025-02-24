from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from dotenv import load_dotenv
from generation_models import ActivityList, FullItinerary
import time

load_dotenv()


class Generator:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini")

    def generate_activities(self, location):
        structured_model = self.llm.with_structured_output(ActivityList)

        # set prompting messages
        messages = [
            SystemMessage(
                "You are an AI travel agent that needs to suggest possible itinerary activities to a user based on a given location."
                "You must provide all details in the schema requested."
            ),
            HumanMessage(
                f"Generate 5 activities that could make for an interesting activity in the following location: {location}."
            ),
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
