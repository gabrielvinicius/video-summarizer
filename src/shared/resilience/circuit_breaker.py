# src/shared/resilience/circuit_breaker.py
from typing import Dict
from pybreaker import CircuitBreaker
import logging

logger = logging.getLogger(__name__)

# A global registry to hold circuit breaker instances
_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(service_key: str) -> CircuitBreaker:
    """
    Factory function to get a circuit breaker for a specific service.
    Creates a new one if it doesn't exist.
    """
    if service_key not in _breakers:
        # If a breaker for this service doesn't exist, create a new one.
        # fail_max=5: Open the circuit after 5 consecutive failures.
        # reset_timeout=60: Keep the circuit open for 60 seconds before trying again.
        _breakers[service_key] = CircuitBreaker(fail_max=5, reset_timeout=60)
        logger.info(f"Circuit breaker created for service: {service_key}")
    
    return _breakers[service_key]
