from .generation_models import FullItinerary, ItineraryItem

from typing import List


class Prompts:
    @staticmethod
    def get_uniqueness_prompt(uniqueness: int) -> str:
        """
        Get a prompt for the uniqueness level.

        Args:
            uniqueness: An integer representing the uniqueness level (0-4)

        Returns:
            A string prompt describing the uniqueness level

        Raises:
            ValueError: If the uniqueness value is outside the valid range (0-4)
        """
        prompts = {
            0: "This is their first time visiting, so they want to see all the classic tourist attractions and main sights.",
            1: "They've visited before, but still want to see some popular spots along with some less touristy options.",
            2: "They've been a few times and want to experience more off-the-beaten-path locations.",
            3: "They know the place well and want to focus on hidden gems and local experiences.",
            4: "They want to completely live like a local, avoiding tourist areas entirely."
        }

        if uniqueness not in prompts:
            raise ValueError(f"Invalid uniqueness value: {uniqueness}. Expected values between 0-4.")

        return prompts[uniqueness]

    @staticmethod
    def get_group_prompt(group: str) -> str:

        """
        Get a prompt for the group type.

        Args:
            group: A string representing the type of group

        Returns:
            A string prompt describing the group
        """
        prompts = {
            "solo": "alone",
            "couples": "as a couple with their partner",
            "family": "with family",
            "friends": "with friends"
        }

        return prompts.get(group, "with their group")

    @staticmethod
    def get_time_of_day_prompt(time_of_day: List[str]) -> str:
        """
        Get a prompt for the time of day.

        Args:
            time_of_day: A list of strings representing times of day

        Returns:
            A string prompt describing the time of day
        """
        if not time_of_day:
            return "during the day"

        if len(time_of_day) == 1:
            return f"during the {time_of_day[0]}"
        elif len(time_of_day) == 2:
            return f"during the {time_of_day[0]} and {time_of_day[1]}"
        else:
            return "all day"

    @staticmethod
    def itinerary_to_string(itinerary: FullItinerary) -> str:
        itinerary_str = ""
        for item in itinerary.itinerary:
            json_item = item.model_dump()
            itinerary_str += "<Itinerary Item>\n"
            for key, value in json_item.items():
                itinerary_str += f"{key}: {value}\n"
            itinerary_str += "</Itinerary Item>\n"
        return itinerary_str

    @staticmethod
    def activity_to_string(activity: ItineraryItem) -> str:
        activity_str = ""
        json_item = activity.model_dump()
        for key, value in json_item.items():
            activity_str += f"{key}: {value}\n"
        return activity_str
