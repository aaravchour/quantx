"""
Input validation helpers (internal module).

The underscore prefix tells other developers: "don't import this directly."
These functions validate user input and raise helpful errors BEFORE we
waste time building quantum circuits with bad data.

Design principle: "Fail fast, fail clearly." It's much better to catch
a problem in line 1 of search() than to get a cryptic Qiskit error
50 lines deep in the circuit construction.
"""

from typing import Any, List

from quantumeasy.exceptions import InvalidInputError, QubitLimitError
from quantumeasy.utils import next_power_of_2, qubits_needed


def validate_search_items(items: Any) -> list:
    """Validate and normalise the items list for search.

    Args:
        items: The search space provided by the user.

    Returns:
        A validated list of items.

    Raises:
        InvalidInputError: If items is not a list, is empty, etc.
    """
    if not isinstance(items, (list, tuple)):
        raise InvalidInputError(
            f"Expected a list or tuple of items, but got {type(items).__name__}.\n"
            f"Example: search(['alice', 'bob', 'charlie'], target='bob')"
        )

    items = list(items)

    if len(items) == 0:
        raise InvalidInputError(
            "Cannot search an empty list.\n"
            "Pass a list with at least 1 item."
        )

    if len(items) == 1:
        raise InvalidInputError(
            "Your search space only has 1 item — no need for a quantum search!\n"
            "The answer is obviously the only item in the list."
        )

    return items


def validate_search_target(items: list, target: Any) -> int:
    """Validate that the target exists in the items list.

    Args:
        items: The validated search space.
        target: The item to search for.

    Returns:
        The index of the target in the items list.

    Raises:
        SearchError: If the target is not in the list.
    """
    from quantumeasy.exceptions import SearchError

    if target not in items:
        # Show a preview of what IS in the list to help the user
        preview = items[:5]
        preview_str = ", ".join(repr(x) for x in preview)
        suffix = f", ... ({len(items)} items total)" if len(items) > 5 else ""
        raise SearchError(
            f"Target {target!r} is not in the search space.\n"
            f"Grover's algorithm requires the target to exist in the list.\n"
            f"Your list contains: [{preview_str}{suffix}]"
        )

    return items.index(target)


def validate_qubit_requirements(
    n_items: int,
    backend_max_qubits: int,
    operation: str = "search",
    force: bool = False,
) -> int:
    """Check that the problem fits within the backend's qubit limit.

    Args:
        n_items: Number of items in the problem.
        backend_max_qubits: Maximum qubits the current backend supports.
        operation: Name of the operation (for error messages).
        force: If True, skip the warning for slow-but-possible operations.

    Returns:
        Number of qubits that will be used.

    Raises:
        QubitLimitError: If the problem exceeds the backend's capacity.
    """
    n_qubits = qubits_needed(n_items)

    if n_qubits > backend_max_qubits:
        padded = next_power_of_2(n_items)
        raise QubitLimitError(
            qubits_needed=n_qubits,
            qubits_available=backend_max_qubits,
            suggestion=(
                f"Your {operation} space has {n_items:,} items, which needs "
                f"{n_qubits} qubits (to encode {padded:,} states).\n"
                f"The current backend supports up to {backend_max_qubits} qubits.\n"
                f"Try reducing your input size or switching to a more powerful backend:\n"
                f"  quantumeasy.set_backend('ibm_brisbane', token='your-token')"
            ),
        )

    # Warn (but don't block) for large but possible operations
    SLOW_THRESHOLD = 16  # 16+ qubits gets noticeably slow on a simulator
    if n_qubits >= SLOW_THRESHOLD and not force:
        import warnings

        est_seconds = 2 ** (n_qubits - 10)  # Rough heuristic
        warnings.warn(
            f"This {operation} uses {n_qubits} qubits ({2**n_qubits:,} states). "
            f"It will work but may take ~{est_seconds:.0f} seconds on the simulator. "
            f"Pass force=True to suppress this warning.",
            stacklevel=3,
        )

    return n_qubits
