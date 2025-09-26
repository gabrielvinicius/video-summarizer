# src/storage/application/storage_service.py
from abc import ABC, abstractmethod, property_method
from typing import Optional, Union, Tuple
from pathlib import Path


class StorageService(ABC):
    """
    Abstract base class defining the interface for storage services.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the name of the storage provider (e.g., 'local', 's3')."""
        pass

    @abstractmethod
    async def upload(self, file_path: Union[str, Path], file: bytes) -> bool:
        """Stores a file in the storage system."""
        pass

    @abstractmethod
    async def download(self, file_path: Union[str, Path]) -> Optional[Tuple[bytes, str]]:
        """Retrieves a file from the storage system."""
        pass

    @abstractmethod
    async def delete(self, file_path: Union[str, Path]) -> bool:
        """Deletes a file from the storage system."""
        pass

    @abstractmethod
    async def exists(self, file_path: Union[str, Path]) -> bool:
        """Checks if a file exists in the storage system."""
        pass


class StorageException(Exception):
    """Custom exception for storage-related errors"""

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.original_exception = original_exception
        self.message = message

    def __str__(self):
        if self.original_exception:
            return f"{self.message} (Original: {str(self.original_exception)})"
        return self.message
