import uvicorn
from fastapi import FastAPI

# from FetchUserPref import apicall

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Travelator backend is running"}


if __name__ == "__main__":
    # apicall()
    uvicorn.run(app, host="0.0.0.0", port=8000)
