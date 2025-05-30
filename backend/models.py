from pydantic import BaseModel
from typing import Dict, Union, Any


class OCRResponse(BaseModel):
    status: str
    message: str
    content: Dict[str, Any]
    extracted_text: str
