"""
Deutsch-Jozsa Algorithm
========================
Determines whether a black-box function f(x) is:
  • Constant  — returns the same value for all inputs
  • Balanced  — returns 0 for half the inputs and 1 for the other half

Classically this requires 2^(n-1) + 1 evaluations in the worst case.
Quantumly it requires exactly ONE evaluation.

This is one of the first algorithms to demonstrate quantum speedup.

Circuit (3-qubit example, balanced oracle):
  q0: ─[H]──[oracle]──[H]──[M]
  q1: ─[H]──[oracle]──[H]──[M]
  q2: ─[X]─[H]──[oracle]──────
"""

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def create_constant_oracle(n: int) -> QuantumCircuit:
    """Create an oracle for a constant function (f(x) = 0 for all x)."""
    oracle = QuantumCircuit(n + 1, name="Constant Oracle")
    # A constant oracle does nothing (f(x) = 0) or flips the ancilla (f(x) = 1).
    # Here we use f(x) = 0 — identity operation.
    return oracle


def create_balanced_oracle(n: int) -> QuantumCircuit:
    """Create an oracle for a balanced function using CNOT gates."""
    oracle = QuantumCircuit(n + 1, name="Balanced Oracle")
    # Each input qubit controls a NOT on the ancilla qubit.
    # This creates f(x) = x_0 XOR x_1 XOR ... which is balanced.
    for qubit in range(n):
        oracle.cx(qubit, n)
    return oracle


def deutsch_jozsa(oracle: QuantumCircuit, n: int) -> QuantumCircuit:
    """Build the full Deutsch-Jozsa circuit around a given oracle."""
    qc = QuantumCircuit(n + 1, n)

    # Prepare ancilla qubit in |1⟩ state
    qc.x(n)

    # Apply Hadamard to all qubits
    qc.h(range(n + 1))

    qc.barrier()

    # Apply the oracle
    qc.compose(oracle, inplace=True)

    qc.barrier()

    # Apply Hadamard to input qubits
    qc.h(range(n))

    # Measure input qubits only
    qc.measure(range(n), range(n))

    return qc


def run_deutsch_jozsa(oracle: QuantumCircuit, n: int, shots: int = 1024) -> dict:
    """Run the Deutsch-Jozsa algorithm and return counts."""
    qc = deutsch_jozsa(oracle, n)
    simulator = AerSimulator()
    compiled = transpile(qc, simulator)
    result = simulator.run(compiled, shots=shots).result()
    return result.get_counts(compiled)


def classify_result(counts: dict, n: int) -> str:
    """Determine if the function is constant or balanced from the results."""
    # If all measurements are |000...0⟩, the function is constant.
    zero_state = "0" * n
    if zero_state in counts and counts[zero_state] == sum(counts.values()):
        return "CONSTANT"
    return "BALANCED"


def main():
    print("=" * 55)
    print("  DEUTSCH-JOZSA — Quantum Function Classification")
    print("=" * 55)
    print()

    n = 3  # Number of input qubits
    shots = 1024

    # --- Test with CONSTANT oracle ---
    print("Test 1: Constant Oracle (f(x) = 0 for all x)")
    print("-" * 45)

    const_oracle = create_constant_oracle(n)
    qc_const = deutsch_jozsa(const_oracle, n)
    print("Circuit:")
    print(qc_const.draw(output="text"))
    print()

    counts_const = run_deutsch_jozsa(const_oracle, n, shots)
    result_const = classify_result(counts_const, n)

    for state, count in sorted(counts_const.items()):
        bar = "█" * int(count / shots * 40)
        pct = count / shots * 100
        print(f"  |{state}⟩  {count:>4}  ({pct:5.1f}%)  {bar}")
    print(f"\n  → Function is: {result_const}")

    print()

    # --- Test with BALANCED oracle ---
    print("Test 2: Balanced Oracle (f(x) = x₀ ⊕ x₁ ⊕ x₂)")
    print("-" * 45)

    bal_oracle = create_balanced_oracle(n)
    qc_bal = deutsch_jozsa(bal_oracle, n)
    print("Circuit:")
    print(qc_bal.draw(output="text"))
    print()

    counts_bal = run_deutsch_jozsa(bal_oracle, n, shots)
    result_bal = classify_result(counts_bal, n)

    for state, count in sorted(counts_bal.items()):
        bar = "█" * int(count / shots * 40)
        pct = count / shots * 100
        print(f"  |{state}⟩  {count:>4}  ({pct:5.1f}%)  {bar}")
    print(f"\n  → Function is: {result_bal}")

    print()
    print("✓ Both functions classified with a SINGLE oracle query!")
    print("  Classical approach would need up to 5 queries for 3-bit input.")


if __name__ == "__main__":
    main()
