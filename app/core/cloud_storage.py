"""Cloud storage utilities for Digital Ocean Spaces."""

import logging
import os

import boto3
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class CloudStorage:
    """Digital Ocean Spaces cloud storage handler."""

    def __init__(self):
        self.client = None
        self.bucket_name = settings.DO_SPACES_BUCKET

        if settings.DO_SPACES_KEY and settings.DO_SPACES_SECRET:
            try:
                self.client = boto3.client(
                    "s3",
                    region_name=settings.DO_SPACES_REGION,
                    endpoint_url=settings.DO_SPACES_ENDPOINT,
                    aws_access_key_id=settings.DO_SPACES_KEY,
                    aws_secret_access_key=settings.DO_SPACES_SECRET,
                    use_ssl=settings.DO_SPACES_USE_SSL,
                )
                logger.info("CloudStorage client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize CloudStorage client: {e}")
        else:
            logger.warning("CloudStorage credentials missing, client not initialized")

    def is_available(self) -> bool:
        """Check if cloud storage is configured and available."""
        return self.client is not None

    def upload_file(self, file_content: bytes, file_path: str, content_type: str | None = None) -> str:
        """Upload file to Digital Ocean Spaces and return its public URL."""
        if not self.client:
            raise Exception("Cloud storage not configured")

        try:
            if not content_type:
                content_type = self._guess_content_type(file_path)

            import io

            self.client.upload_fileobj(
                io.BytesIO(file_content),
                self.bucket_name,
                file_path,
                ExtraArgs={"ACL": "public-read", "ContentType": content_type},
            )

            return f"https://{self.bucket_name}.{settings.DO_SPACES_REGION}.cdn.digitaloceanspaces.com/{file_path}"

        except ClientError as e:
            raise Exception(f"Failed to upload file to cloud storage: {str(e)}")

    def delete_file(self, file_path: str) -> bool:
        """Delete file from Digital Ocean Spaces."""
        if not self.client:
            return False

        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except ClientError:
            return False

    def _guess_content_type(self, file_path: str) -> str:
        """Guess content type based on file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        return content_types.get(ext, "application/octet-stream")


# Global instance
cloud_storage = CloudStorage()
