"""The scenario contract + the feature ledger.

The **scenario** is the unit of UAT; the **ledger** is what it cites. This
package loads and validates both, and computes coverage — per surface and
overall — against the enumerated shipped surface. Pure data + math over YAML;
no ``holdspeak`` import.
"""

from __future__ import annotations
