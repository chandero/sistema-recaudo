"""
Paquete de servicios para la lógica de negocio.
"""

_SERVICE_IMPORTS = {
    "ClientService": ".client_service",
    "DocumentService": ".document_service",
    "ImportService": ".import_service",
    "ObligationService": ".obligation_service",
    "ProcessService": ".process_service",
    "UserService": ".user_service",
    "DocumentGenerationService": ".document_generation_service",
}


def __getattr__(name):
    if name not in _SERVICE_IMPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from importlib import import_module

    module = import_module(_SERVICE_IMPORTS[name], __name__)
    service = getattr(module, name)
    globals()[name] = service
    return service

__all__ = [
    "ClientService",
    "DocumentService",
    "ImportService",
    "ObligationService",
    "ProcessService",
    "UserService",
    "DocumentGenerationService"
]