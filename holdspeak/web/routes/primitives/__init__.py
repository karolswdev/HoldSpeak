"""The desk primitives routes, composed (HS-79-03).

One public constructor, unchanged: ``build_primitives_router`` includes the
family routers (plus the Ask atom's, HSM-16-04). Bodies moved verbatim from
the 1,294-line routes/primitives.py; the run-persist tail stays ONE function
in ``_shared``.
"""
from __future__ import annotations

from fastapi import APIRouter

from ...context import WebContext

# The public wire-vocabulary surface (tests + callers import these from the
# package root, as they did from the module): re-exported unchanged.
from ._shared import CANONICAL_SOURCE_TYPES, canonical_source_type  # noqa: F401

from .ask import build_ask_router
from .recipes import build_recipes_router
from .chains import build_chains_router
from .directories import build_directories_router
from .kbs import build_kbs_router
from .notes import build_notes_router
from .profiles import build_profiles_router
from .workflows import build_workflows_router


def build_primitives_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    router.include_router(build_notes_router(ctx))
    router.include_router(build_ask_router(ctx))
    router.include_router(build_recipes_router(ctx))
    router.include_router(build_profiles_router(ctx))
    router.include_router(build_kbs_router(ctx))
    router.include_router(build_chains_router(ctx))
    router.include_router(build_workflows_router(ctx))
    router.include_router(build_directories_router(ctx))
    return router
