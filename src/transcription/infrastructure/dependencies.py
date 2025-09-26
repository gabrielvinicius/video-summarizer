from typing import Dict, Type, List, Callable
import importlib
import pkgutil
import pathlib

from src.transcription.infrastructure.interfaces import ISpeechRecognition
from src.transcription.infrastructure.transcription_repository import TranscriptionRepository

# Service registry
_speech_recognition_registry: Dict[str, Type[ISpeechRecognition]] = {}
_plugins_loaded = False

# Type alias for the factory that creates a speech recognition service instance
SpeechRecognitionServiceFactory = Callable[[str], ISpeechRecognition]


def register_speech_recognition(provider: str):
    """A decorator to register speech recognition provider classes."""
    def decorator(cls: Type[ISpeechRecognition]):
        _speech_recognition_registry[provider] = cls
        return cls
    return decorator


def get_available_speech_recognition_providers() -> List[str]:
    """Returns a list of all registered speech recognition provider names."""
    _load_speech_recognition_plugins()
    return list(_speech_recognition_registry.keys())


def create_speech_recognition_service(provider: str) -> ISpeechRecognition:
    """Factory function to create a speech recognition service instance by name."""
    _load_speech_recognition_plugins()
    if provider not in _speech_recognition_registry:
        raise ValueError(f"Speech recognition provider '{provider}' is not registered")
    return _speech_recognition_registry[provider]()


def get_speech_recognition_service_factory() -> SpeechRecognitionServiceFactory:
    """Dependency provider that returns the factory function itself."""
    return create_speech_recognition_service


async def get_transcription_repository(db: AsyncSession) -> TranscriptionRepository | None:
    if db:
        return TranscriptionRepository(db)
    return None


def _load_speech_recognition_plugins():
    """Dynamically loads all speech recognition providers in this directory."""
    global _plugins_loaded
    if _plugins_loaded:
        return

    package_path = pathlib.Path(__file__).parent
    package_name = __name__.rsplit(".", 1)[0]

    for _, module_name, _ in pkgutil.iter_modules([str(package_path)]):
        if module_name.startswith("_") or module_name == "dependencies" or module_name == "interfaces":
            continue
        full_module_name = f"{package_name}.{module_name}"
        importlib.import_module(full_module_name)

    _plugins_loaded = True
