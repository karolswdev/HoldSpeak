"""ledgerline — an append-only double-entry payment ledger.

The ledger records money as immutable rows. Nothing here mutates a
posted entry; corrections are made by appending reversals. All money
is integer minor units (cents).
"""

__version__ = "0.4.0"

DEBIT = "debit"
CREDIT = "credit"
