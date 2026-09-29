"""The Room's services on the one composition root (PHILO-9-01), carved from ``composition.py``.

``install_from_web_context`` calls :func:`compose_room_services` once: the
hub's own instances when its context holds them, else the same bare builds
the MCP project family makes off-hub, put on BOTH the context and the root.
"""

from __future__ import annotations

from typing import Any


def compose_room_services(services: Any, ctx: Any, db: Any, observer: Any) -> None:
    """PHILO-9-01: the Room's four bound services, the hub's own when it has them."""
    def _held(name: str) -> Any:
        instance = getattr(services, name, None)
        return instance if instance is not None else getattr(ctx, name, None)

    project = _held("project_service")
    delta = _held("project_delta_service")
    if project is None or delta is None:
        from holdspeak.services.project_delta_service import ProjectDeltaService
        from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector
        from holdspeak.services.project_service import ProjectService

        if delta is None:
            delta = ProjectDeltaService(db, collector=ProjectEvidenceCollector(db))
        if project is None:
            project = ProjectService(db, observer=observer, delta_service=delta)
        if getattr(delta, "_project_service", None) is None:
            delta.attach_project_service(project)
    update = _held("project_update_service")
    if update is None:
        from holdspeak.services.project_update_service import ProjectUpdateService

        update = ProjectUpdateService(db, project_service=project, delta_service=delta)
    door = _held("project_door_service")
    if door is None:
        from holdspeak.services.project_door_service import ProjectDoorService
        from holdspeak.services.watch_service import WatchService

        door = ProjectDoorService(
            project_service=project,
            watch_service=_held("watch_service") or WatchService(db, observer=observer),
        )
    # PHILO-9-02: the steward, the watches, the connections and the suggested
    # sources (the hub composes each; a partial context gets the bare builds
    # the MCP project family makes off-hub).
    watch = _held("watch_service")
    if watch is None:
        from holdspeak.services.watch_service import WatchService

        watch = WatchService(db, observer=observer)
    steward = _held("project_steward_service")
    if steward is None:
        from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector
        from holdspeak.services.project_steward_service import ProjectStewardService

        steward = ProjectStewardService(db, ProjectEvidenceCollector(db), delta,
                                        update_service=update, project_service=project)
    connections = _held("connections_service")
    if connections is None:
        from holdspeak.services.connections_service import ConnectionsService

        connections = ConnectionsService()
    suggested = _held("suggested_source_service")
    if suggested is None:
        from holdspeak.services.suggested_source_service import SuggestedSourceService

        suggested = SuggestedSourceService(db, project_service=project)
    channels = _held("channel_service")
    if channels is None:
        # PHILO-10-01: the Send's one service (every channel.* operation).
        from holdspeak.services.channel_service import ChannelService

        channels = ChannelService(db)
    for name, instance in (("project_service", project), ("project_delta_service", delta),
                           ("project_update_service", update), ("project_door_service", door),
                           ("watch_service", watch), ("project_steward_service", steward),
                           ("connections_service", connections), ("suggested_source_service", suggested),
                           ("channel_service", channels)):
        setattr(services, name, instance)
        try:
            setattr(ctx, name, instance)
        except AttributeError:  # pragma: no cover - a non-dataclass stand-in
            pass
