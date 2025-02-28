from duckduckgo_search import DDGS
import asyncio


async def get_n_random_places(titles):
    # filter out items where value is empty
    filtered_titles = {k: v for k, v in titles.items() if v is not None and len(v) > 0}

    keys = list(filtered_titles.keys())
    values = list(filtered_titles.values())
    final_data = await search_duckduckgo_images(values, keys)
    return final_data


def search_single_image(query, key):
    with DDGS() as ddgs:
        results = ddgs.images(query, max_results=2)
        if results:
            return key, [results[0]["image"], results[1]["image"]]
        return key, None


async def search_duckduckgo_images(queries, keys):
    data = {}

    # Create a mapping between queries and keys
    query_key_map = {queries[i]: keys[i] for i in range(len(queries))}

    # Run searches concurrently using asyncio.to_thread
    tasks = [
        asyncio.to_thread(search_single_image, query, query_key_map[query])
        for query in queries
    ]

    results = await asyncio.gather(*tasks)

    # Process results
    for key, image_url in results:
        if image_url:
            data[key] = image_url

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
        print(val, "\n")
