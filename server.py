""" API  (in progress)"""
from fastapi import FastAPI

from standalone.scraper_visityerevan import scrape_website


app = FastAPI()


@app.get('/api/standalone/visityerevan')
def get_events():
    """ returns json with data from visityerevan """
    data = scrape_website()
    return {"data": data}
