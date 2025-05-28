# src/storage/infrastructure/s3_storage_adapter.py
from src.auth.application.auth_service import settings
from src.storage.application.storage_service import StorageService, StorageException
from typing import Optional, Union
from pathlib import Path
import logging
import aioboto3
from botocore.exceptions import ClientError
from src.shared.config.storage_settings import StorageSettings

settings = StorageSettings()


class S3StorageAdapter(StorageService):
    def __init__(
            self,
            bucket_name: str = settings.bucket_name,
            aws_access_key_id: Optional[str] = settings.access_key,
            aws_secret_access_key: Optional[str] = settings.secret_key,
            region_name: Optional[str] = None,
            endpoint_url: Optional[str] = settings.endpoint_url
    ):
        """
        S3 Storage Adapter using aioboto3 for async operations

        Args:
            bucket_name: Name of the S3 bucket
            aws_access_key_id: AWS access key (optional if using IAM roles)
            aws_secret_access_key: AWS secret key (optional if using IAM roles)
            region_name: AWS region name
            endpoint_url: Custom endpoint URL (for testing with LocalStack or MinIO)
        """
        self.bucket_name = bucket_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name
        self.endpoint_url = endpoint_url
        self.logger = logging.getLogger(__name__)

    async def _get_client(self):
        """Create an async S3 client session"""
        session = aioboto3.Session(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )
        return session.client('s3', endpoint_url=self.endpoint_url)

    async def upload(self, file_path: Union[str, Path], file: bytes) -> None:
        """Upload a file to S3 bucket"""
        try:
            async with await self._get_client() as s3:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=str(file_path),
                    Body=file
                )
            self.logger.debug(f"File uploaded to S3: s3://{self.bucket_name}/{file_path}")
        except ClientError as e:
            self.logger.error(f"S3 upload failed for {file_path}: {e}")
            raise StorageException(f"S3 upload failed for {file_path}", e)

    async def download(self, file_path: Union[str, Path]) -> Optional[bytes]:
        """Download a file from S3 bucket"""
        try:
            async with await self._get_client() as s3:
                response = await s3.get_object(
                    Bucket=self.bucket_name,
                    Key=str(file_path)
                )
                return await response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                self.logger.warning(f"File not found in S3: s3://{self.bucket_name}/{file_path}")
                return None
            self.logger.error(f"S3 download failed for {file_path}: {e}")
            raise StorageException(f"S3 download failed for {file_path}", e)

    async def delete(self, file_path: Union[str, Path]) -> bool:
        """Delete a file from S3 bucket"""
        try:
            async with await self._get_client() as s3:
                await s3.delete_object(
                    Bucket=self.bucket_name,
                    Key=str(file_path)
                )
            self.logger.info(f"File deleted from S3: s3://{self.bucket_name}/{file_path}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return False
            self.logger.error(f"S3 delete failed for {file_path}: {e}")
            raise StorageException(f"S3 delete failed for {file_path}", e)

    async def exists(self, file_path: Union[str, Path]) -> bool:
        """Check if a file exists in S3 bucket"""
        try:
            async with await self._get_client() as s3:
                await s3.head_object(
                    Bucket=self.bucket_name,
                    Key=str(file_path)
                )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            self.logger.error(f"S3 exists check failed for {file_path}: {e}")
            raise StorageException(f"S3 exists check failed for {file_path}", e)
