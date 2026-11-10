"""The engine families a dictation stage's deployment revision can name (HS-131-09).

``plugins/dictation/assembly.py`` reads these to build the pipeline runtime for
the engine the door's chain names. The model call itself runs on the runner's
engine for that revision (``provider._DoorSpeechAdapter``), so nothing here
binds or rebuilds a target.
"""

from __future__ import annotations

#: The revision engines that mean "run on an OpenAI-compatible endpoint".
ENDPOINT_ENGINES = frozenset({"openai_compatible"})
#: The revision engines that mean "run on this device's configured local engine".
#: ``mlx`` and ``llama_cpp`` are the two on-device DICTATION engines: a
#: dictation-local revision names WHICH loader it froze rather than leaving
#: construction to re-derive it, and it is still a same-device engine — never
#: rebindable, and never confusable with a remote backend.
LOCAL_ENGINES = frozenset(
    {"local", "configured_local_engine", "auto", "", "mlx", "llama_cpp"}
)
#: The revision engines that mean "relay to a mesh node" (handled by the mesh leg).
MESH_ENGINES = frozenset({"mesh", "node_runtime", "mesh_relay"})

__all__ = ["ENDPOINT_ENGINES", "LOCAL_ENGINES", "MESH_ENGINES"]
