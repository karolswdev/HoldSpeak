"""The native memory index (docs/internal/MEMORY-DESIGN.md).

Memory is an index, not a second source of truth.  Every row in a
``memory_*`` table is derived from a source table and can be rebuilt.
"""
