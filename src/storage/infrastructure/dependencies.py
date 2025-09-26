# src/storage/infrastructure/dependencies.py

from typing import Dict, Type, List, Callable

from src.storage.application.storage_service import StorageService
import importlib
import pkgutil
import pathlib

# Service registry
_storage_registry: Dict[str, Type[StorageService]] = {}
_plugins_loaded = False  # Ensures plugins are loaded only once

# Type alias for the factory that creates a storage service instance
StorageServiceFactory = Callable[[str], StorageService]


def register_storage(provider: str):
    """A decorator to register storage provider classes."""
    def decorator(cls: Type[StorageService]):
        _storage_registry[provider] = cls
        return cls
    return decorator


def get_available_storage_providers() -> List[str]:
    """Returns a list of all registered storage provider names."""
    _load_storage_plugins()  # Ensure all providers are registered
    return list(_storage_registry.keys())


def create_storage_service(provider: str) -> StorageService:
    """Factory function to create a storage service instance by name."""
    _load_storage_plugins()
    if provider not in _storage_registry:
        raise ValueError(f"Storage provider '{provider}' is not registered")
    return _storage_registry[provider]()


def get_storage_service_factory() -> StorageServiceFactory:
    """Dependency provider that returns the factory function itself."""
    return create_storage_service


def _load_storage_plugins():
    """Dynamically loads all storage providers in this directory."""
    global _plugins_loaded
    if _plugins_loaded:
        return

    package_path = pathlib.Path(__file__).parent
    package_name = __name__.rsplit(".", 1)[0]

    for _, module_name, _ in pkgutil.iter_modules([str(package_path)]):
        if module_name.startswith("_"):
            continue
        full_module_name = f"{package_name}.{module_name}"
        importlib.import_module(full_module_name)

    _plugins_loaded = True
