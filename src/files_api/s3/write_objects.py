import boto3

try:
    from mypy_boto3_s3 import S3Client
except ImportError:
    ...


def upload_s3_object(
    bucket_name: str,
    object_key: str,
    file_content: bytes,
    content_type: str | None = None,
    s3_client: S3Client | None = None,
) -> None:
    """
    Upload a file to an S3 bucket.
    """
    s3_client = s3_client or boto3.client("s3")
    content_type = content_type or "appliation/octet-stream"
    s3_client.put_object(
        Bucket=bucket_name,
        Key=object_key,
        Body=file_content,
        ContentType=content_type,
    )
