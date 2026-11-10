# Parked: Setup owns the one LAN scan; Runs on uses /api/setup/lan.
from holdspeak.concierge_operations import _row, _P

PARKED = (
    # HTTP only: the Engines window's Find on this network, one look per press.
    # setup.lan (setup_operations.py) is the same look in Setup's shape.
    _row("concierge.discover_lan", "discover_lan", ("POST", f"{_P}/discover-lan"), "post_discover_lan",
         lambda s, p, a: s.discover_lan(p),
         "Look once on the owner's private network for engines that answer (/v1/models). It adds no engine.",
         result="{engines: [...], checkedAt}", authority="egress", press=True, refusals=("concierge_lan_refused",)),
)
