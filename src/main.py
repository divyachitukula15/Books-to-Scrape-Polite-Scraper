import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from models import Book


BASE_URL = "https://books.toscrape.com/"
START_URL = "https://books.toscrape.com/catalogue/page-1.html"

PROJECT_DIR = Path(__file__).parent.parent
CACHE_DIR = PROJECT_DIR / "cache"
RAW_FILE = PROJECT_DIR / "raw-books.json"
OUTPUT_DIR = PROJECT_DIR / "output"
ERRORS_FILE = PROJECT_DIR / "errors.json"
REPORT_FILE = PROJECT_DIR / "run-report.json"

USER_AGENT = "FlyRankInternship-A9/1.0"
TIMEOUT = 10
REQUEST_DELAY = 0.5


def fetch_page(url, cache_file):
    if cache_file.exists():
        html = cache_file.read_text(encoding="utf-8")
        print(f"CACHE HIT: {cache_file.name} ({len(html)} bytes)")
        return html, False

    for attempt in range(2):
        try:
            print(f"FETCH: {url}")

            response = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT
            )

            if response.status_code in (403, 404):
                raise RuntimeError(
                    f"HTTP {response.status_code}"
                )

            if 500 <= response.status_code < 600:
                if attempt == 0:
                    print(
                        f"HTTP {response.status_code} - retrying once"
                    )
                    time.sleep(1)
                    continue

                raise RuntimeError(
                    f"HTTP {response.status_code} after retry"
                )

            if response.status_code != 200:
                raise RuntimeError(
                    f"HTTP {response.status_code}"
                )

            html = response.text

            cache_file.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            cache_file.write_text(
                html,
                encoding="utf-8"
            )

            print(f"Fetched: {len(html)} bytes")

            return html, True

        except requests.Timeout:
            if attempt == 0:
                print("TIMEOUT - retrying once")
                time.sleep(1)
                continue

            raise RuntimeError("Timeout after retry")

    raise RuntimeError("Request failed")


def discover_books():
    all_book_urls = set()
    current_url = START_URL
    fetched_pages = 0
    cache_hits = 0

    for page_number in range(1, 4):
        cache_file = (
            CACHE_DIR /
            f"catalogue-page-{page_number}.html"
        )

        html, fetched = fetch_page(
            current_url,
            cache_file
        )

        if fetched:
            fetched_pages += 1
        else:
            cache_hits += 1

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        for article in soup.select(
            "article.product_pod"
        ):
            link = article.select_one("h3 a")

            if link and link.get("href"):
                book_url = urljoin(
                    current_url,
                    link["href"]
                )

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

        time.sleep(REQUEST_DELAY)

    return sorted(all_book_urls), fetched_pages, cache_hits


def extract_book(url, source_page):
    filename = (
        url.rstrip("/").split("/")[-2]
        + ".html"
    )

    cache_file = (
        CACHE_DIR /
        "books" /
        filename
    )

    html, fetched = fetch_page(
        url,
        cache_file
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    title_element = soup.select_one(
        "div.product_main h1"
    )

    price_element = soup.select_one(
        "p.price_color"
    )

    availability_element = soup.select_one(
        "p.availability"
    )

    rating_element = soup.select_one(
        "p.star-rating"
    )

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
        availability_element.get_text(
            " ",
            strip=True
        )
        if availability_element
        else None
    )

    rating_text = None

    if rating_element:
        rating_classes = rating_element.get(
            "class",
            []
        )

        rating_text = next(
            (
                item
                for item in rating_classes
                if item != "star-rating"
            ),
            None
        )

    description = (
        description_element.get_text(
            " ",
            strip=True
        )
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
        "fetched_at": datetime.now(
            timezone.utc
        ).isoformat()
    }, fetched


def normalize_price(price_text):
    if not price_text:
        return None

    cleaned = (
        price_text
        .replace("£", "")
        .replace("Â", "")
        .strip()
    )

    return float(cleaned)


def validate_and_store(raw_records):
    valid_records = []
    invalid_records = []

    for record in raw_records:
        try:
            record["price_gbp"] = normalize_price(
                record["price_text"]
            )

            validated_book = Book.model_validate(
                record
            )

            valid_records.append(
                validated_book.model_dump(
                    mode="json"
                )
            )

        except Exception as error:
            invalid_records.append(
                {
                    "record": record,
                    "error": str(error)
                }
            )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    (OUTPUT_DIR / "books.json").write_text(
        json.dumps(
            valid_records,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    ERRORS_FILE.write_text(
        json.dumps(
            invalid_records,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    return len(valid_records), len(invalid_records)


def main():
    start_time = datetime.now(
        timezone.utc
    )

    failed_pages = []
    raw_records = []

    book_urls, fetched_pages, cache_hits = (
        discover_books()
    )
    

  

    for index, url in enumerate(
        book_urls,
        start=1
    ):
        print(
            f"[{index}/{len(book_urls)}] "
            f"Extracting: {url}"
        )

        try:
            record, _ = extract_book(
                url,
                START_URL
            )

            raw_records.append(record)

        except Exception as error:
            print(
                f"FAILED: {url} - {error}"
            )

            failed_pages.append(
                {
                    "url": url,
                    "error": str(error)
                }
            )

        if index < len(book_urls):
            time.sleep(REQUEST_DELAY)

    RAW_FILE.write_text(
        json.dumps(
            raw_records,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    valid_records, invalid_records = (
        validate_and_store(raw_records)
    )

    duration = (
        datetime.now(timezone.utc)
        - start_time
    ).total_seconds()

    report = {
        "start_time": start_time.isoformat(),
        "duration_seconds": duration,
        "fetched_pages": fetched_pages,
        "cache_hits": cache_hits,
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "failed_pages": failed_pages
    }

    REPORT_FILE.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print()
    print("RUN COMPLETE")
    print(f"Valid records: {valid_records}")
    print(f"Invalid records: {invalid_records}")
    print(f"Failed pages: {len(failed_pages)}")
    print(f"Run report: {REPORT_FILE}")


if __name__ == "__main__":
    main()