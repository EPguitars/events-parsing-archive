# pylint: disable=W0611, E0401
"""
Main goal of this module is to scrape and parse data from "visityerevan.am" website
"""
import logging
import sys

from dataclasses import dataclass
from urllib.parse import urljoin

from httpx import Client
from selectolax.parser import HTMLParser, Node


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)
stream_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s:%(name)s:%(lineno)d:%(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
           "AppleWebKit/537.36 (KHTML, like Gecko) " +
           "Chrome/109.0.0.0 Safari/537.36"}


@dataclass
class Event:
    """ Class contains all info about event """
    title: str
    description: str
    url_to_original: str
    time: str
    price: str
    img: str


@dataclass
class Response:
    """ Class contains html of page and info about existing of the next page """
    body_html: HTMLParser
    status_code: int


def serialize_event(event):
    """ Resulting format for each event """
    return {
        "id": "work in progress...",
        "type": "parsed_v1",
        "parserName": "visityerevan",
        "title": event.title,
        "description": event.description,
        "date": event.time,
        "durationInSeconds": 0,
        "location": {
                "country": "Armenia",
                "city": "Erevan",
        },
        "image": event.img,
        "price": {
            "amount": event.price,
            "currency": "AMD"
        },
        "timezone": {
            "timezoneName": "AMT",
            "timezoneOffset": "UTC +4",
        },
        "url": event.url_to_original,
    }


def get_page(client: Client, url: str) -> Response:
    """ Scrape html from page and check if next pages appears """
    resp = client.get(url, headers=HEADERS)
    html = HTMLParser(resp.text)

    return Response(body_html=html, status_code=resp.status_code)


def get_pages_amount(client: Client, url: str) -> int:
    """ func to get number of pages with events """
    resp = client.get(url, headers=HEADERS)
    html = HTMLParser(resp.text)

    pages_amount = html.css("ul[class='pagination justify-content-center'] >" +
                            "li[class='page-item']")[-1:][0].text()

    return int(pages_amount)


def is_valid(data):
    """ Helps us to catch website's structure changes """
    if data is None:
        logger.warning(
            "Seems that website changed structure. Please recheck code and website")

        return False
    else:
        return True


def parse_detail(blocks: list) -> list:
    """ Clean and prepare all data that we need """
    result = []

    # In this loop we will extract all
    #  Info that we can from each event's div
    for block in blocks:
        # Extract and prepare "time"
        month_day = block.css_first(
            "div[class='col-12 mt-n1'] > div")
        # Need validate data each parsing attempt
        if is_valid(month_day):
            month_day = month_day.text().replace('\n', '').strip()

        time = block.css_first(
            "div[class='text-grey text-md mb-2']")

        if is_valid(time):
            time = time.text().replace('\n', '').strip().split(' ')
            cleaned_time = f"{month_day} {time[-1:][0]}"
        else:
            cleaned_time = None
        # Extract and prepare "description"
        description = block.css_first("p")
        if is_valid(description):
            description = description.text().strip()
        # Clean and prepare "url"
        url = block.css_first("a").attrs["href"]
        if is_valid(url):
            url = "https://www.visityerevan.am" + url
        # Extract price
        price = ''
        cards = block.css("p.card-text > span")

        if len(cards) == 0:
            logger.warning(
                "Seems that website changed structure. Please recheck code and website")
        else:
            for card in cards:
                card = card.text()
                if "AMD" in card:
                    price = card.replace("AMD", "").strip()
                else:
                    price = "no info"
        # Extract img link
        img = block.css_first("img").attrs["src"]

        if is_valid(img):
            img = "https://www.visityerevan.am" + img
        # There is not need in cleaning "title"
        # With data we have create a new event object
        event = Event(
            title=block.css_first("h5").text(),
            description=description,
            url_to_original=url,
            time=cleaned_time,
            price=price,
            img=img
        )

        result.append(serialize_event(event))

    return result


def scrape_blocks(html: HTMLParser) -> list:
    """ Getting all divs with information from page """
    blocks = html.css("div[class='row px-lg-7']" +
                      " > div")

    return blocks


def pagination_loop(client: Client) -> list:
    """ Loop through all pages """
    url = "https://www.visityerevan.am/browse/things-to-do-events/ru/"
    # How many pages we will scrape
    pages_amount = get_pages_amount(client, url)
    # Blocks contains all divs that we need
    blocks = []
    # Iterating through all pages
    for page_number in range(1, pages_amount + 1):
        # Mutating a url to get page with current page number
        url = urljoin(url, f"?sel_filters=&current_page={page_number}")
        # Get object with scraped html markup from current page
        page = get_page(client, url)
        # Grad all divs with events data and append to list
        blocks += scrape_blocks(page.body_html)

    # Scraping is done, time to close session
    client.close()

    return blocks


async def scrape_website() -> list:
    """ Main function which contains all logic """
    # Start a new session
    client = Client()
    # Create list with all divs which contain info about events
    all_blocks = pagination_loop(client)
    # Parsing data from divs
    parsed_data = parse_detail(all_blocks)

    return parsed_data
