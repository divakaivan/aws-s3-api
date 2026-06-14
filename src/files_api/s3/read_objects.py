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
    return


def fetch_s3_object(
    bucket_name: str,
    object_key: str,
    s3_client: S3Client | None = None,
) -> GetObjectOutputTypeDef:
    """
    Fetch metadata of an object in the S3 bucket.
    """
    return


def fetch_s3_objects_using_page_token(
    bucket_name: str,
    continuation_token: str,
    max_keys: int | None = None,
    s3_client: S3Client | None = None,
) -> tuple[list[ObjectTypeDef], str | None]:
    """
    Fetch list of object keys and their metadata using a continuation token.
    """
    return


def fetch_s3_objects_metadata(
    bucket_name: str,
    prefix: str | None = None,
    max_keys: int | None = DEFAULT_MAX_KEYS,
    s3_client: S3Client | None = None,
) -> tuple[list[ObjectTypeDef], str | None]:
    """
    Fetch list of object keys and their metadata.
    """
    return
