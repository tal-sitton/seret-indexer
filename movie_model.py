from datetime import datetime

from pydantic import BaseModel


class MovieModel(BaseModel):
    id: int
    url: str
    priority: float

    name: str
    english_name: str
    keywords: list[str]
    description: str
    year: int | None
    premiere: datetime
    scrape_date: datetime
