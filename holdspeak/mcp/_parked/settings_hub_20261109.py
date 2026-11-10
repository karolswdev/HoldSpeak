# Parked: settings.hub is produced from the SettingsHubService descriptor.

# Old tool declaration:
# _mcp_tool("settings.hub", "Read the settings hub row facts: module state tokens for the settings truth table.", {}),

def _dispatch(name, args, db, principal):
    if name == "settings.hub":
        from holdspeak.config import Config, CONFIG_FILE
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService
        config = Config.load()
        engines = 0; groups_set = 0; default_set = False
        try:
            from holdspeak.services.model_library_service import ModelLibraryApplicationService
            from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
            setup = InferenceSetupApplicationService(db)
            lib = ModelLibraryApplicationService(db, setup_service=setup)
            lib_data = lib.get_library(principal)
            engines = lib_data.get("summary", {}).get("ready_count", 0)
        except Exception:
            pass
        try:
            from holdspeak.kernel.runtime import _configure
            broker = _configure(db)
            asn_svc = InferenceAssignmentService(db, registry=broker.inference_capability_registry)
            asn = asn_svc.assignment_summary(principal)
            for row in asn.get("rows", []):
                if row.get("id") == "global":
                    default_set = row.get("status") == "assigned"
                elif row.get("status") == "assigned":
                    groups_set += 1
        except Exception:
            pass
        connected = 0
        try:
            connected = len(db.automations.list_provider_connections())
        except Exception:
            pass
        loops = 0
        try:
            loops = len(db.cadence.list_loops())
        except Exception:
            pass
        import os
        written_at = None
        try:
            if CONFIG_FILE.exists():
                written_at = os.path.getmtime(CONFIG_FILE)
        except Exception:
            pass
        # HS-171-02: heartbeat rhythm mirror.
        heartbeat_rhythm: dict = {"loops": loops}
        try:
            from holdspeak.services.heartbeat_service import HeartbeatService
            hb = HeartbeatService(db)
            heartbeat_rhythm = hb.hub_rhythm()
        except Exception:
            heartbeat_rhythm["sweepEveryMinutes"] = 15
            heartbeat_rhythm["nextSweepAt"] = None
            heartbeat_rhythm["lastSweepAt"] = None
            heartbeat_rhythm["quiet"] = {"start": 22, "end": 8, "held": False}
        meetings_host = None
        # PHILO-15 B33: the summary engine is the queue's route (the HTTP twin
        # reads the same fact), never the legacy config pointer alone.
        summary_fact: dict = {"engine_set": None, "off": False, "host": None}
        try:
            from holdspeak.services.meeting_route_projection import summary_engine_fact
            summary_fact = summary_engine_fact(db)
            meetings_host = summary_fact.get("host")
        except Exception:
            pass
        try:
            if not meetings_host and config.meeting.intel_profile_id:
                from holdspeak.intel.providers import resolve_meeting_placement as _rmp, endpoint_host as _eh
                _pl = _rmp(config.meeting)
                if _pl.profile_id:
                    if _pl.node:
                        meetings_host = str(_pl.node)
                    else:
                        _h = _eh(_pl.base_url)
                        meetings_host = _h if _h else (_pl.boundary or "local")
        except Exception:
            pass
        return {"models": {"engines": engines, "groupsSet": groups_set, "defaultSet": default_set}, "connections": {"connected": connected}, "voice": {"live": config.dictation.pipeline.enabled, "target": config.dictation.pipeline.target_profile_override or "auto"}, "meetings": {"intelligence": config.meeting.intel_enabled, "engineSet": summary_fact.get("engine_set"), "summariesOff": bool(summary_fact.get("off")), "auto": config.meeting.intelligence_auto, "host": meetings_host}, "rhythm": heartbeat_rhythm, "sounds": {"on": config.ui.desk_sounds}, "system": {"host": "THIS DEVICE", "mesh": bool(getattr(config.mesh, "device_name", ""))}, "posture": config.control_mode, "writtenAt": written_at}
