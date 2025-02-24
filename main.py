import uvicorn
from fastapi import FastAPI
from generation import Generator
from request_models import ActivityRequest, ItineraryRequest
from fastapi.middleware.cors import CORSMiddleware
from image_searcher import get_n_random_places

app = FastAPI()
generator = Generator()

# Allow CORS for the React app's origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "https://voya-trips.com",
        "https://www.voya-trips.com",
    ],  # React app's origin (adjust if needed)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)


@app.get("/")
def read_root():
    return {"message": "Travelator backend is running"}


@app.post("/activities")
def get_activities(request: ActivityRequest):
    city = request.city
    timeOfDay = request.timeOfDay
    group = request.group

    # Activity titles is a list of string representing different activity titles
    activity_titles = generator.generate_activities(city, titles_only=True)

    get_n_random_places(activity_titles)

    activity_response = generator.generate_activities(city, titles=activity_titles)

    # TODO: update image_link for each activity

    return {"activities": activity_response}


@app.post("/itinerary")
def get_itinerary(request: ItineraryRequest):
    city = request.city

    itinerary_response = generator.generate_itinerary(city)
    return {"itinerary": itinerary_response}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
