"""Parked 2026-11-08 from tests/integration/test_inference_placement_adoption.py: the tests of the parked Sequence/Workflow runner
(holdspeak/services/_parked/sequence_workflow_service.py). Kept, not collected.
"""
"""HS-143-10 Slice 6 — one real-object placement-adoption matrix.

The matrix deliberately joins the same frozen route/controller evidence that a
product surface consumes.  Its first table proves the next-run-only rule for
each migrated capability; its second table invokes each production family.
Only the physical engine factory is substituted.
"""
from __future__ import annotations

import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import Event
from pathlib import Path
from typing import Any, Callable

import pytest

from holdspeak.db import Database
from holdspeak.kernel.inference import InferenceRunCodec
from holdspeak.kernel.prompt_adapter import CanonicalPromptAdapter
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.agent_turn_service import AgentTurnService
from holdspeak.services.errors import NotFound
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.recipe_service import RecipeService
from holdspeak.services.sequence_workflow_service import SequenceWorkflowService
from holdspeak.services.workbench_runner import WorkbenchRunner
from holdspeak.services.workbench_service import WorkbenchService
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
from tests.unit.test_phase143_inference_run_retirement import _legacy_request
from tests.unit.test_phase143_tool_turn_routing import _qualified_manifest


OWNER = Principal(PrincipalKind.OWNER, "placement-matrix-owner")


def _run_sequence(db: Database, broker: Any) -> Any:
    recipe = db.recipes.upsert(recipe_id="recipe-matrix", name="Matrix", system_prompt="system", user_template="{input}")
    db.chains.upsert(chain_id="chain-matrix", name="Matrix", steps=[recipe.id])
    _assign(db, _Case("sequence", "sequence.step", "recipe", recipe.id), "matrix-old", "entry-sequence")
    return asyncio.run(SequenceWorkflowService(db, broker).run_sequence(OWNER, "chain-matrix", {"input": "sequence"}))


def _run_workflow(db: Database, broker: Any) -> Any:
    db.workflows.upsert(workflow_id="workflow-matrix", name="Matrix", prompt="Do: {input}")
    _assign(db, _Case("workflow", "workflow.node"), "matrix-old", "entry-workflow")
    return asyncio.run(SequenceWorkflowService(db, broker).run_workflow(OWNER, "workflow-matrix", {"input": "workflow"}))
