# test_local_storage_service.py
import asyncio
from pathlib import Path
from src.storage.infrastructure.local_storage_service import LocalStorageService

async def test_local_storage():
    storage = LocalStorageService("tmp_test_storage")
    file_name = "test_folder/test.txt"
    content = b"Olá, mundo!"

    # Upload
    await storage.upload(file_name, content)
    assert await storage.exists(file_name)

    # Download
    downloaded = await storage.download(file_name)
    assert downloaded == content

    # Delete
    deleted = await storage.delete(file_name)
    assert deleted
    assert not await storage.exists(file_name)

asyncio.run(test_local_storage())
