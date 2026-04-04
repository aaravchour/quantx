"""
Quantum search module — wraps Grover's algorithm.

This is the flagship module of QuantumEasy. A developer writes:

    from quantumeasy import search
    result = search(["alice", "bob", "charlie", "diana"], target="charlie")

...and internally, we:
    1. Validate the input
    2. Map list items to binary strings (qubit states)
    3. Build a Grover's circuit with an oracle for the target
    4. Run it on the backend
    5. Interpret the measurement results
    6. Return a friendly SearchResult object

The user never sees a gate, qubit, or circuit — unless they ask for it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, List, Optional

from qiskit import QuantumCircuit

from quantumeasy._validators import (
    validate_qubit_requirements,
    validate_search_items,
    validate_search_target,
)
from quantumeasy.backends import get_backend
from quantumeasy.utils import next_power_of_2, optimal_grover_iterations, qubits_needed


@dataclass
class SearchResult:
    """Result of a quantum search operation.

    This is what search() returns. It's a dataclass — a simple container
    with named fields. Much nicer than returning a raw dictionary.

    Attributes:
        target: The item that was searched for.
        found: Whether the quantum search found the target.
        confidence: Probability (0.0 to 1.0) that the result is correct.
        iterations: Number of Grover iterations used.
        n_qubits: Number of qubits in the circuit.
        measurements: Raw measurement counts from the quantum backend.
        circuit: The Qiskit QuantumCircuit used (for inspection).
    """

    target: Any
    found: bool
    confidence: float
    iterations: int
    n_qubits: int
    measurements: dict
    circuit: QuantumCircuit

    def __repr__(self) -> str:
        status = "FOUND" if self.found else "NOT FOUND"
        return (
            f"SearchResult({status}: {self.target!r}, "
            f"confidence={self.confidence:.1%}, "
            f"qubits={self.n_qubits}, iterations={self.iterations})"
        )

    def get_circuit(self) -> QuantumCircuit:
        """Get the raw Qiskit circuit for inspection.

        Use this to peek under the hood and see what QuantumEasy built.

        Returns:
            The Qiskit QuantumCircuit used for this search.

        Examples:
            >>> result = search(["a", "b", "c", "d"], target="c")
            >>> circuit = result.get_circuit()
            >>> print(circuit.draw())
        """
        return self.circuit

    def draw(self, output: str = "text") -> Any:
        """Draw the quantum circuit.

        Args:
            output: Drawing format — "text" for terminal, "mpl" for matplotlib.

        Returns:
            Circuit diagram (text string or matplotlib figure).

        Examples:
            >>> result = search(["a", "b", "c", "d"], target="c")
            >>> result.draw()  # Prints ASCII circuit diagram
        """
        return self.circuit.draw(output=output)


def _build_oracle(target_index: int, n_qubits: int) -> QuantumCircuit:
    """Build a phase oracle that marks the target state.

    The oracle flips the phase of the target state |target⟩ by applying
    a multi-controlled Z gate. This is the "marking" step of Grover's algorithm.

    How it works:
    - Convert the target index to binary (e.g., index 2 for 3 qubits → "010")
    - Apply X gates to qubits where the binary is "0" (so they become "1")
    - Apply a multi-controlled Z gate (flips phase only when all qubits are "1")
    - Undo the X gates

    This effectively flips the phase of ONLY the target state.

    Args:
        target_index: Index of the target item in the search space.
        n_qubits: Number of qubits in the circuit.

    Returns:
        QuantumCircuit implementing the oracle.
    """
    # Convert index to binary string, padded to n_qubits length
    target_binary = format(target_index, f"0{n_qubits}b")

    oracle = QuantumCircuit(n_qubits, name=f"Oracle(|{target_binary}⟩)")

    # Flip qubits where target bit is '0'
    # We read the binary string left-to-right, but Qiskit qubit ordering
    # is right-to-left, so we reverse it
    for i, bit in enumerate(reversed(target_binary)):
        if bit == "0":
            oracle.x(i)

    # Multi-controlled Z gate
    if n_qubits == 1:
        oracle.z(0)
    elif n_qubits == 2:
        oracle.cz(0, 1)
    else:
        # CZ = H on target + MCX + H on target
        oracle.h(n_qubits - 1)
        oracle.mcx(list(range(n_qubits - 1)), n_qubits - 1)
        oracle.h(n_qubits - 1)

    # Undo the X flips
    for i, bit in enumerate(reversed(target_binary)):
        if bit == "0":
            oracle.x(i)

    return oracle


def _build_diffusion(n_qubits: int) -> QuantumCircuit:
    """Build the Grover diffusion operator (inversion about the mean).

    This is the "amplification" step. After the oracle marks the target
    with a negative phase, the diffusion operator increases its amplitude
    while decreasing all others. It's like a mirror that reflects
    amplitudes around their average.

    The math: D = 2|s⟩⟨s| - I, where |s⟩ is the uniform superposition.

    Implementation: H → X → MCZ → X → H (on all qubits).

    Args:
        n_qubits: Number of qubits.

    Returns:
        QuantumCircuit implementing the diffusion operator.
    """
    diffusion = QuantumCircuit(n_qubits, name="Diffusion")

    diffusion.h(range(n_qubits))
    diffusion.x(range(n_qubits))

    # Multi-controlled Z
    if n_qubits == 1:
        diffusion.z(0)
    elif n_qubits == 2:
        diffusion.cz(0, 1)
    else:
        diffusion.h(n_qubits - 1)
        diffusion.mcx(list(range(n_qubits - 1)), n_qubits - 1)
        diffusion.h(n_qubits - 1)

    diffusion.x(range(n_qubits))
    diffusion.h(range(n_qubits))

    return diffusion


def _build_grover_circuit(
    target_index: int, n_qubits: int, iterations: int
) -> QuantumCircuit:
    """Build the complete Grover's search circuit.

    Structure:
        1. Hadamard all qubits → uniform superposition
        2. Repeat (Oracle → Diffusion) for `iterations` times
        3. Measure all qubits

    Args:
        target_index: Index of the target in the search space.
        n_qubits: Number of qubits.
        iterations: Number of Grover iterations.

    Returns:
        Complete QuantumCircuit ready to run.
    """
    qc = QuantumCircuit(n_qubits, n_qubits)

    # Step 1: Superposition
    qc.h(range(n_qubits))

    # Step 2: Grover iterations
    oracle = _build_oracle(target_index, n_qubits)
    diffusion = _build_diffusion(n_qubits)

    for _ in range(iterations):
        qc.barrier()
        qc.compose(oracle, inplace=True)
        qc.barrier()
        qc.compose(diffusion, inplace=True)

    # Step 3: Measure
    qc.barrier()
    qc.measure(range(n_qubits), range(n_qubits))

    return qc


def search(
    items: List[Any],
    target: Any,
    shots: Optional[int] = None,
    force: bool = False,
    auto_pad: bool = True,
) -> SearchResult:
    """Search for a target item using Grover's quantum search algorithm.

    Grover's algorithm finds an item in an unsorted collection in O(sqrt(N))
    time — a quadratic speedup over classical linear search. You provide
    a list and a target, and QuantumEasy handles all the quantum mechanics.

    Args:
        items: List of items to search through. Can be any Python objects
            (strings, numbers, etc.). Must contain at least 2 items.
        target: The item to find. Must exist in the items list.
        shots: Number of times to run the quantum circuit. More shots = more
            accurate probability estimates. Default: 1024 (from backend config).
        force: If True, skip warnings about slow operations on large inputs.
        auto_pad: If True (default), automatically pad the search space to a
            power of 2. Grover's algorithm requires this — we add dummy items
            that can never be the answer.

    Returns:
        SearchResult with the outcome, confidence score, and circuit.

    Raises:
        InvalidInputError: If items is empty or not a list.
        SearchError: If target is not in the items list.
        QubitLimitError: If the search space exceeds backend capacity.

    Examples:
        >>> from quantumeasy import search
        >>> result = search(["alice", "bob", "charlie", "diana"], target="charlie")
        >>> print(result)
        SearchResult(FOUND: 'charlie', confidence=96.5%, qubits=2, iterations=1)

        >>> result = search(list(range(100)), target=42)
        >>> print(result.confidence)
        0.953125

        >>> # Inspect the circuit
        >>> result.draw()
    """
    # === Step 1: Validate input ===
    items = validate_search_items(items)
    target_index = validate_search_target(items, target)

    # === Step 2: Calculate quantum parameters ===
    n_items = len(items)
    padded_size = next_power_of_2(n_items)
    n_qubits = qubits_needed(padded_size)

    # Check qubit limits
    backend = get_backend()
    validate_qubit_requirements(n_items, backend.max_qubits, "search", force)

    # Notify about padding if needed
    if padded_size != n_items and not auto_pad:
        from quantumeasy.exceptions import InvalidInputError

        raise InvalidInputError(
            f"Your search space has {n_items} items, which is not a power of 2.\n"
            f"Grover's algorithm needs a power-of-2 search space.\n"
            f"QuantumEasy can pad it to {padded_size} items automatically.\n"
            f"Set auto_pad=True (default) to allow this."
        )

    # === Step 3: Build the quantum circuit ===
    iterations = optimal_grover_iterations(padded_size)
    circuit = _build_grover_circuit(target_index, n_qubits, iterations)

    # === Step 4: Run on the backend ===
    counts = backend.run_circuit(circuit, shots=shots)

    # === Step 5: Interpret results ===
    # The target's binary representation
    target_binary = format(target_index, f"0{n_qubits}b")

    # How often did we measure the target state?
    total_shots = sum(counts.values())
    target_count = counts.get(target_binary, 0)
    confidence = target_count / total_shots

    # The most-measured state
    most_common = max(counts, key=counts.get)
    found = most_common == target_binary

    return SearchResult(
        target=target,
        found=found,
        confidence=confidence,
        iterations=iterations,
        n_qubits=n_qubits,
        measurements=counts,
        circuit=circuit,
    )
