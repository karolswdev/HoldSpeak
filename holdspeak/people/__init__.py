"""Encrypted, local-only authority for confidential People records.

This package deliberately does not depend on HoldSpeak's primary database,
sync, search, inference, or cadence layers.
"""

from .crypto import Envelope, decrypt_payload, encrypt_payload
from .keys import MemoryKeyStore, NativeKeyStore, PeopleKeyError
from .policy import PeopleOperation, PeoplePolicy, PeopleUse, Visibility
from .store import (
    DEFAULT_PEOPLE_DB_PATH,
    EncryptedPeopleStore,
    PeopleReadiness,
    PeopleStoreError,
    production_people_store,
)

__all__ = [
    "EncryptedPeopleStore",
    "DEFAULT_PEOPLE_DB_PATH",
    "Envelope",
    "MemoryKeyStore",
    "NativeKeyStore",
    "PeopleKeyError",
    "PeopleOperation",
    "PeoplePolicy",
    "PeopleUse",
    "PeopleReadiness",
    "PeopleStoreError",
    "Visibility",
    "decrypt_payload",
    "encrypt_payload",
    "production_people_store",
]
