from fastapi import APIRouter

from root.standalone import views

router = APIRouter(prefix="/api")

router.include_router(views.router)
