"""
Example 01 — Basic Quantum Search
===================================

This example shows how to use QuantX to search a list
using Grover's quantum search algorithm.

You don't need to know anything about quantum computing!
Just pass a list and a target — QuantX handles the rest.
"""

from quantx import search

# --- Example 1: Simple string search ---
print("=" * 50)
print("  Example 1: Search a list of names")
print("=" * 50)

names = ["alice", "bob", "charlie", "diana"]
result = search(names, target="charlie")

print(f"Searching for 'charlie' in {names}")
print(f"Result: {result}")
print(f"Found: {result.found}")
print(f"Confidence: {result.confidence:.1%}")
print()

# --- Example 2: Numeric search ---
print("=" * 50)
print("  Example 2: Search numbers")
print("=" * 50)

numbers = list(range(16))  # [0, 1, 2, ..., 15]
result = search(numbers, target=7)

print(f"Searching for 7 in a list of {len(numbers)} numbers")
print(f"Result: {result}")
print(f"Grover iterations used: {result.iterations}")
print(f"Qubits used: {result.n_qubits}")
print()

# --- Example 3: Inspect the circuit ---
print("=" * 50)
print("  Example 3: Peek under the hood")
print("=" * 50)

result = search(["a", "b", "c", "d"], target="b")
print("The quantum circuit that was built:")
print(result.draw())
print()

# --- Example 4: Raw measurement data ---
print("=" * 50)
print("  Example 4: Raw quantum measurements")
print("=" * 50)

result = search(["red", "green", "blue", "yellow"], target="blue")
print("Measurement counts (1024 shots):")
for state, count in sorted(result.measurements.items()):
    pct = count / sum(result.measurements.values()) * 100
    bar = "█" * int(pct / 2)
    print(f"  |{state}⟩  {count:>4} ({pct:5.1f}%)  {bar}")
