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

from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .db import Database
from .runs import RunManager


class CreateRunBody(BaseModel):
    config: Optional[dict] = None
    deck: Optional[str] = None
    lan: bool = False
    port: Optional[int] = None


class RestartRunBody(BaseModel):
    config: Optional[dict] = None
    deck: Optional[str] = None
    lan: Optional[bool] = None


def create_app(manager: RunManager | None = None) -> FastAPI:
    app = FastAPI(title="HoldSpeak UAT Conductor", version="0.1.0")
    app.state.manager = manager or RunManager(Database())

    def mgr() -> RunManager:
        return app.state.manager

    @app.get("/api/health")
    def conductor_health() -> Any:
        runs = mgr().list_runs()
        return {
            "status": "ok",
            "service": "uat-conductor",
            "runs": len(runs),
            "up": sum(1 for r in runs if r.status == "up"),
        }

    @app.get("/")
    def index() -> Any:
        # The guided site (HSU-1-04) builds to static assets served here.
        return JSONResponse(
            {
                "service": "HoldSpeak UAT Conductor",
                "note": "The guided site lands in HSU-1-04. API is under /api.",
                "health": "/api/health",
            }
        )

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

    @app.on_event("shutdown")
    def _shutdown() -> None:
        mgr().teardown_all()

    return app
