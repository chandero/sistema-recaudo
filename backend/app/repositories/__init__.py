"""
Paquete de repositorios para el patrón Repository.
"""

_REPOSITORY_IMPORTS = {
    "BaseRepository": ".base",
    "ClientRepository": ".client",
    "ObligationRepository": ".obligation",
    "DocumentRepository": ".document",
    "ProcessRepository": ".process",
    "UserRepository": ".user",
    "ImportBatchRepository": ".import_batch",
}


def __getattr__(name):
    if name not in _REPOSITORY_IMPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from importlib import import_module

    module = import_module(_REPOSITORY_IMPORTS[name], __name__)
    repository = getattr(module, name)
    globals()[name] = repository
    return repository

__all__ = [
    "BaseRepository",
    "ClientRepository",
    "ObligationRepository",
    "DocumentRepository",
    "ProcessRepository",
    "UserRepository",
    "ImportBatchRepository"
]