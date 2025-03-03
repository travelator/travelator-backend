from fastapi import APIRouter
from generation.generation import Generator


router = APIRouter()
generator = Generator()


@router.get("/facts")
async def get_facts(location: str, num: int):
    # Get facts for the location
    facts = await generator.generate_facts(location, num)

    return {"facts": facts}
