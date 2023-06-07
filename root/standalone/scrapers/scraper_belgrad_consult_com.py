import asyncio
from datetime import datetime

from selectolax.parser import HTMLParser, Node
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
)
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By


async def get_page() -> str:
    options = ChromeOptions()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    driver.get("https://belgrad-consult.com/afisha-belgrada")

    button = driver.find_element(
        By.CSS_SELECTOR,
        "div[id='rec566883233'] "
        "div[class='js-feed-btn-show-more "
        "t-feed__showmore-btn t-btn t-btn_md']",
    )

    try:
        cnt = 0
        while cnt < 100:
            cnt += 1
            try:
                button.click()
            except ElementClickInterceptedException:
                driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                await asyncio.sleep(0.1)
    except ElementNotInteractableException:
        pass

    html = driver.page_source
    driver.close()
    return html


def scrape_blocks(page: str) -> list:
    html = HTMLParser(page)
    blocks = html.css(
        "div[id='allrecords'] "
        "> div[id='rec566883233'] "
        "> div[class='t915'] "
        "> div "
        "> div "
        "> div["
        "class='js-feed-post "
        "t-feed__post "
        "t-item "
        "t-width "
        "t-feed__grid-col "
        "t-col "
        "t-col_4 "
        "t-align_left'"
        "]"
    )

    return blocks


def parse_block(block: Node) -> dict:
    base_node = block.css_first(
        "a "
        "> div "
        "> div["
        "class='t-feed__col-grid__wrapper "
        "t-feed__col-grid__wrapper_align "
        "t-feed__col-grid__content '"
        "]"
    )
    img = block.css_first("a > div > div > img").attributes.get("src")
    date, time = base_node.css_first("div > span").text().split()
    date = datetime.strptime(date, "%d.%m.%Y").date().isoformat()
    title = base_node.css_first("div > div:nth-child(2) > div").text()
    description = base_node.css_first(
        "div > div:nth-child(2) > div:nth-child(2)"
    ).text()
    url = block.css_first("a").attributes.get("href")

    return {
        "id": 1,
        "type": "parsed_v1",
        "parserName": "scraper_belgrad_consult_com",
        "title": title,
        "description": description,
        "date": date,
        "time": time,
        "durationInSeconds": 0,
        "location": {
            "country": "Serbia",
            "city": "Belgrade",
        },
        "image": img,
        "price": None,
        "timezone": {
            "timezoneName": "Central European Time",
            "timezoneOffset": "UTC+01:00",
        },
        "url": url,
    }


async def get_data() -> list[dict]:
    html = await get_page()
    blocks = scrape_blocks(html)
    return [parse_block(block) for block in blocks]
