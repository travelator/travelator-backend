from duckduckgo_search import DDGS


def get_10_random_places(preferences):
    # convert json to list

    # temp return for testing
    return [
        {"name": "Monmatre", "activity": "walking tour"},
        {"name": "New York", "activity": "sightseeing"},
        {"name": "London", "activity": "sightseeing"},
        {"name": "Paris", "activity": "sightseeing"},
        {"name": "Tokyo", "activity": "sightseeing"},
    ]


def build_query(places):
    queries = [place["name"] + place["activity"] for place in places]
    print(queries)
    return queries


def search_duckduckgo_images(queries):
    results_list = []  # format is image and backup image

    for query in queries:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=2))
            results_list.append(results)
    return results_list


# Example usage
if __name__ == "__main__":
    places = get_10_random_places("hello")
    queries = build_query(places)
    final_list = search_duckduckgo_images(queries)
    for element in final_list:
        print(element)
