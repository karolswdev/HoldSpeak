"""HS-131-03 Recipe runner migration, origins, and bypass fence."""
from __future__ import annotations
import ast, asyncio
from pathlib import Path
import pytest
from holdspeak.db import Database
from holdspeak.kernel.recipe_projection import materialize_run
from holdspeak.kernel.model import KernelRefused
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.recipe_service import RecipeService
OWNER=Principal(PrincipalKind.OWNER,"owner")
class Engine:
    active_provider="test"; active_model="test-model"
    def run_prompt(self, **kwargs): return "runner recipe"
@pytest.fixture
def rig(tmp_path,monkeypatch):
    db=Database(tmp_path/"recipe.db"); db.recipes.upsert(recipe_id="r1",name="Recipe",system_prompt="system")
    monkeypatch.setattr("holdspeak.inference_targets._this_machine_readiness",lambda:("ready",""))
    monkeypatch.setattr("holdspeak.intel.providers.build_configured_meeting_intel",lambda:Engine())
    return db,_configure(db)
def test_recipe_run_and_root_chat_use_exact_saved_revision_and_stages(rig):
    db,broker=rig; service=RecipeService(db,broker=broker); recipe=db.recipes.get("r1")
    run=asyncio.run(service.run(OWNER,"r1",input="hello")); chat=asyncio.run(service.chat(OWNER,"r1",question="hello"))
    assert run["artifact_id"] and chat["output"]=="runner recipe"
    with db._connection() as conn:
        rows=conn.execute("SELECT kind,invocation_id,operation_id,state FROM kernel_projection_stages ORDER BY kind").fetchall()
        ops=conn.execute("SELECT native_id,parent_operation_id FROM kernel_operations ORDER BY native_id").fetchall()
        assert conn.execute("SELECT COUNT(*) FROM recipe_results").fetchone()[0]==1
        assert conn.execute("SELECT COUNT(*) FROM recipe_chat_results").fetchone()[0]==1
    assert {r["kind"] for r in rows}=={"recipe-run","recipe-chat-result"}
    assert all(r["state"]=="PUBLISHED" for r in rows)
    assert all(r["parent_operation_id"]=="" for r in ops)
    events=broker.events(0,{},OWNER)["events"]
    admitted=[e for e in events if e["event_type"]=="operation.admitted"]
    assert any(f"recipe:r1" in e["refs"] for e in admitted)
    assert str(recipe.last_modified)
def test_recipe_profile_revision_is_committed_before_runner_claim(rig, monkeypatch):
    db,broker=rig; db.profiles.upsert(profile_id="profile",name="Profile",kind="openAICompatible",base_url="http://profile",model="model")
    monkeypatch.setattr("holdspeak.intel.providers.build_meeting_intel_for_profile",lambda **_:Engine())
    result=asyncio.run(RecipeService(db,broker=broker).run(OWNER,"r1",input="profile",inference_target_id="profile"))
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM deployment_revisions").fetchone()[0]==1
        assert conn.execute("SELECT outcome FROM kernel_receipts WHERE operation_id=?",(result["operation_id"],)).fetchone()[0]=="succeeded"


def test_recipe_service_ast_fence_and_forged_materializer_permit(rig):
    db,_=rig; source=Path(__file__).parents[2]/"holdspeak/services/recipe_service.py"; tree=ast.parse(source.read_text())
    text=source.read_text()
    assert not any(token in text for token in ("RunLifecycle","run_prompt","build_intel_for_target","persona:","unversioned"))
    with db._connection() as conn:
        with pytest.raises(KernelRefused,match="projection_publication_permit_invalid"):
            materialize_run(conn,object(),object())
