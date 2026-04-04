"""
Custom exceptions for QuantumEasy.

Design decision: We have a base class (QuantumEasyError) and specific subclasses
for different error categories. This lets users catch broad errors with
`except QuantumEasyError` or specific ones with `except QubitLimitError`.

Every exception stores a human-readable message with actionable advice —
not just "something went wrong" but "here's what happened and how to fix it."
"""


class QuantumEasyError(Exception):
    """Base exception for all QuantumEasy errors.

    All custom exceptions inherit from this, so users can do:
        try:
            result = search(items, target)
        except QuantumEasyError as e:
            print(e)  # Always a human-readable message
    """

    pass


class QubitLimitError(QuantumEasyError):
    """Raised when the problem requires more qubits than the backend supports.

    Example:
        QubitLimitError: Your search space has 1,000,000 items, which needs 20 qubits.
        The current simulator supports up to 24 qubits. This will work but may be slow.
        Estimated time: ~45 seconds. Set force=True to skip this warning.
    """

    def __init__(self, qubits_needed: int, qubits_available: int, suggestion: str = ""):
        self.qubits_needed = qubits_needed
        self.qubits_available = qubits_available
        message = (
            f"This operation needs {qubits_needed} qubits, but the current backend "
            f"supports up to {qubits_available}."
        )
        if suggestion:
            message += f"\n{suggestion}"
        super().__init__(message)


class InvalidInputError(QuantumEasyError):
    """Raised when the user provides invalid input to a QuantumEasy function.

    Example:
        InvalidInputError: Cannot search an empty list.
        Pass a list with at least 1 item.
    """

    pass


class BackendError(QuantumEasyError):
    """Raised when there's a problem with the quantum backend.

    Example:
        BackendError: Could not connect to IBM Quantum backend 'ibm_brisbane'.
        Check your API token and internet connection.
    """

    pass


class SearchError(QuantumEasyError):
    """Raised for search-specific issues.

    Example:
        SearchError: Target 'alice' not found in the search space.
        Grover's algorithm requires the target to exist in the list.
    """

    pass
