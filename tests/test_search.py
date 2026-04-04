"""
Tests for the QuantX search module.

Testing strategy:
- Unit tests for utility functions (deterministic, fast)
- Integration tests for the full search pipeline (runs actual quantum circuits)
- Error handling tests (verifies our custom exceptions fire correctly)

We use pytest because it's the standard for Python testing. Each test function
starts with test_ so pytest auto-discovers it.
"""

import math

import pytest

from quantx import search, SearchResult
from quantx.exceptions import (
    InvalidInputError,
    QubitLimitError,
    SearchError,
)
from quantx.utils import (
    next_power_of_2,
    optimal_grover_iterations,
    qubits_needed,
)


# ============================================================
# Utility function tests — fast, deterministic, no quantum
# ============================================================


class TestQubitsNeeded:
    """Tests for the qubits_needed utility."""

    def test_power_of_2_inputs(self):
        assert qubits_needed(2) == 1
        assert qubits_needed(4) == 2
        assert qubits_needed(8) == 3
        assert qubits_needed(16) == 4

    def test_non_power_of_2_rounds_up(self):
        assert qubits_needed(3) == 2   # 3 items → 2 qubits (4 states)
        assert qubits_needed(5) == 3   # 5 items → 3 qubits (8 states)
        assert qubits_needed(100) == 7  # 100 items → 7 qubits (128 states)

    def test_single_item(self):
        assert qubits_needed(1) == 1

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            qubits_needed(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            qubits_needed(-5)


class TestNextPowerOf2:
    def test_already_power_of_2(self):
        assert next_power_of_2(1) == 1
        assert next_power_of_2(4) == 4
        assert next_power_of_2(8) == 8

    def test_rounds_up(self):
        assert next_power_of_2(3) == 4
        assert next_power_of_2(5) == 8
        assert next_power_of_2(7) == 8


class TestOptimalGroverIterations:
    def test_small_search_spaces(self):
        # 4 items → 1 iteration (the classic result)
        assert optimal_grover_iterations(4) == 1

    def test_larger_search_spaces(self):
        # 16 items → floor(pi/4 * sqrt(16)) = floor(pi) = 3
        assert optimal_grover_iterations(16) == 3

    def test_always_at_least_1(self):
        assert optimal_grover_iterations(2) >= 1


# ============================================================
# Input validation tests — verify errors are helpful
# ============================================================


class TestSearchValidation:
    """Tests that bad input produces clear, helpful error messages."""

    def test_empty_list_raises(self):
        with pytest.raises(InvalidInputError, match="empty list"):
            search([], target="x")

    def test_single_item_raises(self):
        with pytest.raises(InvalidInputError, match="only has 1 item"):
            search(["only_one"], target="only_one")

    def test_non_list_raises(self):
        with pytest.raises(InvalidInputError, match="list or tuple"):
            search("not a list", target="x")

    def test_target_not_in_list_raises(self):
        with pytest.raises(SearchError, match="not in the search space"):
            search(["alice", "bob"], target="charlie")

    def test_target_not_in_list_shows_preview(self):
        """Error message should show what IS in the list."""
        with pytest.raises(SearchError, match="alice"):
            search(["alice", "bob"], target="charlie")

    def test_non_power_of_2_with_auto_pad_false(self):
        """Should raise when auto_pad=False and list isn't power of 2."""
        with pytest.raises(InvalidInputError, match="not a power of 2"):
            search(["a", "b", "c"], target="b", auto_pad=False)


# ============================================================
# Integration tests — runs actual quantum circuits
# ============================================================


class TestSearchIntegration:
    """Tests that run real quantum circuits on the simulator.

    These tests verify end-to-end behaviour. Because quantum circuits
    are probabilistic, we use a high shot count and check that the
    confidence is above a reasonable threshold (not exactly 100%).
    """

    def test_search_4_items(self):
        """Classic Grover's: 4 items, should find target with high confidence."""
        items = ["alice", "bob", "charlie", "diana"]
        result = search(items, target="charlie")

        assert isinstance(result, SearchResult)
        assert result.found is True
        assert result.target == "charlie"
        assert result.confidence > 0.8
        assert result.n_qubits == 2
        assert result.iterations == 1

    def test_search_power_of_2(self):
        """8 items — exact power of 2, no padding needed."""
        items = list(range(8))
        result = search(items, target=5)

        assert result.found is True
        assert result.confidence > 0.7
        assert result.n_qubits == 3

    def test_search_non_power_of_2_auto_pads(self):
        """5 items — should auto-pad to 8 and still find the target."""
        items = ["a", "b", "c", "d", "e"]
        result = search(items, target="c")

        assert result.found is True
        assert result.confidence > 0.5  # Lower confidence expected with padding
        assert result.n_qubits == 3  # ceil(log2(5)) = 3

    def test_search_returns_circuit(self):
        """The circuit should be accessible for inspection."""
        result = search(["a", "b", "c", "d"], target="b")
        circuit = result.get_circuit()

        assert circuit is not None
        assert circuit.num_qubits == 2

    def test_search_draw(self):
        """Drawing should return something printable for text output."""
        result = search(["a", "b", "c", "d"], target="a")
        drawing = result.draw("text")

        # Qiskit returns a TextDrawing object, not a plain str
        drawing_str = str(drawing)
        assert len(drawing_str) > 0
        assert "H" in drawing_str  # Should contain Hadamard gates

    def test_search_with_integers(self):
        """Should work with non-string items."""
        result = search([10, 20, 30, 40], target=30)
        assert result.found is True

    def test_search_with_tuples(self):
        """Should accept tuples as input."""
        result = search(("x", "y", "z", "w"), target="z")
        assert result.found is True

    def test_search_16_items(self):
        """Larger search space — 16 items."""
        items = [f"item_{i}" for i in range(16)]
        result = search(items, target="item_7")

        assert result.found is True
        assert result.confidence > 0.7
        assert result.n_qubits == 4
        assert result.iterations == 3

    def test_search_first_item(self):
        """Target is the first item (index 0 → binary 00)."""
        result = search(["first", "second", "third", "fourth"], target="first")
        assert result.found is True

    def test_search_last_item(self):
        """Target is the last item (highest index)."""
        result = search(["a", "b", "c", "d"], target="d")
        assert result.found is True

    def test_result_repr(self):
        """repr should be human-readable."""
        result = search(["a", "b", "c", "d"], target="b")
        r = repr(result)

        assert "SearchResult" in r
        assert "'b'" in r
        assert "confidence=" in r

    def test_measurements_are_dict(self):
        """Raw measurements should be a dict of binary strings → counts."""
        result = search(["a", "b", "c", "d"], target="a")

        assert isinstance(result.measurements, dict)
        assert all(isinstance(k, str) for k in result.measurements)
        assert all(isinstance(v, int) for v in result.measurements.values())
