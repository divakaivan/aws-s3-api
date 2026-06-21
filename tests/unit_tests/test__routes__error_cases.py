from fastapi import status
from fastapi.testclient import TestClient

from files_api.schemas import (
    DEFAULT_GET_FILES_MAX_PAGE_SIZE,
    DEFAULT_GET_FILES_MIN_PAGE_SIZE,
)
from tests.consts import TEST_BUCKET_NAME
from tests.utils import delete_s3_bucket


def test_get_nonexistant_file(client: TestClient):
    response = client.get("/v1/files/nonexistant_file.txt")
    assert response.status_code == 404
    assert response.json() == {"detail": "File not found"}


def test_head_nonexistent_file(client: TestClient):
    response = client.head("/v1/files/nonexistent_file.txt")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_nonexistent_file(client: TestClient):
    response = client.delete("/v1/files/nonexistent_file.txt")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "File not found"}


def test_get_files_invalid_page_size(client: TestClient):
    response = client.get(f"/v1/files?page_size={DEFAULT_GET_FILES_MIN_PAGE_SIZE - 1}")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    response = client.get(f"/v1/files?page_size={DEFAULT_GET_FILES_MAX_PAGE_SIZE + 1}")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_get_files_page_token_is_mutually_exclusive_with_page_size_and_directory(
    client: TestClient,
):
    response = client.get("/v1/files?page_token=token&page_size=10")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "mutually exclusive" in str(response.json())

    response = client.get("/v1/files?page_token=token&directory=dir")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "mutually exclusive" in str(response.json())

    response = client.get("/v1/files?page_token=token&page_size=10&directory=dir")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "mutually exclusive" in str(response.json())


def test_unforeseen_500_error(client: TestClient):
    delete_s3_bucket(TEST_BUCKET_NAME)

    response = client.get("/v1/files")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Internal server error"}
