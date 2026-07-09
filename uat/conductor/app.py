"""The conductor's FastAPI app — the harness's own front door.

Localhost-only by default (``UAT_HOST`` opts it onto the LAN for device
sittings). It serves the run-lifecycle API in HSU-1-01; the induction
verbs (HSU-1-02), scenario/coverage reads (HSU-1-03), the guided site +
verdict writes (HSU-1-04), and the debrief (HSU-1-05) mount onto this same
app in later stories.

Handlers that boot or tear down a product are plain ``def`` so FastAPI
runs them in its threadpool — the blocking subprocess work never stalls
the event loop that keeps the site responsive while the product is being
deliberately broken.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .db import Database
from .runs import RunManager
from .sittings import SittingError, SittingManager


def _site_dist() -> Path:
    return Path(__file__).resolve().parents[2] / "uat" / "web" / "dist"


class CreateRunBody(BaseModel):
    config: Optional[dict] = None
    deck: Optional[str] = None
    lan: bool = False
    port: Optional[int] = None


class RestartRunBody(BaseModel):
    config: Optional[dict] = None
    deck: Optional[str] = None
    lan: Optional[bool] = None


class ApplyRecipeBody(BaseModel):
    allow_intel: bool = True


class SpawnNodeBody(BaseModel):
    name: str


class CreateSittingBody(BaseModel):
    pack: str
    deck: Optional[str] = None
    lan: bool = False


class StageBody(BaseModel):
    scenario_id: str


class VerdictBody(BaseModel):
    scenario_id: str
    step_index: int
    surface: str
    verdict: str
    note: Optional[str] = None
    shot_path: Optional[str] = None
    started_at: Optional[str] = None


class AfterBody(BaseModel):
    scenario_id: str
    step_index: int


class TriageBody(BaseModel):
    triage_state: str
    disposition: Optional[str] = None


def create_app(manager: RunManager | None = None) -> FastAPI:
    app = FastAPI(title="HoldSpeak UAT Conductor", version="0.1.0")
    app.state.manager = manager or RunManager(Database())

    def mgr() -> RunManager:
        return app.state.manager

    app.state.sittings = SittingManager(app.state.manager, app.state.manager.db)

    def sit() -> SittingManager:
        return app.state.sittings

    from .debrief import DebriefGenerator

    app.state.debrief = DebriefGenerator(app.state.manager, app.state.manager.db)

    def debrief() -> DebriefGenerator:
        return app.state.debrief

    @app.get("/api/health")
    def conductor_health() -> Any:
        runs = mgr().list_runs()
        return {
            "status": "ok",
            "service": "uat-conductor",
            "runs": len(runs),
            "up": sum(1 for r in runs if r.status == "up"),
        }

    @app.post("/api/runs", status_code=201)
    def create_run(body: CreateRunBody) -> Any:
        run = mgr().create_run(
            config=body.config, deck=body.deck, lan=body.lan, port=body.port
        )
        return run.to_public()

    @app.get("/api/runs")
    def list_runs() -> Any:
        return {"runs": [r.to_public() for r in mgr().list_runs()]}

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: str) -> Any:
        run = mgr().get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"no such run: {run_id}")
        return run.to_public()

    @app.post("/api/runs/{run_id}/restart")
    def restart_run(run_id: str, body: RestartRunBody) -> Any:
        try:
            run = mgr().restart(
                run_id, config=body.config, deck=body.deck, lan=body.lan
            )
        except KeyError:
            raise HTTPException(status_code=404, detail=f"no live run: {run_id}")
        return run.to_public()

    @app.delete("/api/runs/{run_id}")
    def delete_run(run_id: str) -> Any:
        run = mgr().teardown(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"no such run: {run_id}")
        return run.to_public()

    @app.get("/api/runs/{run_id}/logs")
    def run_logs(run_id: str, n: int = 80) -> Any:
        run = mgr().get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"no such run: {run_id}")
        return mgr().logs(run_id, n=n)

    # --- induction engine (HSU-1-02) -------------------------------------

    @app.get("/api/decks")
    def list_decks() -> Any:
        return {"decks": mgr().decks.all()}

    @app.get("/api/recipes")
    def list_recipes() -> Any:
        return {"recipes": mgr().recipes.registry.all()}

    @app.post("/api/runs/{run_id}/recipes/{name}")
    def apply_recipe(run_id: str, name: str, body: ApplyRecipeBody) -> Any:
        if mgr().get(run_id) is None:
            raise HTTPException(status_code=404, detail=f"no such run: {run_id}")
        from .induction.recipes import RecipeError, RecipeVerifyError

        try:
            result = mgr().apply_recipe(run_id, name, allow_intel=body.allow_intel)
        except RecipeVerifyError as exc:
            # A recipe that cannot verify itself fails loudly — 422 with the
            # probe report so the caller sees exactly which assertion missed.
            return JSONResponse(
                status_code=422,
                content={"error": str(exc), "result": exc.result.to_dict()},
            )
        except RecipeError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return result.to_dict()

    @app.post("/api/runs/{run_id}/nodes", status_code=201)
    def spawn_node(run_id: str, body: SpawnNodeBody) -> Any:
        try:
            return mgr().spawn_node(run_id, body.name)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"no live run: {run_id}")

    @app.get("/api/runs/{run_id}/nodes")
    def list_nodes(run_id: str) -> Any:
        if mgr().get(run_id) is None:
            raise HTTPException(status_code=404, detail=f"no such run: {run_id}")
        return {"nodes": mgr().list_nodes(run_id)}

    @app.delete("/api/runs/{run_id}/nodes/{name}")
    def kill_node(run_id: str, name: str) -> Any:
        killed = mgr().kill_node(run_id, name)
        if not killed:
            raise HTTPException(status_code=404, detail=f"no such node: {name}")
        return {"name": name, "killed": True}

    # --- the scenario contract + feature ledger (HSU-1-03) ---------------

    from .contract.ledger import FeatureLedger
    from .contract import scenarios as scen_mod
    from .contract.coverage import pack_coverage
    from .contract.scenarios import ScenarioError, load_pack, validate_scenario

    def _ledger() -> FeatureLedger:
        cached = getattr(app.state, "ledger", None)
        if cached is None:
            cached = FeatureLedger.load()
            app.state.ledger = cached
        return cached

    def _recipe_names() -> set[str]:
        return set(mgr().recipes.registry.names())

    def _deck_names() -> set[str]:
        return set(mgr().decks.names())

    @app.get("/api/features")
    def features() -> Any:
        ledger = _ledger()
        return {
            "version": ledger.raw.get("version"),
            "feature_count": len(ledger.features),
            "phases_total": len(ledger.phase_map),
            "features": [
                {
                    "key": f.key,
                    "title": f.title,
                    "domain": f.domain,
                    "phases": f.phases,
                    "surfaces": f.surfaces,
                    "priority": f.priority,
                    "status": f.status,
                }
                for f in ledger.features
            ],
        }

    @app.get("/api/packs")
    def packs() -> Any:
        ledger = _ledger()
        out = []
        for name in scen_mod.list_packs():
            try:
                scenarios = load_pack(name)
            except ScenarioError as exc:
                out.append({"pack": name, "error": str(exc)})
                continue
            cov = pack_coverage(scenarios, ledger)
            out.append(
                {
                    "pack": name,
                    "scenario_count": len(scenarios),
                    "coverage": {"overall": cov["overall"], "web": cov["web"], "ipad": cov["ipad"], "iphone": cov["iphone"]},
                    "expected_verdicts": cov["expected_verdicts"],
                }
            )
        return {"packs": out}

    @app.get("/api/packs/{pack}")
    def pack_detail(pack: str) -> Any:
        ledger = _ledger()
        try:
            scenarios = load_pack(pack)
        except ScenarioError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        errors: list[str] = []
        for s in scenarios:
            errors += validate_scenario(
                s, ledger_keys=ledger.keys(), recipe_names=_recipe_names(), deck_names=_deck_names()
            )
        return {
            "pack": pack,
            "scenarios": [s.to_dict() for s in scenarios],
            "coverage": pack_coverage(scenarios, ledger),
            "validation_errors": errors,
        }

    # --- sittings (HSU-1-04) ---------------------------------------------

    @app.post("/api/sittings", status_code=201)
    def create_sitting(body: CreateSittingBody) -> Any:
        from .contract.scenarios import ScenarioError

        try:
            return sit().create(body.pack, deck_override=body.deck, lan=body.lan)
        except ScenarioError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except SittingError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.get("/api/sittings")
    def list_sittings() -> Any:
        return {"sittings": sit().list()}

    @app.get("/api/sittings/{sitting_id}")
    def get_sitting(sitting_id: str) -> Any:
        try:
            return sit().get(sitting_id)
        except SittingError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    @app.post("/api/sittings/{sitting_id}/stage")
    def stage_sitting(sitting_id: str, body: StageBody) -> Any:
        try:
            return sit().stage(sitting_id, body.scenario_id)
        except SittingError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    @app.post("/api/sittings/{sitting_id}/verdicts")
    def cast_verdict(sitting_id: str, body: VerdictBody) -> Any:
        try:
            return sit().cast_verdict(
                sitting_id,
                scenario_id=body.scenario_id,
                step_index=body.step_index,
                surface=body.surface,
                verdict=body.verdict,
                note=body.note,
                shot_path=body.shot_path,
                started_at=body.started_at,
            )
        except SittingError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post("/api/sittings/{sitting_id}/shots")
    def upload_shot(
        sitting_id: str,
        scenario_id: str = Form(...),
        step_index: int = Form(...),
        surface: str = Form(...),
        file: UploadFile = File(...),
    ) -> Any:
        suffix = Path(file.filename or "shot.png").suffix or ".png"
        data = file.file.read()
        try:
            path = sit().save_shot(sitting_id, scenario_id, step_index, surface, data, suffix=suffix)
        except SittingError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        return {"shot_path": path}

    @app.post("/api/sittings/{sitting_id}/after")
    def run_after(sitting_id: str, body: AfterBody) -> Any:
        try:
            return {"performed": sit().run_after_actions(sitting_id, body.scenario_id, body.step_index)}
        except SittingError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    @app.post("/api/sittings/{sitting_id}/finish")
    def finish_sitting(sitting_id: str) -> Any:
        try:
            return sit().finish(sitting_id)
        except SittingError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    # --- debrief + triage (HSU-1-05) -------------------------------------

    @app.post("/api/sittings/{sitting_id}/debrief")
    def generate_debrief(sitting_id: str) -> Any:
        try:
            return debrief().generate(sitting_id)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"no such sitting: {sitting_id}")

    @app.get("/api/sittings/{sitting_id}/debrief")
    def read_debrief(sitting_id: str) -> Any:
        try:
            return debrief().read(sitting_id)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"no such sitting: {sitting_id}")

    @app.patch("/api/findings/{finding_id}")
    def triage_finding(finding_id: str, body: TriageBody) -> Any:
        valid = {"untriaged", "fix", "wont-fix", "by-design", "duplicate"}
        if body.triage_state not in valid:
            raise HTTPException(status_code=400, detail=f"triage_state must be one of {sorted(valid)}")
        if not mgr().db.set_triage(finding_id, body.triage_state, body.disposition):
            raise HTTPException(status_code=404, detail=f"no such finding: {finding_id}")
        return mgr().db.get_finding(finding_id)

    @app.get("/api/sittings/{sitting_id}/findings/backlog-block")
    def backlog_block(sitting_id: str) -> Any:
        sitting = mgr().db.get_sitting(sitting_id)
        if sitting is None:
            raise HTTPException(status_code=404, detail=f"no such sitting: {sitting_id}")
        return {"block": debrief().backlog_block(sitting["run_id"])}

    @app.on_event("shutdown")
    def _shutdown() -> None:
        mgr().teardown_all()

    # The built guided site (uat/web/dist) is served at / when present. Until it
    # is built, a JSON pointer answers at / so the conductor is still usable.
    dist = _site_dist()
    if dist.exists() and (dist / "index.html").exists():
        app.mount("/", StaticFiles(directory=str(dist), html=True), name="site")
    else:
        @app.get("/")
        def index() -> Any:
            return JSONResponse(
                {
                    "service": "HoldSpeak UAT Conductor",
                    "note": "The guided site is not built. Run: npm --prefix uat/web install && npm --prefix uat/web run build",
                    "health": "/api/health",
                }
            )

    return app
