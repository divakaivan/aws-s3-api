from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from loguru import logger

from files_api.route_handler import RouteHandler
from files_api.s3.delete_objects import delete_s3_object
from files_api.s3.read_objects import (
    fetch_s3_object,
    fetch_s3_objects_metadata,
    fetch_s3_objects_using_page_token,
    object_exists_in_s3,
)
from files_api.s3.write_objects import upload_s3_object
from files_api.schemas import (
    FileMetadata,
    GetFilesQueryParams,
    GetFilesResponse,
    PutFileResponse,
)

ROUTER = APIRouter(
    tags=["Files"],
    route_class=RouteHandler,
)


@ROUTER.put(
    "/v1/files/{file_path:path}",
    responses={
        status.HTTP_200_OK: {"model": PutFileResponse},
        status.HTTP_201_CREATED: {"model": PutFileResponse},
    },
)
async def upload_file(
    request: Request, file_path: str, file: UploadFile, response: Response
) -> PutFileResponse:
    """Upload a file."""
    file_content: bytes = await file.read()
    s3_bucket_name = request.app.state.settings.s3_bucket_name

    object_already_exists = object_already_exists = object_exists_in_s3(
        bucket_name=s3_bucket_name, object_key=file_path
    )
    logger.debug("object_already_exists: {exists}", exists=object_already_exists)
    if object_already_exists:
        response_message = f"Existing file updated at path: /{file_path}"
        response.status_code = status.HTTP_200_OK
    else:
        response_message = f"New file uploaded at path: /{file_path}"
        response.status_code = status.HTTP_201_CREATED

    logger.debug("trying to upload file to s3: {file_path}", file_path=file_path)
    upload_s3_object(
        bucket_name=s3_bucket_name,
        object_key=file_path,
        content_type=file.content_type,
        file_content=file_content,
    )

    logger.info(response_message)

    return PutFileResponse(file_path=file_path, message=response_message)


@ROUTER.get("/v1/files")
async def list_files(
    request: Request,
    query_params: GetFilesQueryParams = Depends(),
) -> GetFilesResponse:
    """List files with pagination."""
    s3_bucket_name = request.app.state.settings.s3_bucket_name
    if query_params.page_token:
        files, next_page_token = fetch_s3_objects_using_page_token(
            bucket_name=s3_bucket_name,
            continuation_token=query_params.page_token,
            max_keys=query_params.page_size,
        )
    else:
        files, next_page_token = fetch_s3_objects_metadata(
            bucket_name=s3_bucket_name,
            prefix=query_params.directory,
            max_keys=query_params.page_size,
        )
    logger.debug("query_params.page_token: {exists}", exists=query_params.page_token)

    file_metadata_objs = [
        FileMetadata(
            file_path=f"{item['Key']}",
            last_modified=item["LastModified"],
            size_bytes=item["Size"],
        )
        for item in files
    ]
    logger.info("items returned: {count}", count=len(file_metadata_objs))
    return GetFilesResponse(
        files=file_metadata_objs,
        next_page_token=next_page_token if next_page_token else None,
    )


@ROUTER.head(
    "/v1/files/{file_path:path}",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "File not found for the given `file_path`.",
        },
        status.HTTP_200_OK: {
            "headers": {
                "Content-Type": {
                    "description": "The [MIME type](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types) of the file.",
                    "example": "text/plain",
                    "schema": {"type": "string"},
                },
                "Content-Length": {
                    "description": "The size of the file in bytes.",
                    "example": 512,
                    "schema": {"type": "integer"},
                },
                "Last-Modified": {
                    "description": "The last modified date of the file.",
                    "example": "Thu, 01 Jan 2022 00:00:00 GMT",
                    "schema": {"type": "string", "format": "date-time"},
                },
            }
        },
    },
)
async def get_file_metadata(
    request: Request, file_path: str, response: Response
) -> Response:
    """Retrieve file metadata.

    Note: by convention, HEAD requests MUST NOT return a body in the response.
    """
    s3_bucket_name = request.app.state.settings.s3_bucket_name

    object_exists = object_exists_in_s3(
        bucket_name=s3_bucket_name, object_key=file_path
    )
    if not object_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )

    get_object_response = fetch_s3_object(s3_bucket_name, object_key=file_path)
    response.headers["Content-Type"] = get_object_response["ContentType"]
    response.headers["Content-Length"] = str(get_object_response["ContentLength"])
    response.headers["Last-Modified"] = get_object_response["LastModified"].strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )
    response.status_code = status.HTTP_200_OK
    return response


@ROUTER.get(
    "/v1/files/{file_path:path}",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "File not found for the given `file_path`.",
        },
        status.HTTP_200_OK: {
            "description": "The file content.",
            "content": {
                "application/octet-stream": {
                    "schema": {"type": "string", "format": "binary"},
                },
            },
        },
    },
)
async def get_file(
    request: Request,
    file_path: str,
) -> StreamingResponse:
    """Retrieve a file."""
    s3_bucket_name = request.app.state.settings.s3_bucket_name

    logger.debug("fetching file from s3")
    object_exists = object_exists_in_s3(
        bucket_name=s3_bucket_name, object_key=file_path
    )
    if not object_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    get_object_response = fetch_s3_object(s3_bucket_name, object_key=file_path)
    return StreamingResponse(
        content=get_object_response["Body"],
        media_type=get_object_response["ContentType"],
    )


@ROUTER.delete(
    "/v1/files/{file_path:path}",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "File not found for the given `file_path`.",
        },
        status.HTTP_204_NO_CONTENT: {
            "description": "File deleted successfully.",
        },
    },
)
async def delete_file(
    request: Request,
    file_path: str,
    response: Response,
) -> Response:
    """Delete a file.

    NOTE: DELETE requests MUST NOT return a body in the response."""
    s3_bucket_name = request.app.state.settings.s3_bucket_name

    object_exists = object_exists_in_s3(
        bucket_name=s3_bucket_name, object_key=file_path
    )
    if not object_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    delete_s3_object(s3_bucket_name, object_key=file_path)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
