"""Schema compiler for the DIR-01 intent router (HS-1-04).

Spec: `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` §7.3. The router
emits structured JSON conforming to::

    {"matched": bool,
     "block_id": <enum>,
     "confidence": float,
     "extras": {<key>: <enum>, ...}}

Free-form prose is forbidden; the token sampler is constrained at
decode time. Each backend implements this in its idiomatic mechanism,
behind the shared `BlockSet → backend artifact` compiler in this
module:

- `to_gbnf(schema)` — GBNF string for `llama-cpp-python`'s
  `LlamaGrammar.from_string` (consumed by `runtime_llama_cpp.py`).
- `to_outlines(schema)` — JSON-schema dict for an `outlines`-style
  logits processor (consumed by `runtime_mlx.py`).

Both emitters compile from the same `BlockSet`; the value sets they
allow MUST be identical so the same prompt produces outputs from the
same value set regardless of which runtime served them (DIR-01 §7.3
item 3).
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

_BLOCK_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_EXTRA_VALUE_RE = re.compile(r"^[a-z0-9_-]+$", re.IGNORECASE)


class GrammarCompileError(ValueError):
    """Raised when a `BlockSet` / `StructuredOutputSchema` cannot be compiled."""


@dataclass(frozen=True)
class BlockSpec:
    """One block in the loaded `BlockSet` (HS-1-05 will populate from YAML)."""

    id: str
    extras_schema: Mapping[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class BlockSet:
    """The loaded block taxonomy. HS-1-04 builds this by hand for tests."""

    blocks: tuple[BlockSpec, ...]
    default_match_confidence: float = 0.6

    def block_ids(self) -> tuple[str, ...]:
        return tuple(b.id for b in self.blocks)


@dataclass(frozen=True)
class StructuredOutputSchema:
    """Backend-neutral router-output schema, derived from a `BlockSet`."""

    block_ids: tuple[str, ...]
    extras_per_block: Mapping[str, Mapping[str, tuple[str, ...]]]

    @classmethod
    def from_block_set(cls, bs: BlockSet) -> "StructuredOutputSchema":
        if not bs.blocks:
            raise GrammarCompileError("BlockSet must declare at least one block.")
        seen: set[str] = set()
        extras: dict[str, dict[str, tuple[str, ...]]] = {}
        for b in bs.blocks:
            if not _BLOCK_ID_RE.match(b.id):
                raise GrammarCompileError(
                    f"block_id {b.id!r} must match {_BLOCK_ID_RE.pattern}"
                )
            if b.id in seen:
                raise GrammarCompileError(f"duplicate block_id {b.id!r}")
            seen.add(b.id)
            block_extras: dict[str, tuple[str, ...]] = {}
            for key, values in b.extras_schema.items():
                if not values:
                    raise GrammarCompileError(
                        f"extras[{b.id}][{key!r}] must declare at least one value"
                    )
                for v in values:
                    if not _EXTRA_VALUE_RE.match(v):
                        raise GrammarCompileError(
                            f"extras value {v!r} must match {_EXTRA_VALUE_RE.pattern}"
                        )
                block_extras[key] = tuple(values)
            extras[b.id] = block_extras
        return cls(
            block_ids=tuple(b.id for b in bs.blocks),
            extras_per_block=extras,
        )


def _quote(s: str) -> str:
    """Quote a literal for a GBNF rule. We control the alphabet."""
    return '"\\"' + s + '\\""'


def to_gbnf(schema: StructuredOutputSchema) -> str:
    """Emit a GBNF string for the structured router output.

    The grammar is intentionally narrow: it produces the exact JSON
    object shape spec'd in §7.3, with `block_id` and per-block extras
    constrained to the schema's enum values. Whitespace is permissive
    in JSON-style (one optional space after structural punctuation).
    """
    if not schema.block_ids:
        raise GrammarCompileError("schema must contain at least one block_id")

    block_id_alts = " | ".join(_quote(bid) for bid in schema.block_ids)

    # Per-block extras: build one alternative per block whose extras_per_block
    # entry maps that block's id to its allowed key/value pairs. If a block has
    # no extras, allow an empty object for that branch.
    extras_alts: list[str] = []
    for bid in schema.block_ids:
        block_extras = schema.extras_per_block.get(bid, {})
        if not block_extras:
            extras_alts.append('"{}"')
            continue
        # Each pair: "key": value-enum. Pairs joined by ws "," ws. We require
        # all keys to appear in declared order — keeps the grammar finite and
        # easy for the model.
        pair_chunks: list[str] = []
        for key, values in block_extras.items():
            value_alt = " | ".join(_quote(v) for v in values)
            pair_chunks.append(f'{_quote(key)} ws ":" ws ({value_alt})')
        body = ' ws "," ws '.join(pair_chunks)
        extras_alts.append(f'"{{" ws {body} ws "}}"')
    extras_rule = " | ".join(f"({alt})" for alt in extras_alts)

    return "\n".join(
        [
            'root ::= "{" ws "\\"matched\\"" ws ":" ws bool ws "," ws '
            '"\\"block_id\\"" ws ":" ws block_id ws "," ws '
            '"\\"confidence\\"" ws ":" ws confidence ws "," ws '
            '"\\"extras\\"" ws ":" ws extras ws "}"',
            f"block_id ::= {block_id_alts}",
            f"extras ::= {extras_rule}",
            'bool ::= "true" | "false"',
            'confidence ::= "0" "." [0-9] [0-9]* | "1" "." "0" "0"*',
            'ws ::= [ \\t\\n]*',
        ]
    )


def to_outlines(schema: StructuredOutputSchema) -> dict[str, Any]:
    """Emit a JSON-schema dict for an `outlines`-style logits processor.

    `outlines.processors.JSONLogitsProcessor` accepts a JSON-schema
    string; this function returns the parsed dict so callers can
    `json.dumps` it at the call site or inspect it in tests. We
    encode block_id as a top-level enum. Per-block extras are
    expressed as a `oneOf` over per-block sub-schemas keyed by
    `block_id` via const + extras shape.
    """
    if not schema.block_ids:
        raise GrammarCompileError("schema must contain at least one block_id")

    one_of: list[dict[str, Any]] = []
    for bid in schema.block_ids:
        extras_props: dict[str, Any] = {}
        required: list[str] = []
        for key, values in schema.extras_per_block.get(bid, {}).items():
            extras_props[key] = {"type": "string", "enum": list(values)}
            required.append(key)
        extras_schema: dict[str, Any] = {
            "type": "object",
            "properties": extras_props,
            "additionalProperties": False,
        }
        if required:
            extras_schema["required"] = required
        one_of.append(
            {
                "type": "object",
                "properties": {
                    "matched": {"type": "boolean"},
                    "block_id": {"const": bid},
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "extras": extras_schema,
                },
                "required": ["matched", "block_id", "confidence", "extras"],
                "additionalProperties": False,
            }
        )
    return {"oneOf": one_of}


def to_outlines_json(schema: StructuredOutputSchema) -> str:
    """Convenience: stringified form for handing to `outlines` directly."""
    return json.dumps(to_outlines(schema), separators=(",", ":"))


def equivalent_value_sets(schema: StructuredOutputSchema) -> dict[str, Any]:
    """Cross-backend equivalence: the value set both emitters describe.

    Returns a structure usable by tests to assert that GBNF and outlines
    output (for any compliant model) draws from the *same* enum domains:
    `{block_ids, extras_per_block}`. Any discrepancy between this and a
    backend emitter is a bug in the emitter, not in the schema.
    """
    return {
        "block_ids": tuple(schema.block_ids),
        "extras_per_block": {
            bid: {k: tuple(v) for k, v in keys.items()}
            for bid, keys in schema.extras_per_block.items()
        },
    }
