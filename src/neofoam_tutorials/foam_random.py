"""OpenFOAM's ``Foam::Random`` (v2506, also v2406): the sequence TwoPhaseFlow's
``reconstructInterface`` draws its interface centres from.

``Random`` wraps ``Rand48`` (``std::linear_congruential_engine<uint64_t, 0x5DEECE66D, 0xB,
2^48>`` seeded with ``(seed << 16) | 0x330E``, each draw the state's top 31 bits) and
``std::uniform_real_distribution<double>``, which in libstdc++ is
``generate_canonical<double, 53>``: two draws ``a, b`` give ``(a + b 2^31) / 2^62``.
``position(start, end)`` draws one such value per component, x first.

``reconstructInterface`` seeds ``Random(1234567)`` once and, when ``nIter > 1``, takes
``globalPosition(0.9 origin, 1.1 origin)`` (on one rank the same as ``position``) as the
centre of every iteration; ``centres`` returns that sequence.
"""

from __future__ import annotations

import numpy as np

from .foam import Array

_MODULUS = 1 << 48
_MULTIPLIER = 0x5DEECE66D
_INCREMENT = 0xB
_RANGE = float(1 << 31)


class Random:
    """``Foam::Random(seed)``: :meth:`scalar01` and :meth:`position`."""

    def __init__(self, seed: int) -> None:
        self._state = ((seed & 0xFFFFFFFF) << 16) | 0x330E

    def _draw(self) -> int:
        self._state = (_MULTIPLIER * self._state + _INCREMENT) % _MODULUS
        return self._state >> 17

    def scalar01(self) -> float:
        """``Random::scalar01``: uniform in [0, 1)."""
        first = self._draw()
        second = self._draw()
        value = (first + second * _RANGE) / (_RANGE * _RANGE)
        return value if value < 1.0 else float(np.nextafter(1.0, 0.0))

    def position(self, start: Array, end: Array) -> Array:
        """``Random::position<vector>(start, end)``: one draw per component."""
        return np.array([s + self.scalar01() * (e - s) for s, e in zip(start, end)])


def centres(origin: Array, n_iter: int, seed: int = 1234567) -> Array:
    """The ``n_iter`` interface centres of ``reconstructInterface`` (rows of the result).

    With ``nIter 1`` it keeps the dictionary's ``origin``; otherwise every iteration
    draws a centre in the box ``origin +- 0.1 origin``.
    """
    origin = np.asarray(origin, dtype=float)
    if n_iter <= 1:
        return origin[None, :].copy()
    random = Random(seed)
    low, high = origin - 0.1 * origin, origin + 0.1 * origin
    return np.array([random.position(low, high) for _ in range(n_iter)])
