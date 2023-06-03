""" API """
from fastapi import FastAPI

from scraper import scrape_website


app = FastAPI()
data = scrape_website()

@app.get('/')
def get_events():
    
    return {"data": data}