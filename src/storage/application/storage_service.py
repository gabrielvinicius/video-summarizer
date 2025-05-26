# src/storage/application/storage_service.py
from abc import ABC, abstractmethod
from typing import Optional, Union
from pathlib import Path
import logging


class StorageService(ABC):
    """
    Abstract base class defining the interface for storage services.
    Concrete implementations should handle specific storage backends.
    """

    @abstractmethod
    async def upload(self, file_path: Union[str, Path], file: bytes) -> None:
        """
        Store a file in the storage system.

        Args:
            file_path: Destination path for the file (relative to storage root)
            file: File content as bytes

        Raises:
            StorageException: If the operation fails
        """
        pass

    @abstractmethod
    async def download(self, file_path: Union[str, Path]) -> Optional[bytes]:
        """
        Retrieve a file from the storage system.

        Args:
            file_path: Path to the file (relative to storage root)

        Returns:
            File content as bytes, or None if file doesn't exist

        Raises:
            StorageException: If the operation fails (except for missing files)
        """
        pass

    @abstractmethod
    async def delete(self, file_path: Union[str, Path]) -> bool:
        """
        Delete a file from the storage system.

        Args:
            file_path: Path to the file (relative to storage root)

        Returns:
            True if file was deleted, False if file didn't exist

        Raises:
            StorageException: If the operation fails
        """
        pass

    @abstractmethod
    async def exists(self, file_path: Union[str, Path]) -> bool:
        """
        Check if a file exists in the storage system.

        Args:
            file_path: Path to the file (relative to storage root)

        Returns:
            True if file exists, False otherwise
        """
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