"""
QuantX — Quantum computing for everyone.

Use quantum algorithms without knowing quantum mechanics.

Quick start:
    >>> from quantx import search
    >>> result = search(["alice", "bob", "charlie", "diana"], target="charlie")
    >>> print(result)
    SearchResult(FOUND: 'charlie', confidence=96.5%, qubits=2, iterations=1)

Configure backend:
    >>> import quantx
    >>> quantx.set_backend("ibm_brisbane", token="your-token")
"""

__version__ = "0.1.0"

# Public API — these are what `from quantx import X` exposes
from quantx.search import search, SearchResult
from quantx.backends import set_backend, set_shots, get_backend
from quantx.exceptions import (
    QuantXError,
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
    "QuantXError",
    "QubitLimitError",
    "InvalidInputError",
    "BackendError",
    "SearchError",
]
