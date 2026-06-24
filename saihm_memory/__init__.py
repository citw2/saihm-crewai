"""SAIHM memory for Python — CrewAI storage backend.

Route CrewAI's unified memory through SAIHM: a store you own — portable across models and
frameworks, non-custodial (sealed by a bundled Node sidecar — Python holds no key), and
provably erasable (GDPR Art. 17).

    from saihm_memory import SaihmStorageBackend   # crewai StorageBackend, SAIHM-backed
    from saihm_memory import SaihmMemoryClient      # the core client (any Python app)
"""
from .client import Memory, SaihmMemoryClient, SaihmTimeout

__all__ = ["SaihmMemoryClient", "Memory", "SaihmTimeout", "SaihmStorageBackend"]


def __getattr__(name: str):
    # Import the adapter lazily so the core client works without crewai installed.
    if name == "SaihmStorageBackend":
        from .crewai_memory import SaihmStorageBackend

        return SaihmStorageBackend
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
