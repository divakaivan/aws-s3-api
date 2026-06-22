"""
Load/e2e test for the Files API.

Note, if you ever want to incorporate AWS SigV4 auth, it is straightforward. Reference
this SO answer: https://stackoverflow.com/questions/74002094/aws-authentication-in-locust-io-python
"""

import random

from locust import (
    HttpUser,
    between,
    task,
)


class FilesAPIUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def file_operations_flow(self):
        file_path = f"test_file_{random.randint(1000, 9999)}.txt"
        file = b"This is a test file content."

        # 0. List files
        self.client.get("/v1/files", name="List Files")

        # 1. Upload file
        files = {"file": (file_path, file, "text/plain")}
        self.client.put(f"/v1/files/{file_path}", files=files, name="Upload File")

        # 2. Describe the file (HEAD request)
        self.client.head(f"/v1/files/{file_path}", name="Describe File")

        # 3. List files again
        self.client.get("/v1/files", name="List Files (After Upload)")

        # 4. Download the file
        self.client.get(f"/v1/files/{file_path}", name="Download File")

        # 5. Delete the file
        self.client.delete(f"/v1/files/{file_path}", name="Delete File")
