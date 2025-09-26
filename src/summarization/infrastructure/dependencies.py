from typing import Dict, Type, List, Callable
import importlib
import pkgutil
import pathlib

from src.summarization.infrastructure.interfaces import ISummarizer

# Service registry
_summarizer_registry: Dict[str, Type[ISummarizer]] = {}
_plugins_loaded = False

# Type alias for the factory
SummarizerServiceFactory = Callable[[str], ISummarizer]


def register_summarizer(provider: str):
    """A decorator to register summarizer provider classes."""
    def decorator(cls: Type[ISummarizer]):
        _summarizer_registry[provider] = cls
        return cls
    return decorator


def get_available_summarizer_providers() -> List[str]:
    """Returns a list of all registered summarizer provider names."""
    _load_summarizer_plugins()
    return list(_summarizer_registry.keys())


def create_summarizer_service(provider: str) -> ISummarizer:
    """Factory function to create a summarizer service instance by name."""
    _load_summarizer_plugins()
    if provider not in _summarizer_registry:
        raise ValueError(f"Summarizer provider '{provider}' is not registered")
    return _summarizer_registry[provider]()


def get_summarizer_service_factory() -> SummarizerServiceFactory:
    """Dependency provider that returns the factory function itself."""
    return create_summarizer_service


def _load_summarizer_plugins():
    """Dynamically loads all summarizer providers in this directory."""
    global _plugins_loaded
    if _plugins_loaded:
        return

    package_path = pathlib.Path(__file__).parent
    package_name = __name__.rsplit(".", 1)[0]

    for _, module_name, _ in pkgutil.iter_modules([str(package_path)]):
        if module_name.startswith("_") or module_name in ["dependencies", "interfaces"]:
            continue
        full_module_name = f"{package_name}.{module_name}"
        importlib.import_module(full_module_name)

    _plugins_loaded = True
