from fastapi import APIRouter

from root.standalone.scrapers.scraper_belgrad_consult_com import get_data

router = APIRouter(prefix="/standalone")


@router.get("/belgrad_consult_com")
async def get_events() -> dict:
    data = await get_data()
    return {
        "status": "success",
        "data": data,
    }
