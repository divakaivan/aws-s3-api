from pydantic import Field
from pydantic import BaseModel
from datetime import datetime

# constants.py
DEFAULT_GET_FILES_PAGE_SIZE = 10
DEFAULT_GET_FILES_MIN_PAGE_SIZE = 10
DEFAULT_GET_FILES_MAX_PAGE_SIZE = 100
DEFAULT_GET_FILES_DIRECTORY = ""


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
    page_size: int = Field(
        DEFAULT_GET_FILES_PAGE_SIZE,
        ge=DEFAULT_GET_FILES_MIN_PAGE_SIZE,
        le=DEFAULT_GET_FILES_MAX_PAGE_SIZE,
    )
    directory: str = DEFAULT_GET_FILES_DIRECTORY
    page_token: str | None = None


# delete (cruD)
class DeleteFileResponse(BaseModel):
    message: str


# create/update (CrUd)
class PutFileResponse(BaseModel):
    file_path: str
    message: str
