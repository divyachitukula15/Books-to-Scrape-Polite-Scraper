import requests
from pathlib import Path


URL = "https://books.toscrape.com/catalogue/page-1.html"

CACHE_FILE = (
    Path(__file__).parent.parent
    / "cache"
    / "catalogue-page-1.html"
)

USER_AGENT = "FlyRankInternship-A9/1.0"


def fetch_page():
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    if CACHE_FILE.exists():
        html = CACHE_FILE.read_text(encoding="utf-8")
        print(f"CACHE HIT: {len(html)} bytes")
        return html

    print("FETCH")

    headers = {
        "User-Agent": USER_AGENT
    }

    response = requests.get(
        URL,
        headers=headers,
        timeout=30
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Fetch failed: HTTP {response.status_code}"
        )

    html = response.text

    CACHE_FILE.write_text(
        html,
        encoding="utf-8"
    )

    print(f"Fetched: {len(html)} bytes")

    return html


if __name__ == "__main__":
    fetch_page()