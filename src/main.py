import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://books.toscrape.com/"
START_URL = "https://books.toscrape.com/catalogue/page-1.html"

CACHE_DIR = Path(__file__).parent.parent / "cache"

USER_AGENT = "FlyRankInternship-A9/1.0"


def fetch_page(url, cache_file):
    if cache_file.exists():
        html = cache_file.read_text(encoding="utf-8")
        print(f"CACHE HIT: {cache_file.name} ({len(html)} bytes)")
        return html

    print(f"FETCH: {url}")

    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=10
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Fetch failed: HTTP {response.status_code}"
        )

    html = response.text

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(html, encoding="utf-8")

    print(f"Fetched: {len(html)} bytes")

    return html


def discover_books():
    all_book_urls = set()

    current_url = START_URL

    for page_number in range(1, 4):
        cache_file = CACHE_DIR / f"catalogue-page-{page_number}.html"

        html = fetch_page(current_url, cache_file)

        soup = BeautifulSoup(html, "html.parser")

        for article in soup.select("article.product_pod"):
            link = article.select_one("h3 a")

            if link and link.get("href"):
                book_url = urljoin(current_url, link["href"])
                all_book_urls.add(book_url)

        print(
            f"Page {page_number}: "
            f"{len(all_book_urls)} unique books discovered"
        )

        next_link = soup.select_one("li.next a")

        if not next_link:
            break

        current_url = urljoin(
            current_url,
            next_link["href"]
        )

        time.sleep(0.5)

    return sorted(all_book_urls)


def extract_book(url, source_page):
    filename = url.rstrip("/").split("/")[-2] + ".html"
    cache_file = CACHE_DIR / "books" / filename

    html = fetch_page(url, cache_file)

    soup = BeautifulSoup(html, "html.parser")

    title_element = soup.select_one("div.product_main h1")
    price_element = soup.select_one("p.price_color")
    availability_element = soup.select_one("p.availability")
    rating_element = soup.select_one("p.star-rating")

    description_element = soup.select_one(
        "#product_description + p"
    )

    title = (
        title_element.get_text(strip=True)
        if title_element
        else None
    )

    price_text = (
        price_element.get_text(strip=True)
        if price_element
        else None
    )

    availability_text = (
        availability_element.get_text(" ", strip=True)
        if availability_element
        else None
    )

    rating_text = None

    if rating_element:
        rating_classes = rating_element.get("class", [])
        rating_text = next(
            (
                item
                for item in rating_classes
                if item != "star-rating"
            ),
            None
        )

    description = (
        description_element.get_text(" ", strip=True)
        if description_element
        else None
    )

    return {
        "title": title,
        "product_url": url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }


def main():
    book_urls = discover_books()

    print()
    print(f"Total books: {len(book_urls)}")
    print()

    records = []

    for index, url in enumerate(book_urls, start=1):
        print(f"[{index}/60] Extracting: {url}")

        try:
            record = extract_book(
                url=url,
                source_page=START_URL
            )

            records.append(record)

        except Exception as error:
            print(f"ERROR: {error}")

        if index < len(book_urls):
            time.sleep(0.5)

    output_file = Path(__file__).parent.parent / "raw-books.json"

    output_file.write_text(
        json.dumps(
            records,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print()
    print(f"Extracted records: {len(records)}")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()