from minio import Minio
from typing import BinaryIO

class MinioClient:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool = False):
        self.client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

    def upload_file(
            self, 
            bucket_name: str, 
            object_name: str, 
            data: BinaryIO, 
            content_type: str = "application/octet-stream"
        ):
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

        data.seek(0, 2)
        size = data.tell()
        data.seek(0)

        self.client.put_object(
            bucket_name=bucket_name, 
            object_name=object_name, 
            data=data, 
            length=size,
            content_type=content_type
        )

    def download_file(
            self, 
            bucket_name: str, 
            object_name: str,
            file_path: str
        ):
        if file_path:
            self.client.fget_object(
                bucket_name=bucket_name, 
                object_name=object_name,
                file_path=file_path
            )
