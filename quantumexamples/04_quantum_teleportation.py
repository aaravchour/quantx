"""
Quantum Teleportation
======================
Transfers the quantum state of one qubit to another using:
  • One entangled Bell pair (shared beforehand)
  • Two classical bits of communication

The original qubit's state is destroyed in the process
(no-cloning theorem is preserved).

Protocol:
  1. Alice and Bob share an entangled pair (qubits 1 & 2)
  2. Alice has a qubit (qubit 0) in an arbitrary state |ψ⟩ to teleport
  3. Alice entangles her message qubit with her half of the pair
  4. Alice measures both her qubits and sends the 2 classical bits to Bob
  5. Bob applies corrections based on Alice's bits → his qubit is now |ψ⟩

Circuit:
  q0 (Alice's message): ─[Rz]─[Rx]──●──[H]──[M]─────────────────
                                     │        ↓
  q1 (Alice's EPR):     ──[H]──●───⊕──────[M]──────────────────
                                │              ↓          ↓
  q2 (Bob's EPR):       ───────⊕──────────────[X^c1]──[Z^c0]──[M]
"""

import math
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import AerSimulator


def create_teleportation_circuit(
    theta: float = math.pi / 4,
    phi: float = math.pi / 3,
) -> QuantumCircuit:
    """
    Build a quantum teleportation circuit.

    Args:
        theta: Rotation angle for Rx gate (prepares the state to teleport)
        phi:   Rotation angle for Rz gate (prepares the state to teleport)

    The message state |ψ⟩ = Rx(θ)·Rz(φ)|0⟩
    """
    # Use separate classical registers so we can condition on each independently
    qr = QuantumRegister(3, "q")
    cr0 = ClassicalRegister(1, "c0")
    cr1 = ClassicalRegister(1, "c1")
    cr2 = ClassicalRegister(1, "c2")
    qc = QuantumCircuit(qr, cr0, cr1, cr2)

    # --- Step 1: Prepare the message state |ψ⟩ on qubit 0 ---
    qc.rz(phi, 0)
    qc.rx(theta, 0)
    qc.barrier(label="Prepare |ψ⟩")

    # --- Step 2: Create Bell pair between qubits 1 (Alice) and 2 (Bob) ---
    qc.h(1)
    qc.cx(1, 2)
    qc.barrier(label="Bell Pair")

    # --- Step 3: Alice's Bell measurement ---
    qc.cx(0, 1)  # CNOT: message → Alice's EPR qubit
    qc.h(0)       # Hadamard on message qubit
    qc.barrier(label="Bell Meas")

    # Measure Alice's qubits
    qc.measure(0, cr0)  # c0
    qc.measure(1, cr1)  # c1

    qc.barrier(label="Classical Comm")

    # --- Step 4: Bob's conditional corrections ---
    # If c1 = 1, apply X; if c0 = 1, apply Z
    with qc.if_test((cr1, 1)):
        qc.x(2)
    with qc.if_test((cr0, 1)):
        qc.z(2)

    qc.barrier(label="Bob Corrects")

    # --- Step 5: Measure Bob's qubit ---
    qc.measure(2, cr2)

    return qc


def run_teleportation(shots: int = 4096) -> dict:
    """Run the teleportation circuit on a simulator."""
    qc = create_teleportation_circuit()
    simulator = AerSimulator()
    compiled = transpile(qc, simulator)
    result = simulator.run(compiled, shots=shots).result()
    return result.get_counts(compiled), qc


def analyze_teleportation(counts: dict, shots: int) -> None:
    """Analyze whether teleportation succeeded by checking Bob's qubit statistics."""
    # Bob's qubit is bit 2 (the most significant in the 3-bit string)
    bob_0 = 0
    bob_1 = 0

    for state, count in counts.items():
        # With separate registers, state is like "0 1 0" (c2 c1 c0)
        # Bob's qubit is c2 — the first segment
        bob_bit = state.split()[0] if " " in state else state[0]
        if bob_bit == "0":
            bob_0 += count
        else:
            bob_1 += count

    print("Bob's qubit (teleported state) statistics:")
    print("-" * 40)
    bar0 = "█" * int(bob_0 / shots * 40)
    bar1 = "█" * int(bob_1 / shots * 40)
    print(f"  |0⟩  {bob_0:>4}  ({bob_0/shots*100:5.1f}%)  {bar0}")
    print(f"  |1⟩  {bob_1:>4}  ({bob_1/shots*100:5.1f}%)  {bar1}")
    print()

    # For |ψ⟩ = Rx(π/4)·Rz(π/3)|0⟩, the expected probabilities are:
    theta = math.pi / 4
    expected_0 = math.cos(theta / 2) ** 2
    expected_1 = math.sin(theta / 2) ** 2
    print(f"Expected: |0⟩ = {expected_0*100:.1f}%, |1⟩ = {expected_1*100:.1f}%")
    print(f"Measured: |0⟩ = {bob_0/shots*100:.1f}%, |1⟩ = {bob_1/shots*100:.1f}%")

    error = abs(bob_0 / shots - expected_0)
    print(f"Error:    {error*100:.1f}%")


def main():
    print("=" * 55)
    print("  QUANTUM TELEPORTATION — State Transfer Protocol")
    print("=" * 55)
    print()

    shots = 4096
    counts, qc = run_teleportation(shots)

    print(f"Teleporting state |ψ⟩ = Rx(π/4)·Rz(π/3)|0⟩")
    print(f"from Alice (qubit 0) to Bob (qubit 2)")
    print()
    print("Circuit:")
    print(qc.draw(output="text"))
    print()

    print(f"Full measurement results ({shots} shots):")
    print("-" * 40)
    for state, count in sorted(counts.items()):
        pct = count / shots * 100
        print(f"  |{state}⟩  {count:>4}  ({pct:5.1f}%)")
    print()

    analyze_teleportation(counts, shots)
    print()
    print("✓ Quantum state teleported successfully!")
    print("  The original qubit was destroyed (no-cloning theorem).")
    print("  2 classical bits were needed to complete the transfer.")


if __name__ == "__main__":
    main()
