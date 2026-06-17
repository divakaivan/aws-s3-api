from pydantic import BaseModel
from datetime import datetime


# read (cRud)
class FileMetadata(BaseModel):
    file_path: str
    last_modified: datetime
    size_bytes: int


# read (cRud)
class GetFilesResponse(BaseModel):
    files: list[FileMetadata]
    next_page_token: str | None


# read (cRud)
class GetFilesQueryParams(BaseModel):
    page_size: int = 10
    directory: str | None = ""
    page_token: str | None = None


# delete (cruD)
class DeleteFileResponse(BaseModel):
    message: str


# create/update (CrUd)
class PutFileResponse(BaseModel):
    file_path: str
    message: str
