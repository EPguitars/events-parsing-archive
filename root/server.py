""" API """
from fastapi import FastAPI

from root.routers import router

app = FastAPI()

app.include_router(router)
