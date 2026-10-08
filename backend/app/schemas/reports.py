from pydantic import BaseModel


class ReportPage(BaseModel):
    items: list[dict]
    total: int
    page: int
    page_size: int
    summary: dict

