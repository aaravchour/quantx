"""
Grover's Search Algorithm
==========================
Finds a specific item in an unsorted database of N items using
only O(√N) queries, compared to O(N) classically.

For a 2-qubit system (4 states), Grover's algorithm finds the
marked state in just ONE iteration with 100% probability.

Steps:
  1. Initialize all qubits in superposition
  2. Apply the Oracle (marks the target state by flipping its phase)
  3. Apply the Diffusion operator (amplifies the marked state)
  4. Repeat steps 2-3 approximately √N times
  5. Measure

We search for the state |11⟩ in a 2-qubit system.
"""

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def create_oracle(target: str) -> QuantumCircuit:
    """
    Create a phase oracle that marks the target state.
    For |11⟩: uses a controlled-Z gate.
    """
    n = len(target)
    oracle = QuantumCircuit(n, name=f"Oracle(|{target}⟩)")

    # Flip qubits where target has '0' so that we can use a multi-controlled Z
    for i, bit in enumerate(reversed(target)):
        if bit == "0":
            oracle.x(i)

    # Apply multi-controlled Z (CZ for 2 qubits)
    if n == 2:
        oracle.cz(0, 1)
    else:
        # For n > 2, use a multi-controlled Z via H + MCX + H
        oracle.h(n - 1)
        oracle.mcx(list(range(n - 1)), n - 1)
        oracle.h(n - 1)

    # Undo the X flips
    for i, bit in enumerate(reversed(target)):
        if bit == "0":
            oracle.x(i)

    return oracle


def create_diffusion(n: int) -> QuantumCircuit:
    """
    Create Grover's diffusion operator (inversion about the mean).
    Amplifies the amplitude of the marked state.
    """
    diffusion = QuantumCircuit(n, name="Diffusion")

    # Apply H to all qubits
    diffusion.h(range(n))

    # Apply X to all qubits
    diffusion.x(range(n))

    # Multi-controlled Z
    if n == 2:
        diffusion.cz(0, 1)
    else:
        diffusion.h(n - 1)
        diffusion.mcx(list(range(n - 1)), n - 1)
        diffusion.h(n - 1)

    # Undo X and H
    diffusion.x(range(n))
    diffusion.h(range(n))

    return diffusion


def grovers_search(target: str, iterations: int = 1) -> QuantumCircuit:
    """Build the complete Grover's search circuit."""
    n = len(target)
    qc = QuantumCircuit(n, n)

    # Step 1: Initialize superposition
    qc.h(range(n))

    # Steps 2-3: Repeat Oracle + Diffusion
    oracle = create_oracle(target)
    diffusion = create_diffusion(n)

    for _ in range(iterations):
        qc.barrier()
        qc.compose(oracle, inplace=True)
        qc.barrier()
        qc.compose(diffusion, inplace=True)

    # Step 4: Measure
    qc.barrier()
    qc.measure(range(n), range(n))

    return qc


def run_grovers(target: str, shots: int = 1024) -> dict:
    """Run Grover's search and return measurement counts."""
    import math
    n = len(target)
    # Optimal number of iterations ≈ floor(π/4 * √N)
    N = 2 ** n
    iterations = max(1, int(math.pi / 4 * math.sqrt(N)))

    qc = grovers_search(target, iterations)
    simulator = AerSimulator()
    compiled = transpile(qc, simulator)
    result = simulator.run(compiled, shots=shots).result()
    return result.get_counts(compiled), qc, iterations


def main():
    print("=" * 50)
    print("  GROVER'S SEARCH — Quantum Database Search")
    print("=" * 50)
    print()

    target = "11"
    shots = 1024
    n = len(target)

    print(f"Searching for |{target}⟩ in {2**n} possible states")
    print(f"Classical search: up to {2**n} queries needed")
    print()

    counts, qc, iterations = run_grovers(target, shots)

    print(f"Grover iterations used: {iterations}")
    print()
    print("Circuit:")
    print(qc.draw(output="text"))
    print()

    print(f"Results ({shots} shots):")
    print("-" * 40)
    for state, count in sorted(counts.items()):
        bar = "█" * int(count / shots * 40)
        pct = count / shots * 100
        marker = " ← TARGET" if state == target else ""
        print(f"  |{state}⟩  {count:>4}  ({pct:5.1f}%)  {bar}{marker}")

    # Find the most measured state
    found = max(counts, key=counts.get)
    print()
    if found == target:
        print(f"✓ Found target |{target}⟩ with {counts[found]/shots*100:.1f}% probability!")
        print(f"  Quantum speedup: √{2**n} = {2**n**0.5:.1f}x fewer queries")
    else:
        print(f"✗ Most frequent state was |{found}⟩, expected |{target}⟩")


if __name__ == "__main__":
    main()
