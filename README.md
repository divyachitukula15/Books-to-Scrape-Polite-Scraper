# Books to Scrape — Polite Scraper

## Overview

This project is a small, polite scraping pipeline built for the FlyRank Internship Week 5 A9 assignment.

It follows this pipeline:

**classify → fetch → extract → normalize → validate → store → report**

## Target

**Website:** Books to Scrape
**Classification:** Sandbox/training website

The scraper processes the first **3 catalogue pages** and discovers **60 unique book URLs**.

### Robots check

The requested robots file was:

`https://books.toscrape.com/robots.txt`

No robots file was found.

## Data collected

For each book, the scraper extracts:

* `title`
* `product_url`
* `price_text`
* `availability_text`
* `rating_text`
* `description`
* `source_page`
* `fetched_at`

During normalization, `price_text` is converted into numeric `price_gbp`.

The final records are validated using Pydantic.

## Project structure

```text
scraper/
├── cache/
├── output/
│   └── books.json
├── errors.json
├── run-report.json
├── requirements.txt
├── README.md
└── src/
    ├── main.py
    └── models.py
```

`cache/` and `raw-books.json` are excluded from Git.

## Installation

Python 3.10+ is required.

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

From the project directory:

```bash
python src/main.py
```

The scraper processes the catalogue, extracts book data, validates the records, stores the final JSON output, and creates a run report.

## Politeness rules

The scraper:

* Uses an identifying User-Agent.
* Uses a 10-second request timeout.
* Checks HTTP status codes.
* Waits at least 0.5 seconds between real requests.
* Caches downloaded catalogue and book pages.
* Retries a timeout or 5xx response once.
* Does not retry 403 or 404 responses.

## Output

The validated book records are stored in:

```text
output/books.json
```

Validation failures are stored in:

```text
errors.json
```

Run statistics and failed pages are stored in:

```text
run-report.json
```

A normal run produces 60 valid records.

## Failure handling

The scraper processes book pages individually. If one page fails, the failure is recorded in the run report and the scraper continues processing the remaining pages.

A broken-page test produced:

```text
failed_pages: 1
```

while the remaining book records continued to be processed.

## Limitation

This scraper is designed specifically for the Books to Scrape sandbox and its current HTML structure. Changes to the website's HTML structure could require changes to the extraction selectors.

I will not reuse this code on another site without checking its rules and terms first.

## Ethics

This project is intended for learning and demonstration on a sandbox scraping website. It uses caching, request delays, timeouts, and limited catalogue scope to avoid unnecessary requests.
