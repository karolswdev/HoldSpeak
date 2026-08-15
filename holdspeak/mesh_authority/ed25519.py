"""RFC 8032 Ed25519 over the standard library (HS-131-16).

The hub signs ONE dispatch offer per claim with a per-node private key; the
worker verifies it with the public half it pinned at pairing. That asymmetry is
Sol Amendment 1: the node's own bearer token authenticates its requests and MACs
its reports, and it must not be able to forge the hub's authority.

HoldSpeak pins no cryptographic package, and the acceptance map admits a new
dependency only when an already-pinned one cannot carry the signature. Nothing is
pinned, so the algorithm lives here in its RFC 8032 §5.1 form and is proved
against the RFC's own §7.1 test vectors.

Recorded note (design §Recorded notes): this is a straightforward, NOT a
constant-time, implementation. The forgery this story fences is a node-token
holder minting hub authority on a private mesh; timing analysis of the hub's own
signing loop sits beyond the owner's realistic-use bar and is recorded here
rather than defended. Verification touches only public material.
"""

from __future__ import annotations

import hashlib
from typing import Optional, Tuple

#: Curve constants (RFC 8032 §5.1).
_P = 2**255 - 19
_L = 2**252 + 27742317777372353535851937790883648493
_D = -121665 * pow(121666, _P - 2, _P) % _P
_SQRT_M1 = pow(2, (_P - 1) // 4, _P)

PUBLIC_KEY_BYTES = 32
PRIVATE_KEY_BYTES = 32
SIGNATURE_BYTES = 64

_Point = Tuple[int, int, int, int]


def _sha512(data: bytes) -> bytes:
    return hashlib.sha512(data).digest()


def _sha512_int(data: bytes) -> int:
    return int.from_bytes(_sha512(data), "little")


# ── curve arithmetic (extended homogeneous coordinates) ───────────────


def _point_add(p: _Point, q: _Point) -> _Point:
    a = (p[1] - p[0]) * (q[1] - q[0]) % _P
    b = (p[1] + p[0]) * (q[1] + q[0]) % _P
    c = 2 * p[3] * q[3] * _D % _P
    d = 2 * p[2] * q[2] % _P
    e, f, g, h = b - a, d - c, d + c, b + a
    return (e * f % _P, g * h % _P, f * g % _P, e * h % _P)


def _point_mul(scalar: int, point: _Point) -> _Point:
    result: _Point = (0, 1, 1, 0)
    while scalar > 0:
        if scalar & 1:
            result = _point_add(result, point)
        point = _point_add(point, point)
        scalar >>= 1
    return result


def _point_equal(p: _Point, q: _Point) -> bool:
    if (p[0] * q[2] - q[0] * p[2]) % _P != 0:
        return False
    return (p[1] * q[2] - q[1] * p[2]) % _P == 0


def _recover_x(y: int, sign: int) -> Optional[int]:
    if y >= _P:
        return None
    square = (y * y - 1) * pow(_D * y * y + 1, _P - 2, _P) % _P
    if square == 0:
        return None if sign else 0
    x = pow(square, (_P + 3) // 8, _P)
    if (x * x - square) % _P != 0:
        x = x * _SQRT_M1 % _P
    if (x * x - square) % _P != 0:
        return None
    if (x & 1) != sign:
        x = _P - x
    return x


_BASE_Y = 4 * pow(5, _P - 2, _P) % _P
_BASE_X = _recover_x(_BASE_Y, 0) or 0
_BASE: _Point = (_BASE_X, _BASE_Y, 1, _BASE_X * _BASE_Y % _P)


def _compress(point: _Point) -> bytes:
    inverse = pow(point[2], _P - 2, _P)
    x = point[0] * inverse % _P
    y = point[1] * inverse % _P
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _decompress(encoded: bytes) -> Optional[_Point]:
    if len(encoded) != 32:
        return None
    y = int.from_bytes(encoded, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _recover_x(y, sign)
    if x is None:
        return None
    return (x, y, 1, x * y % _P)


# ── the three verbs ───────────────────────────────────────────────────


def _expand(private_key: bytes) -> Tuple[int, bytes]:
    if len(private_key) != PRIVATE_KEY_BYTES:
        raise ValueError("ed25519_private_key_invalid")
    digest = _sha512(private_key)
    scalar = int.from_bytes(digest[:32], "little")
    scalar &= (1 << 254) - 8
    scalar |= 1 << 254
    return scalar, digest[32:]


def public_key(private_key: bytes) -> bytes:
    """The 32-byte public half of one Ed25519 private key."""
    scalar, _prefix = _expand(private_key)
    return _compress(_point_mul(scalar, _BASE))


def sign(private_key: bytes, message: bytes) -> bytes:
    """Deterministic RFC 8032 signature over exactly ``message``."""
    scalar, prefix = _expand(private_key)
    encoded_public = _compress(_point_mul(scalar, _BASE))
    nonce = _sha512_int(prefix + message) % _L
    commitment = _compress(_point_mul(nonce, _BASE))
    challenge = _sha512_int(commitment + encoded_public + message) % _L
    signature_scalar = (nonce + challenge * scalar) % _L
    return commitment + int.to_bytes(signature_scalar, 32, "little")


def verify(public: bytes, message: bytes, signature: bytes) -> bool:
    """True only for a well-formed signature over exactly ``message``.

    Every malformed input is a plain ``False`` — a caller must never have to
    distinguish "not a signature" from "not this signature".
    """
    if len(public) != PUBLIC_KEY_BYTES or len(signature) != SIGNATURE_BYTES:
        return False
    encoded_public = _decompress(public)
    if encoded_public is None:
        return False
    commitment = _decompress(signature[:32])
    if commitment is None:
        return False
    signature_scalar = int.from_bytes(signature[32:], "little")
    if signature_scalar >= _L:
        return False
    challenge = _sha512_int(signature[:32] + public + message) % _L
    left = _point_mul(signature_scalar, _BASE)
    right = _point_add(commitment, _point_mul(challenge, encoded_public))
    return _point_equal(left, right)


__all__ = [
    "PRIVATE_KEY_BYTES",
    "PUBLIC_KEY_BYTES",
    "SIGNATURE_BYTES",
    "public_key",
    "sign",
    "verify",
]
