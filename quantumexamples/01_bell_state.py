"""
Bell State — Quantum Entanglement
==================================
Creates a maximally entangled pair of qubits (a Bell state).
When measured, both qubits always collapse to the same value:
either |00⟩ or |11⟩, each with ~50% probability.

This is the quantum computing "Hello World".

Circuit:
  q0: ─[H]──●──[M]
             │
  q1: ──────⊕──[M]
"""

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def create_bell_state() -> QuantumCircuit:
    """Build a 2-qubit Bell state circuit."""
    qc = QuantumCircuit(2, 2)

    # Put qubit 0 into superposition
    qc.h(0)

    # Entangle qubit 0 and qubit 1 with a CNOT gate
    qc.cx(0, 1)

    # Measure both qubits
    qc.measure([0, 1], [0, 1])

    return qc


def run_bell_state(shots: int = 1024) -> dict:
    """Simulate the Bell state circuit and return measurement counts."""
    qc = create_bell_state()
    simulator = AerSimulator()
    compiled = transpile(qc, simulator)
    result = simulator.run(compiled, shots=shots).result()
    counts = result.get_counts(compiled)
    return counts


def main():
    print("=" * 50)
    print("  BELL STATE — Quantum Entanglement Demo")
    print("=" * 50)
    print()

    qc = create_bell_state()
    print("Circuit:")
    print(qc.draw(output="text"))
    print()

    shots = 1024
    counts = run_bell_state(shots)

    print(f"Results ({shots} shots):")
    print("-" * 30)
    for state, count in sorted(counts.items()):
        bar = "█" * int(count / shots * 40)
        pct = count / shots * 100
        print(f"  |{state}⟩  {count:>4}  ({pct:5.1f}%)  {bar}")

    print()
    print("✓ Only |00⟩ and |11⟩ appear — the qubits are entangled!")
    print("  Measuring one qubit instantly determines the other.")


if __name__ == "__main__":
    main()
