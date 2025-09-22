# src/shared/infrastructure/logging_config.py
import logging
import structlog
from structlog.types import EventDict, WrappedLogger
from typing import Any
import sys

def drop_color_message_key(_, __, event_dict: EventDict) -> EventDict:
    """
    Remover a chave `color_message` do event dict, pois é usada apenas para console.
    """
    event_dict.pop("color_message", None)
    return event_dict

def add_service_context(_, __, event_dict: EventDict) -> EventDict:
    """
    Adiciona contexto global ao log (ex: nome do serviço).
    """
    event_dict["service"] = "video-summarizer"
    return event_dict

def configure_logging():
    """
    Configura o logging estruturado com structlog.
    """
    # Configuração do logging padrão
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Configuração do structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            drop_color_message_key,
            add_service_context,
            # Renderizador para produção (JSON)
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

# Configura o logging ao importar este módulo
configure_logging()