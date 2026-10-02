import time
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

        # Find every book link on this catalogue page
        for article in soup.select("article.product_pod"):
            link = article.select_one("h3 a")

            if link and link.get("href"):
                book_url = urljoin(current_url, link["href"])
                all_book_urls.add(book_url)

        print(
            f"Page {page_number}: "
            f"{len(all_book_urls)} unique books discovered"
        )

        # Find next catalogue page
        next_link = soup.select_one("li.next a")

        if not next_link:
            break

        next_url = urljoin(current_url, next_link["href"])

        # Wait before the next real request
        time.sleep(0.5)

        current_url = next_url

    return all_book_urls


if __name__ == "__main__":
    book_urls = discover_books()

    print()
    print("CHECKPOINT")
    print(f"catalogue_pages=3")
    print(f"discovered={len(book_urls)}")
    print(f"unique_urls={len(book_urls)}")