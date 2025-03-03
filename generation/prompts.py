from .generation_models import FullItinerary


class Prompts:
    @staticmethod
    def get_group_prompt(group: str) -> str:
        if group == "solo":
            return "alone"
        elif group == "couples":
            return "as a couple with their partner"
        else:
            return f"with {group}"

    @staticmethod
    def get_uniqueness_prompt(uniqueness: int) -> str:
        if uniqueness == 0:
            return "It is the user's first time to the area and they are looking to see all of the classical top attractions"
        elif uniqueness == 1:
            return "The user has seen some of the most common major attractions, but is still looking to explore popular spots in the area"
        elif uniqueness == 2:
            return "The user is looking for off-the-beaten-path attractions that are not commonly visited by tourists"
        elif uniqueness == 3:
            return "The user is looking for hidden gems that are not commonly known by tourists"
        elif uniqueness == 4:
            return "The user is looking to fully live like a local and experience the city as a local would"

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
