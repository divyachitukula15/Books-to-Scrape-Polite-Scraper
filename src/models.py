from pydantic import BaseModel, HttpUrl


class Book(BaseModel):
    title: str
    product_url: HttpUrl
    price_text: str | None
    price_gbp: float | None
    availability_text: str | None
    rating_text: str | None
    description: str | None
    source_page: HttpUrl
    fetched_at: str