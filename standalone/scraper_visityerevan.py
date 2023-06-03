# pylint: disable=W0611, E0401
"""
Main goal of this module is to scrape and parse data from "visityerevan.am" website
"""
from dataclasses import dataclass
from urllib.parse import urljoin

from httpx import Client
from selectolax.parser import HTMLParser, Node
# uncomment if your want to use "smart" print (needs "rich" package be installed)
#from rich import print


@dataclass
class Event:
    """ Class contains all info about event """
    title: str
    description: str
    url_to_original: str
    time: str


@dataclass
class Response:
    """ Class contains html of page and info about existing of the next page """
    body_html: HTMLParser
    next_page: dict


def get_page(client: Client, url: str) -> Response:
    """ Scrape html from page and check if next pages appears """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
               "AppleWebKit/537.36 (KHTML, like Gecko) " +
               "Chrome/109.0.0.0 Safari/537.36"}
    resp = client.get(url, headers=headers)
    html = HTMLParser(resp.text)

    # Here we checking if next page appears or not
    if html.css_first("span[class='fas fa-angle-right']"):
        next_page = True

    else:
        next_page = False

    return Response(body_html=html, next_page=next_page)


def parse_detail(blocks: list) -> list:
    """ Clean and prepare all data that we need """
    result = []

    for block in blocks:
        # Clean and prepare "time"
        month_day = block.css_first(
            "div[class='col-12 mt-n1'] > div").text().replace('\n', '').strip()
        time = block.css_first(
            "div[class='text-grey text-md mb-2']").text().replace('\n', '').strip().split(' ')
        cleaned_time = f"{month_day} {time[-1:][0]}"

        # Clean and prepare "description"
        cleaned_description = block.css_first("p").text().strip()

        # Clean and prepare "url"
        cleaned_url = "https://www.visityerevan.am" + \
            block.css_first("a").attrs["href"]

        # There is not need in cleaning "title"
        # With data we have create a new event object
        event = Event(
            title=block.css_first("h5").text(),
            description=cleaned_description,
            url_to_original=cleaned_url,
            time=cleaned_time
        )

        result.append({"title": event.title,
                       "description": event.description,
                       "url_to_original": event.url_to_original,
                       "time": event.time})

    return result


def scrape_blocks(html: HTMLParser) -> list:
    """ Getting all divs with information from page """
    links = html.css("div[class='row px-lg-7']" +
                     " > div")

    return [link for link in links]


def pagination_loop(client: Client) -> list:
    """ Loop through all pages """
    url = "https://www.visityerevan.am/browse/things-to-do-events/ru/"
    # Counter represents number of page
    counter = 1
    # Blocks contains all divs that we need
    blocks = []

    while True:
        page = get_page(client, url)
        blocks += scrape_blocks(page.body_html)

        if page.next_page is False:
            client.close()
            break
        else:
            counter += 1
            url = urljoin(url, f"?sel_filters=&current_page={counter}")

    return blocks


def scrape_website() -> list:
    """ Main function which contains all logic """
    # Start a new session
    client = Client()
    # Create list with all divs which contain info about events
    all_blocks = pagination_loop(client)
    # Parsing data from divs
    parsed_data = parse_detail(all_blocks)

    return parsed_data
