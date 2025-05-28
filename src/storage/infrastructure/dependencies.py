#src/storage/infrastructure/dependencies.py
from typing import Dict, Type
from src.storage.application.storage_service import StorageService
from src.shared.config.storage_settings import StorageSettings

# Registrador de serviços
_storage_registry: Dict[str, Type[StorageService]] = {}

def register_storage(provider: str):
    def decorator(cls: Type[StorageService]):
        _storage_registry[provider] = cls
        return cls
    return decorator

def get_storage_service() -> StorageService:
    settings = StorageSettings()
    provider = settings.storage_provider

    if provider not in _storage_registry:
        raise ValueError(f"Storage provider '{provider}' não está registrado")

    return _storage_registry[provider]()  # Instância do StorageService
