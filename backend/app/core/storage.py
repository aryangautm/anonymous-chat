import tempfile
import os
from pathlib import Path
from typing import Optional, BinaryIO
from contextlib import contextmanager

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config


class S3Client:
    def __init__(
        self,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
        region: str = "us-east-1",
    ):
        self.bucket_name = bucket_name

        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region,
            config=Config(
                signature_version="s3v4",
                retries={"max_attempts": 3, "mode": "adaptive"},
            ),
        )

    def download_file(self, key: str, local_path: str) -> None:
        """Download a file from S3 to local path."""
        try:
            self.client.download_file(self.bucket_name, key, local_path)
        except ClientError as e:
            raise Exception(f"Failed to download file {key}: {str(e)}")

    def upload_file(self, local_path: str, key: str) -> None:
        """Upload a file from local path to S3."""
        try:
            self.client.upload_file(local_path, self.bucket_name, key)
        except ClientError as e:
            raise Exception(f"Failed to upload file {key}: {str(e)}")

    def upload_fileobj(self, file_obj: BinaryIO, key: str) -> None:
        """Upload a file object to S3."""
        try:
            self.client.upload_fileobj(file_obj, self.bucket_name, key)
        except ClientError as e:
            raise Exception(f"Failed to upload file object {key}: {str(e)}")

    def delete_file(self, key: str) -> None:
        """Delete a file from S3."""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
        except ClientError as e:
            raise Exception(f"Failed to delete file {key}: {str(e)}")

    def file_exists(self, key: str) -> bool:
        """Check if a file exists in S3."""
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False

    def get_file_url(self, key: str, expiration: int = 3600) -> str:
        """Generate a presigned URL for the file."""
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expiration,
            )
            return url
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL for {key}: {str(e)}")

    @contextmanager
    def download_to_temp(self, key: str, suffix: Optional[str] = None):
        """
        Download a file to a temporary location and yield the path.
        Automatically cleans up the temp file after use.
        """
        if suffix is None:
            suffix = Path(key).suffix

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_path = temp_file.name
        temp_file.close()

        try:
            self.download_file(key, temp_path)
            yield temp_path
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


_s3_client_instance: Optional[S3Client] = None


def get_s3_client() -> S3Client:
    """Get or create singleton S3 client instance."""
    global _s3_client_instance

    if _s3_client_instance is None:
        from .config import settings

        _s3_client_instance = S3Client(
            endpoint_url=settings.AWS_S3_INTERNAL_ENDPOINT,
            access_key_id=settings.AWS_ACCESS_KEY_ID,
            secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            bucket_name=settings.AWS_S3_BUCKET_NAME,
            region=settings.AWS_REGION,
        )

    return _s3_client_instance
