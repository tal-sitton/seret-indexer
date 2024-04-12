from pydantic import BaseModel


class SiteInfoModel(BaseModel):
    mid: int
    url: str
    priority: float
