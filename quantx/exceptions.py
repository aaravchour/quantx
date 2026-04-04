"""
Custom exceptions for QuantX.

Design decision: We have a base class (QuantXError) and specific subclasses
for different error categories. This lets users catch broad errors with
`except QuantXError` or specific ones with `except QubitLimitError`.

Every exception stores a human-readable message with actionable advice —
not just "something went wrong" but "here's what happened and how to fix it."
"""


class QuantXError(Exception):
    """Base exception for all QuantX errors.

    All custom exceptions inherit from this, so users can do:
        try:
            result = search(items, target)
        except QuantXError as e:
            print(e)  # Always a human-readable message
    """

    pass


class QubitLimitError(QuantXError):
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


class InvalidInputError(QuantXError):
    """Raised when the user provides invalid input to a QuantX function.

    Example:
        InvalidInputError: Cannot search an empty list.
        Pass a list with at least 1 item.
    """

    pass


class BackendError(QuantXError):
    """Raised when there's a problem with the quantum backend.

    Example:
        BackendError: Could not connect to IBM Quantum backend 'ibm_brisbane'.
        Check your API token and internet connection.
    """

    pass


class SearchError(QuantXError):
    """Raised for search-specific issues.

    Example:
        SearchError: Target 'alice' not found in the search space.
        Grover's algorithm requires the target to exist in the list.
    """

    pass
