from src.storage.application.storage_service import StorageService, StorageException
from src.storage.infrastructure.dependencies import register_storage
from src.shared.config.storage_settings import StorageSettings

import aiohttp
from pathlib import Path
from typing import Union, Optional


@register_storage("s3")
class S3StorageService(StorageService):
    def __init__(self):
        self.settings = StorageSettings()
        import boto3
        self.client = boto3.client(
            "s3",
            aws_access_key_id=self.settings.access_key,
            aws_secret_access_key=self.settings.secret_key,
            endpoint_url=self.settings.endpoint_url,
        )
        self.client.create_bucket(Bucket=self.settings.bucket_name)

    async def upload(self, file_path: Union[str, Path], file: bytes) -> None:
        try:
            self.client.put_object(
                Bucket=self.settings.bucket_name,
                Key=str(file_path),
                Body=file
            )
        except Exception as e:
            raise StorageException("Erro ao fazer upload no S3", e)

    async def download(self, file_path: Union[str, Path]) -> Optional[bytes]:
        try:
            response = self.client.get_object(
                Bucket=self.settings.bucket_name,
                Key=str(file_path)
            )
            return response["Body"].read()
        except self.client.exceptions.NoSuchKey:
            return None
        except Exception as e:
            raise StorageException("Erro ao baixar do S3", e)

    async def delete(self, file_path: Union[str, Path]) -> bool:
        try:
            self.client.delete_object(
                Bucket=self.settings.bucket_name,
                Key=str(file_path)
            )
            return True
        except self.client.exceptions.NoSuchKey:
            return False
        except Exception as e:
            raise StorageException("Erro ao deletar do S3", e)

    async def exists(self, file_path: Union[str, Path]) -> bool:
        try:
            self.client.head_object(
                Bucket=self.settings.bucket_name,
                Key=str(file_path)
            )
            return True
        except self.client.exceptions.ClientError:
            return False
