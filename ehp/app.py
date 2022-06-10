import asyncio
from datetime import date, datetime

import httpx
from bs4 import BeautifulSoup
from p3orm import Porm
from pydantic import BaseModel

from ehp.db.models import Item, Sale
from ehp.settings import Settings
from ehp.utils.log import get_logger, log_exception

logger = get_logger(__name__)


SOLD_ITEMS_URL = "https://www.ebay.com/sch/i.html?_from=R40&_nkw={query}&_sacat=0&LH_TitleDesc=0&_fsrp=1&LH_Sold=1&rt=nc&LH_ItemCondition=3000"


class SaleMetadata(BaseModel):
    date_sold: date
    listing_name: str
    listing_url: str
    listing_image: str
    listing_price: int


def normalize_query(name: str) -> str:
    return name.lower().replace(" ", "+")


async def persist_sales(item: Item, sale_metadatas: list[SaleMetadata]) -> list[Sale]:

    existing_sales = await Sale.fetch_all(Sale.listing_url.isin([s.listing_url for s in sale_metadatas]))
    existing_sale_urls = [s.listing_url for s in existing_sales]

    to_insert: list[Sale] = []

    for sale_metadata in sale_metadatas:
        if sale_metadata.listing_url in existing_sale_urls:
            continue

        to_insert.append(
            Sale(
                item_id=item.id,
                listing_price=sale_metadata.listing_price,
                sold_at=sale_metadata.date_sold,
                listing_name=sale_metadata.listing_name,
                listing_url=sale_metadata.listing_url,
                listing_image=sale_metadata.listing_image,
            )
        )

    if not to_insert:
        return []

    return await Sale.insert_many(to_insert)


async def get_sale_metadatas_for_item(item: Item) -> list[SaleMetadata]:

    async with httpx.AsyncClient() as client:
        url = SOLD_ITEMS_URL.format(query=normalize_query(item.name))

        resp = await client.get(url)

    if resp.status_code != 200:
        logger.info(f"error getting search results {resp.status_code}")
        return []

    html = resp.text
    soup = BeautifulSoup(html, features="html.parser")

    result_column = soup.find("div", attrs={"class": "srp-river srp-layout-inner"})
    listings = result_column.find_all("li", attrs={"class": "s-item s-item__pl-on-bottom"})

    sale_metadatas = []

    for listing in listings:
        listing_title = listing.find("h3").text

        if normalize_query(item.name) not in normalize_query(listing_title):
            continue

        listing_url = listing.find("a").get("href")

        if "https://ebay.com/itm/123456" in listing_url:
            continue

        listing_image = listing.find("img").get("src")

        listing_price = int(
            float(listing.find("span", attrs={"class": "s-item__price"}).text[1:].replace(",", "")) * 100
        )

        sold_at = datetime.strptime(
            listing.find("div", attrs={"class": "s-item__title--tagblock"})
            .find("span", attrs={"class": "POSITIVE"})
            .text,
            "SOLD %b %d, %Y",
        ).date()

        sale_metadatas.append(
            SaleMetadata(
                date_sold=sold_at,
                listing_name=listing_title,
                listing_url=listing_url,
                listing_image=listing_image,
                listing_price=listing_price,
            )
        )

    return sale_metadatas


async def scrape_and_persist_ebay_sales():

    items = await Item.fetch_all(Item.deleted_at.isnull())

    all_persisted_sales = []

    for item in items:
        found_sale_metadatas = await get_sale_metadatas_for_item(item)
        persisted_sales = await persist_sales(item, found_sale_metadatas)

        logger.info(f"processed {item.name=} {len(found_sale_metadatas)=} {len(persisted_sales)=}")
        all_persisted_sales += persisted_sales

    return all_persisted_sales


async def run():

    await Porm.connect(Settings.DATABASE_URL)

    try:
        persisted_sales = await scrape_and_persist_ebay_sales()
        logger.info(f"persisted a total of {len(persisted_sales)} sales")
    except Exception as e:
        log_exception(logger.exception, "error running", e)

    await Porm.disconnect()


if __name__ == "__main__":
    asyncio.run(run())
