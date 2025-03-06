import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from routes import activities, itinerary, facts, swap

load_dotenv()

app = FastAPI()

# Allow CORS for the React app's origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "https://voya-trips.com",
        "https://www.voya-trips.com",
        os.getenv("DATABASE_API_URL"),
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(activities.router)
app.include_router(itinerary.router)
app.include_router(facts.router)
app.include_router(swap.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
