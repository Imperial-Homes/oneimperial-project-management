"""Cloud storage utilities for Digital Ocean Spaces."""

import logging
import os
from urllib.parse import unquote, urlparse

import boto3
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)

# Key prefixes this service may sign or store: its own uploads (project/progress-reports/,
# project/site-visits/) and handover letters uploaded through CRM (crm/legal-documents/).
# The bucket also holds private DB backups under backups/; never add that prefix.
SIGNABLE_PREFIXES = ("project/", "crm/legal-documents/")


def is_signable_key(key: str) -> bool:
    """Check that a key is under an allowlisted prefix and has no dot segments."""
    if not key.startswith(SIGNABLE_PREFIXES):
        return False
    return not any(part in (".", "..") for part in key.split("/"))


def _key_prefix(key: str) -> str:
    """Top-level folder of a key, for logging without exposing the full key."""
    return key.split("/", 1)[0] + "/"


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
        """Upload a private file to Digital Ocean Spaces and return its CDN URL.

        The object is private, so the returned URL is only a stored reference;
        use presign_stored() to get a readable link.
        """
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
                ExtraArgs={"ContentType": content_type},
            )

            return f"https://{self.bucket_name}.{settings.DO_SPACES_REGION}.cdn.digitaloceanspaces.com/{file_path}"

        except ClientError as e:
            raise Exception(f"Failed to upload file to cloud storage: {str(e)}")

    def generate_presigned_url(self, file_path: str, expiration: int = 3600) -> str | None:
        """Generate a presigned GET URL for a file, or None if cloud storage is not available."""
        if not self.client:
            return None

        try:
            return self.client.generate_presigned_url(
                "get_object", Params={"Bucket": self.bucket_name, "Key": file_path}, ExpiresIn=expiration
            )
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {file_path}: {e}")
            return None

    def key_from_reference(self, value: str | None) -> str | None:
        """Return the object key for a stored file reference, or None if it is not in our bucket.

        Accepts a bare key (must contain a "/" folder prefix and not start with "/"),
        a virtual-host URL (origin or CDN, e.g.
        https://{bucket}.lon1.cdn.digitaloceanspaces.com/<key>) or a path-style URL
        (https://<region>.digitaloceanspaces.com/{bucket}/<key>). Query strings
        (e.g. from old presigned URLs) are dropped.
        """
        if not value or not value.strip():
            return None

        value = value.strip()
        parsed = urlparse(value)

        if not parsed.scheme and not parsed.netloc:
            # Plain filenames and absolute local paths are not keys in our bucket
            if "/" in value and not value.startswith("/"):
                return value
            return None

        if parsed.scheme != "https" or not parsed.hostname:
            return None

        host = parsed.hostname
        path = unquote(parsed.path).lstrip("/")

        if not host.endswith(".digitaloceanspaces.com"):
            return None

        if host.startswith(f"{self.bucket_name}."):
            return path or None

        bucket_prefix = f"{self.bucket_name}/"
        if host.count(".") == 2 and path.startswith(bucket_prefix):
            return path[len(bucket_prefix) :] or None

        return None

    def presign_stored(self, value: str | None, expiration: int = 3600) -> str | None:
        """Return a fresh presigned URL for a stored file reference, or the value unchanged.

        References to our bucket outside SIGNABLE_PREFIXES return None.
        """
        try:
            key = self.key_from_reference(value)
            if key and not is_signable_key(key):
                logger.warning(f"Refusing to presign key outside allowed prefixes: {_key_prefix(key)}")
                return None
            if key and self.client:
                url = self.generate_presigned_url(key, expiration)
                if url:
                    return url
        except Exception as e:
            logger.error(f"Failed to presign stored file reference: {e}")
        return value

    def normalize_reference(self, value):
        """Return the bare key for a URL to our bucket (public or presigned), else the value unchanged.

        Used on write so the DB stores keys, not expiring presigned links. Raises
        ValueError for a reference to our bucket outside SIGNABLE_PREFIXES.
        """
        if not isinstance(value, str):
            return value

        key = self.key_from_reference(value)
        if not key:
            return value
        if not is_signable_key(key):
            raise ValueError("File reference is not allowed")
        return key if value.startswith("http") else value

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
