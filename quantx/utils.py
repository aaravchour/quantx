"""
Shared utilities used across QuantX modules.

These are internal helpers — things like "how many qubits do I need for N items?"
that multiple modules will use. Keeping them here avoids duplication.
"""

import math


def qubits_needed(n_items: int) -> int:
    """Calculate the minimum number of qubits needed to represent n_items states.

    Qubits encode information in powers of 2: n qubits can represent 2^n states.
    So for 5 items, we need ceil(log2(5)) = 3 qubits (which gives us 8 states).

    Args:
        n_items: Number of items to encode.

    Returns:
        Number of qubits required.

    Examples:
        >>> qubits_needed(4)
        2
        >>> qubits_needed(5)
        3
        >>> qubits_needed(1)
        1
    """
    if n_items <= 0:
        raise ValueError("n_items must be positive")
    if n_items == 1:
        return 1
    return math.ceil(math.log2(n_items))


def optimal_grover_iterations(n_items: int, n_targets: int = 1) -> int:
    """Calculate the optimal number of Grover iterations.

    The magic formula: floor(pi/4 * sqrt(N/M)) where N is the search space
    size and M is the number of targets. This comes from the math of
    quantum amplitude amplification.

    Too few iterations = target not amplified enough.
    Too many iterations = amplitude "overshoots" and wraps back down.
    The sweet spot is this exact formula.

    Args:
        n_items: Total size of the search space (will be rounded up to power of 2).
        n_targets: Number of target items (usually 1).

    Returns:
        Optimal number of Grover iterations.

    Examples:
        >>> optimal_grover_iterations(4)
        1
        >>> optimal_grover_iterations(16)
        3
        >>> optimal_grover_iterations(1024)
        25
    """
    # The actual search space is the next power of 2
    n_qubits = qubits_needed(n_items)
    search_space = 2**n_qubits
    return max(1, int(math.pi / 4 * math.sqrt(search_space / n_targets)))


def next_power_of_2(n: int) -> int:
    """Return the smallest power of 2 that is >= n.

    Examples:
        >>> next_power_of_2(4)
        4
        >>> next_power_of_2(5)
        8
        >>> next_power_of_2(1)
        1
    """
    if n <= 0:
        raise ValueError("n must be positive")
    if n == 1:
        return 1
    return 2 ** math.ceil(math.log2(n))
