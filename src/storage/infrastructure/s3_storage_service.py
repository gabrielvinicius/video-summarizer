# src/storage/infrastructure/s3_storage_service.py
import asyncio
import boto3
from botocore.exceptions import ClientError

from src.storage.application.storage_service import StorageService, StorageException
from src.storage.infrastructure.dependencies import register_storage
from src.shared.config.storage_settings import StorageSettings

from pathlib import Path
from typing import Union, Optional, Tuple


@register_storage("s3")
class S3StorageService(StorageService):
    def __init__(self):
        self.settings = StorageSettings()
        self.client = boto3.client(
            "s3",
            aws_access_key_id=self.settings.access_key,
            aws_secret_access_key=self.settings.secret_key,
            endpoint_url=self.settings.endpoint_url,
        )
        try:
            self.client.head_bucket(Bucket=self.settings.bucket_name)
        except ClientError:
            self.client.create_bucket(Bucket=self.settings.bucket_name)

    @property
    def provider_name(self) -> str:
        return "s3"

    async def upload(self, file_path: Union[str, Path], file: bytes) -> bool:
        loop = asyncio.get_event_loop()

        def _upload():
            self.client.put_object(
                Bucket=self.settings.bucket_name,
                Key=str(file_path),
                Body=file
            )
            return True

        try:
            return await loop.run_in_executor(None, _upload)
        except Exception as e:
            raise StorageException("Error uploading to S3", e)

    async def download(self, file_path: Union[str, Path]) -> Optional[Tuple[bytes, str]]:
        loop = asyncio.get_event_loop()

        def _download():
            try:
                response = self.client.get_object(
                    Bucket=self.settings.bucket_name,
                    Key=str(file_path)
                )
                content = response["Body"].read()
                filename = str(file_path).split('/')[-1]
                return content, filename
            except self.client.exceptions.NoSuchKey:
                return None

        try:
            return await loop.run_in_executor(None, _download)
        except Exception as e:
            raise StorageException("Error downloading from S3", e)

    async def delete(self, file_path: Union[str, Path]) -> bool:
        loop = asyncio.get_event_loop()

        def _delete():
            try:
                self.client.delete_object(
                    Bucket=self.settings.bucket_name,
                    Key=str(file_path)
                )
                return True
            except self.client.exceptions.NoSuchKey:
                return False

        try:
            return await loop.run_in_executor(None, _delete)
        except Exception as e:
            raise StorageException("Error deleting from S3", e)

    async def exists(self, file_path: Union[str, Path]) -> bool:
        loop = asyncio.get_event_loop()

        def _exists():
            try:
                self.client.head_object(
                    Bucket=self.settings.bucket_name,
                    Key=str(file_path)
                )
                return True
            except self.client.exceptions.ClientError:
                return False

        try:
            return await loop.run_in_executor(None, _exists)
        except Exception as e:
            raise StorageException("Error checking existence in S3", e)
