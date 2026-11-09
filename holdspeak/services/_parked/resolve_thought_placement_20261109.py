"""PARKED 20261109 (lane door/own-choice-park-waist): the Thought runs through the engine door (#2121); no caller is left.
Moved from holdspeak/inference_targets.py. Not imported.
"""


def resolve_thought_placement(db: Any) -> PlacementResolution:
    """Resolve the owner-configured Thought Workbench destination.

    A blank pointer inherits the built-in this-device target. Keeping this
    selector here makes setup, projection, reservation, and the final
    transaction-bound admission recheck name the same target.
    """
    from .config import Config

    config = Config.load()
    pointer = getattr(getattr(config, "thoughts", None), "inference_target_id", None)
    return resolve_placement(db, workbench=pointer)


