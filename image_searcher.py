from duckduckgo_search import DDGS
from concurrent.futures import ThreadPoolExecutor


def get_n_random_places(titles):
    # unpack dict if necessary before this
    keys = list(titles.keys())
    values = list(titles.values())
    final_data = search_duckduckgo_images(values, keys)
    return final_data


def search_single_image(query, key):
    with DDGS() as ddgs:
        results = ddgs.images(query, max_results=2)
        if results:
            return (key, [results[0]["image"], results[1]["image"]])
        return (key, None)


def search_duckduckgo_images(queries, keys):
    data = dict()
    # Create a mapping between queries and their corresponding keys
    query_key_map = {queries[i]: keys[i] for i in range(len(queries))}

    # Use ThreadPoolExecutor to run searches concurrently
    with ThreadPoolExecutor(max_workers=min(10, len(queries))) as executor:
        # Submit all search tasks
        future_to_query = {
            executor.submit(search_single_image, query, query_key_map[query]): query
            for query in queries
        }

        # Process results as they complete
        for future in future_to_query:
            try:
                key, image_url = future.result()
                if image_url:
                    data[key] = image_url
            except Exception as e:
                print(f"Error searching for image: {e}")

    return data


# Example usage
if __name__ == "__main__":
    titles = {
        "1": "Montmartre",
        "2": "New York",
        "3": "London",
        "4": "Paris",
        "5": "Tokyo",
    }
    places = get_n_random_places(titles)
    for val in places.values():
        print(val, '\n')
