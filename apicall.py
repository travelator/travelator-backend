import requests
def apicall():
    url = "https://api.geoapify.com/v2/places?categories=catering.restaurant,catering.taproom&conditions=vegetarian&filter=circle:-0.2710713,51.5110185,5000&bias=proximity:-0.2710713,51.5110185&limit=20&apiKey=YOUR_API_KEY"

    response = requests.get(url)
    print(response.status_code)
    print(response.json())