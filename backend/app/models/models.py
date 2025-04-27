from pydantic import BaseModel, HttpUrl
from typing import Optional

class SummaryRequest(BaseModel):
    video_url: HttpUrl
    language: Optional[str] = "en"