"""Parked: defaults now ask public profile and assignment ports for these reads."""
from typing import Any


class RetiredDefaultQueries:
    def _profiles(self) -> Any:
        if self._library is not None:
            return self._library._profiles
        from ..model_profile_service import ModelProfileService

        return ModelProfileService(self._db)


    def _embed_head_ever_existed(self) -> bool:
        with self._db._connection() as conn:
            return conn.execute(
                "SELECT 1 FROM inference_assignment_heads WHERE assignment_key='capability:memory.embed'"
            ).fetchone() is not None

