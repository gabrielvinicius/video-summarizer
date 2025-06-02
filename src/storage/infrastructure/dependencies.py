# src/storage/infrastructure/dependencies.py

from typing import Dict, Type

from dotenv import load_dotenv

from src.storage.application.storage_service import StorageService
from src.shared.config.storage_settings import StorageSettings
import importlib
import pkgutil
import pathlib

# Registrador de serviços
_storage_registry: Dict[str, Type[StorageService]] = {}
_plugins_loaded = False  # Garante que plugins só sejam carregados uma vez


def register_storage(provider: str):
    def decorator(cls: Type[StorageService]):
        _storage_registry[provider] = cls
        return cls
    return decorator


def get_storage_service() -> StorageService:
    load_dotenv()
    _load_storage_plugins()  # Lazy-load dos providers
    settings = StorageSettings()
    provider = settings.provider

    if provider not in _storage_registry:
        raise ValueError(f"Storage provider '{provider}' não está registrado")

    return _storage_registry[provider]()  # Cria instância do provider


def _load_storage_plugins():
    global _plugins_loaded
    if _plugins_loaded:
        return

    package_path = pathlib.Path(__file__).parent
    package_name = __name__.rsplit(".", 1)[0]  # "storage.infrastructure"

    for _, module_name, _ in pkgutil.iter_modules([str(package_path)]):
        if module_name.startswith("_"):
            continue  # Evita importar arquivos como __init__.py
        full_module_name = f"{package_name}.{module_name}"
        importlib.import_module(full_module_name)

    _plugins_loaded = True
