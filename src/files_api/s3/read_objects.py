from mypy_boto3_s3.type_defs import ListObjectsOutputTypeDef
import boto3

try:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_s3.type_defs import (
        GetObjectOutputTypeDef,
        ObjectTypeDef,
    )
except ImportError:
    ...

DEFAULT_MAX_KEYS = 1_000


def object_exists_in_s3(
    bucket_name: str, object_key: str, s3_client: S3Client | None = None
) -> bool:
    """
    Check if an object exists in the S3 bucket using head_object.
    """
    s3_client = s3_client or boto3.client("s3")
    try:
        s3_client.head_object(Bucket=bucket_name, Key=object_key)
        return True
    except s3_client.exceptions.ClientError as err:
        error_code = err.response["Error"]["Code"]
        if error_code == "404":
            return False
        return


def fetch_s3_object(
    bucket_name: str,
    object_key: str,
    s3_client: S3Client | None = None,
) -> GetObjectOutputTypeDef:
    """
    Fetch metadata of an object in the S3 bucket.
    """
    s3_client = s3_client or boto3.client("s3")
    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    return response


def fetch_s3_objects_using_page_token(
    bucket_name: str,
    continuation_token: str,
    max_keys: int | None = None,
    s3_client: S3Client | None = None,
) -> tuple[list[ObjectTypeDef], str | None]:
    """
    Fetch list of object keys and their metadata using a continuation token.
    """
    s3_client = s3_client or boto3.client("s3")
    response: ListObjectsOutputTypeDef = s3_client.list_objects_v2(
        Bucket=bucket_name,
        ContinuationToken=continuation_token,
        MaxKeys=max_keys or DEFAULT_MAX_KEYS,
    )
    files: list[ObjectTypeDef] = response.get("Contents", [])
    next_continuation_token: str | None = response.get("NextContinuationToken")
    return files, next_continuation_token


def fetch_s3_objects_metadata(
    bucket_name: str,
    prefix: str | None = None,
    max_keys: int | None = DEFAULT_MAX_KEYS,
    s3_client: S3Client | None = None,
) -> tuple[list[ObjectTypeDef], str | None]:
    """
    Fetch list of object keys and their metadata.
    """
    s3_client = s3_client or boto3.client("s3")
    response = s3_client.list_objects_v2(
        Bucket=bucket_name, Prefix=prefix or "", MaxKeys=max_keys
    )
    files: list[ObjectTypeDef] = response.get("Contents", [])
    next_page_token: str | None = response.get("NextContinuationToken")

    return files, next_page_token
