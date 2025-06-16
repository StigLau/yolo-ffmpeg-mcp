from pydantic import BaseModel
from typing import Optional # For type hinting

class FileInfo(BaseModel):
    id: str
    name: str
    size: int
    extension: str

class ProcessResult(BaseModel):
    success: bool
    message: str
    output_file_id: Optional[str] = None
    logs: Optional[str] = None
