"""
QuantumEasy — Quantum computing for everyone.

Use quantum algorithms without knowing quantum mechanics.

Quick start:
    >>> from quantumeasy import search
    >>> result = search(["alice", "bob", "charlie", "diana"], target="charlie")
    >>> print(result)
    SearchResult(FOUND: 'charlie', confidence=96.5%, qubits=2, iterations=1)

Configure backend:
    >>> import quantumeasy
    >>> quantumeasy.set_backend("ibm_brisbane", token="your-token")
"""

__version__ = "0.1.0"

# Public API — these are what `from quantumeasy import X` exposes
from quantumeasy.search import search, SearchResult
from quantumeasy.backends import set_backend, set_shots, get_backend
from quantumeasy.exceptions import (
    QuantumEasyError,
    QubitLimitError,
    InvalidInputError,
    BackendError,
    SearchError,
)

__all__ = [
    # Core functions
    "search",
    # Configuration
    "set_backend",
    "set_shots",
    "get_backend",
    # Result types
    "SearchResult",
    # Exceptions (users may want to catch these)
    "QuantumEasyError",
    "QubitLimitError",
    "InvalidInputError",
    "BackendError",
    "SearchError",
]
