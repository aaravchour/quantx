# QuantumEasy

Quantum computing for everyone. Use quantum algorithms without knowing quantum mechanics.

```python
from quantumeasy import search

result = search(["alice", "bob", "charlie", "diana"], target="charlie")
print(result)
# SearchResult(FOUND: 'charlie', confidence=100.0%, qubits=2, iterations=1)
```

QuantumEasy wraps [Qiskit](https://qiskit.org/) and handles all the quantum circuit construction, qubit management, and measurement interpretation behind a clean Python API. You pass in normal Python data, you get back normal Python results.

## Install

```bash
pip install quantumeasy
```

Requires Python 3.9+ and Qiskit 2.x (installed automatically).

## Quick Start

### Search a list (Grover's algorithm)

Grover's algorithm searches an unsorted collection in O(sqrt(N)) time — a quadratic speedup over classical linear search.

```python
from quantumeasy import search

# Search through strings
result = search(["alice", "bob", "charlie", "diana"], target="charlie")
print(result.found)       # True
print(result.confidence)  # 1.0 (100%)

# Search through numbers
result = search(list(range(16)), target=7)
print(result.found)       # True
print(result.confidence)  # ~0.96
print(result.iterations)  # 3 (optimal Grover iterations)
```

### Inspect the circuit

Every result lets you peek under the hood at the actual quantum circuit:

```python
result = search(["a", "b", "c", "d"], target="b")

# Print the circuit diagram
print(result.draw())

# Get the raw Qiskit circuit object
circuit = result.get_circuit()
```

### Configure the backend

QuantumEasy uses a local simulator by default. Switch to real IBM Quantum hardware with one line:

```python
import quantumeasy

# Local simulator (default — no setup needed)
quantumeasy.set_backend("aer_simulator")

# Real quantum hardware
quantumeasy.set_backend("ibm_brisbane", token="your-ibm-quantum-token")

# Adjust measurement shots (default: 1024)
quantumeasy.set_shots(4096)
```

Get a free IBM Quantum token at [quantum.ibm.com](https://quantum.ibm.com/).

## Modules

| Module | Algorithm | Status |
|--------|-----------|--------|
| `search` | Grover's search | Available |
| `optimise` | QAOA optimisation | Planned |
| `ml` | Quantum kernel classification | Planned |
| `crypto` | Shor's factoring, BB84 QKD | Planned |

## Error Messages

QuantumEasy is designed to give you clear, actionable errors — not cryptic quantum tracebacks:

```
InvalidInputError: Target 'eve' is not in the search space.
Grover's algorithm requires the target to exist in the list.
Your list contains: ['alice', 'bob', 'charlie', 'diana']
```

```
QubitLimitError: This operation needs 25 qubits, but the current backend
supports up to 24.
Try reducing your input size or switching to a more powerful backend:
  quantumeasy.set_backend('ibm_brisbane', token='your-token')
```

## API Reference

### `search(items, target, *, shots=None, force=False, auto_pad=True)`

Search for an item using Grover's quantum search algorithm.

**Parameters:**
- `items` — list or tuple of items to search through (at least 2)
- `target` — the item to find (must exist in items)
- `shots` — number of circuit executions (default: 1024)
- `force` — skip warnings for large search spaces
- `auto_pad` — automatically pad to power-of-2 size (default: True)

**Returns:** `SearchResult` with:
- `.found` — whether the target was found (bool)
- `.confidence` — probability of correctness (0.0 to 1.0)
- `.target` — the searched item
- `.iterations` — Grover iterations used
- `.n_qubits` — number of qubits in the circuit
- `.measurements` — raw measurement counts dict
- `.get_circuit()` — returns the Qiskit QuantumCircuit
- `.draw()` — renders the circuit diagram

### `set_backend(backend_name, *, token=None, max_qubits=None)`

Switch the quantum backend. `"aer_simulator"` for local, or an IBM backend name for real hardware.

### `set_shots(shots)`

Set the default number of measurement shots (default: 1024).

## How It Works

When you call `search(items, target)`, QuantumEasy:

1. Validates your input and gives a clear error if something is wrong
2. Calculates how many qubits are needed (`ceil(log2(len(items)))`)
3. Pads the search space to a power of 2 (required by Grover's algorithm)
4. Computes the optimal number of Grover iterations (`floor(pi/4 * sqrt(N))`)
5. Builds a quantum circuit: Hadamard gates, oracle, diffusion operator
6. Runs it on the backend and interprets the measurements
7. Returns a `SearchResult` with the answer and confidence score

You get the quantum speedup without writing a single quantum gate.

## Development

```bash
# Clone and install in dev mode
git clone https://github.com/aaravchourishi/quantumeasy.git
cd quantumeasy
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=quantumeasy
```

## Project Structure

```
quantumeasy/
├── __init__.py       # Public API
├── search.py         # Grover's search
├── backends.py       # Backend management
├── exceptions.py     # Custom error classes
├── utils.py          # Shared utilities
├── _validators.py    # Input validation
tests/
├── test_search.py    # 28 tests
examples/
├── 01_basic_search.py
```

## Standalone Algorithms

The repo also includes standalone implementations of fundamental quantum algorithms (no library needed):

| File | Algorithm |
|------|-----------|
| `01_bell_state.py` | Bell State — quantum entanglement |
| `02_deutsch_joshi.py` | Deutsch-Jozsa — constant vs balanced |
| `03_grovers_search.py` | Grover's Search — unstructured search |
| `04_quantum_teleportation.py` | Quantum Teleportation |
| `05_quantum_calculator.py` | Quantum arithmetic (+, -, x) |

## Requirements

- Python 3.9+
- Qiskit 2.x
- Qiskit Aer 0.13+
- NumPy

Optional: `qiskit-ibm-runtime` for real hardware, `scikit-learn` for the ML module.

## License

MIT
