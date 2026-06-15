from datetime import datetime

from fastapi import (
    FastAPI,
    Response,
    UploadFile,
)
from src.files_api.s3.write_objects import upload_s3_object
from pydantic import BaseModel

S3_BUCKET_NAME = "some-bucket"

APP = FastAPI()


# read (cRud)
class FileMetadata(BaseModel):
    file_path: str
    last_modified: datetime
    size_bytes: int


@APP.put("/files/{file_path:path}")
async def upload_file(file_path: str, file: UploadFile, response: Response):
    """Upload a file."""
    file_content: bytes = await file.read()
    upload_s3_object(
        bucket_name=S3_BUCKET_NAME,
        object_key=file_path,
        content_type=file.content_type,
        file_content=file_content,
    )


@APP.get("/files")
async def list_files(
    query_params=...,
):
    """List files with pagination."""
    ...


@APP.head("/files/{file_path:path}")
async def get_file_metadata(file_path: str, response: Response) -> Response:
    """Retrieve file metadata.

    Note: by convention, HEAD requests MUST NOT return a body in the response.
    """
    return


@APP.get("/files/{file_path:path}")
async def get_file(
    file_path: str,
):
    """Retrieve a file."""
    ...


@APP.delete("/files/{file_path:path}")
async def delete_file(
    file_path: str,
    response: Response,
) -> Response:
    """Delete a file.

    NOTE: DELETE requests MUST NOT return a body in the response."""
    return


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(APP, host="0.0.0.0", port=8000)
