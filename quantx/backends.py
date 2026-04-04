"""
Backend management for QuantX.

This module uses the "module-level state" pattern — there's a single global
BackendManager that all modules share. When a user calls:

    quantx.set_backend("ibm_brisbane", token="xxx")

...it updates this shared state, and the next time any module runs a circuit,
it uses the new backend automatically.

Why not pass the backend to every function? Because it's tedious:
    search(items, target, backend=my_backend)  # Nobody wants this everywhere

Instead, you set it once and forget about it — like how pandas.set_option() works.
"""

from __future__ import annotations

from typing import Optional

from qiskit import transpile
from qiskit_aer import AerSimulator

from quantx.exceptions import BackendError


class BackendManager:
    """Manages the active quantum backend.

    This class holds the current backend configuration. There's one global
    instance (_default_manager) that all QuantX modules use.
    """

    # Maximum qubits for common backends (used for helpful error messages)
    KNOWN_LIMITS = {
        "aer_simulator": 24,  # Practical limit — technically higher but very slow
    }

    def __init__(self) -> None:
        self._backend = AerSimulator()
        self._backend_name = "aer_simulator"
        self._max_qubits = self.KNOWN_LIMITS["aer_simulator"]
        self._shots = 1024

    @property
    def name(self) -> str:
        """Name of the current backend."""
        return self._backend_name

    @property
    def max_qubits(self) -> int:
        """Maximum qubit count for the current backend."""
        return self._max_qubits

    @property
    def shots(self) -> int:
        """Default number of measurement shots."""
        return self._shots

    @shots.setter
    def shots(self, value: int) -> None:
        if value < 1:
            raise BackendError("Number of shots must be at least 1.")
        self._shots = value

    def set_backend(
        self,
        backend_name: str = "aer_simulator",
        token: Optional[str] = None,
        max_qubits: Optional[int] = None,
    ) -> None:
        """Switch the active quantum backend.

        Args:
            backend_name: Name of the backend. Use "aer_simulator" for local simulation
                or an IBM backend name like "ibm_brisbane" for real hardware.
            token: IBM Quantum API token. Required for real hardware.
            max_qubits: Override the max qubit limit. If not set, uses known defaults
                or 5 for unknown IBM backends.

        Examples:
            >>> manager = BackendManager()
            >>> manager.set_backend("aer_simulator")  # Local simulator (default)
            >>> manager.set_backend("ibm_brisbane", token="your-token-here")
        """
        if backend_name == "aer_simulator":
            self._backend = AerSimulator()
            self._backend_name = "aer_simulator"
            self._max_qubits = max_qubits or self.KNOWN_LIMITS["aer_simulator"]
            return

        # For IBM backends, try to connect via qiskit-ibm-runtime
        if token is None:
            raise BackendError(
                f"To use '{backend_name}', you need an IBM Quantum API token.\n"
                f"Get one at https://quantum.ibm.com/ and pass it as:\n"
                f"  quantx.set_backend('{backend_name}', token='your-token')"
            )

        try:
            from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

            service = QiskitRuntimeService(channel="ibm_quantum", token=token)
            self._backend = service.backend(backend_name)
            self._backend_name = backend_name
            self._max_qubits = max_qubits or getattr(
                self._backend, "num_qubits", 5
            )
        except ImportError:
            raise BackendError(
                f"To use IBM Quantum hardware, install qiskit-ibm-runtime:\n"
                f"  pip install qiskit-ibm-runtime"
            )
        except Exception as e:
            raise BackendError(
                f"Could not connect to backend '{backend_name}'.\n"
                f"Check your API token and internet connection.\n"
                f"Original error: {e}"
            )

    def run_circuit(self, circuit, shots: Optional[int] = None) -> dict:
        """Transpile and run a circuit on the current backend.

        Args:
            circuit: A Qiskit QuantumCircuit to execute.
            shots: Number of measurement shots. Uses default if not specified.

        Returns:
            Dictionary of measurement counts, e.g. {"01": 512, "10": 512}.
        """
        shots = shots or self._shots
        compiled = transpile(circuit, self._backend)
        result = self._backend.run(compiled, shots=shots).result()
        return result.get_counts(compiled)


# Global default backend manager — shared by all modules
_default_manager = BackendManager()


def get_backend() -> BackendManager:
    """Get the global backend manager."""
    return _default_manager


def set_backend(
    backend_name: str = "aer_simulator",
    token: Optional[str] = None,
    max_qubits: Optional[int] = None,
) -> None:
    """Set the global quantum backend.

    Args:
        backend_name: Backend name. "aer_simulator" for local, or IBM backend name.
        token: IBM Quantum API token (required for real hardware).
        max_qubits: Override the qubit limit for the backend.

    Examples:
        >>> import quantx
        >>> quantx.set_backend("aer_simulator")  # Default
        >>> quantx.set_backend("ibm_brisbane", token="your-token")
    """
    _default_manager.set_backend(backend_name, token, max_qubits)


def set_shots(shots: int) -> None:
    """Set the default number of measurement shots.

    More shots = more accurate results but slower execution.
    Default is 1024, which is a good balance.

    Args:
        shots: Number of times to run each circuit.

    Examples:
        >>> import quantx
        >>> quantx.set_shots(4096)  # More accurate results
    """
    _default_manager.shots = shots
