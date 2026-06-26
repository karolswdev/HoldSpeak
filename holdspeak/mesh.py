"""LAN discovery for the mesh (HSM-15-10) — the desktop advertises itself.

When ``holdspeak web`` binds **off-loopback** (LAN mode) it advertises a Bonjour
service so a companion (the iPad) can FIND the computer by name instead of
hand-typing host/port. The advertised service is ``_holdspeak._tcp`` carrying the
device name, the real bound port, and a small TXT record (``name`` / ``version`` /
``requiresToken``). A loopback bind advertises **nothing** — there is no one on
the network to discover it and broadcasting would be needless noise.

Design:

- :func:`should_advertise` is the single decision: advertise iff the bind host is
  not loopback (reuses :mod:`holdspeak.web_auth`'s loopback classifier).
- :func:`resolve_device_name` resolves the advertised name (explicit config name,
  else the machine hostname).
- :func:`build_service_info` constructs the :class:`zeroconf.ServiceInfo` for a
  given name/host/port. This is pure and testable without a live network.
- :class:`MeshAdvertiser` ties registration into the server lifecycle: ``start``
  registers, ``stop`` unregisters + closes. It is **best-effort** — if zeroconf
  is unavailable or registration fails it logs a warning and the server runs on
  unaffected (advertising never blocks or crashes the runtime).

``zeroconf`` is an optional dependency (declared in the ``[meeting]`` extra). It
is imported lazily so the core runtime never requires it.
"""

from __future__ import annotations

import socket
from typing import Any, Optional

from .logging_config import get_logger
from . import web_auth

log = get_logger("mesh")

# The Bonjour service type the iPad's NWBrowser browses for.
MESH_SERVICE_TYPE = "_holdspeak._tcp.local."


def should_advertise(host: Optional[str]) -> bool:
    """True when a bind to ``host`` should be advertised on the LAN.

    Only off-loopback binds are advertised: a loopback bind is reachable only on
    this machine, so there is nothing on the network to discover it (and not
    broadcasting is the privacy-respecting default).
    """
    return not web_auth.is_loopback_host(host)


def resolve_device_name(configured_name: Optional[str]) -> str:
    """Resolve the advertised device name.

    Uses the explicitly configured name when set; otherwise falls back to the
    machine hostname (stripped of a trailing ``.local``), and finally a generic
    label if even the hostname is unavailable.
    """
    name = (configured_name or "").strip()
    if name:
        return name
    try:
        host = socket.gethostname().strip()
    except Exception:
        host = ""
    if host.endswith(".local"):
        host = host[: -len(".local")]
    return host or "HoldSpeak"


def _local_ip_for_host(host: str) -> Optional[bytes]:
    """Best-effort packed IPv4 address to advertise for ``host``.

    A wildcard bind (``0.0.0.0`` / ``::``) has no single address, so we discover
    the primary outbound LAN IP. A concrete bind host is used as-is. Returns the
    4-byte packed form for the zeroconf A record, or ``None`` if undiscoverable
    (zeroconf can still register without an explicit address in that case).
    """
    candidate = (host or "").strip()
    if candidate in ("", "0.0.0.0", "::"):
        candidate = ""
    if candidate:
        try:
            return socket.inet_aton(candidate)
        except OSError:
            candidate = ""
    # Discover the primary outbound interface IP without sending any packets.
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("192.168.255.255", 1))
            ip = probe.getsockname()[0]
        return socket.inet_aton(ip)
    except OSError:
        return None


def build_service_info(
    *,
    device_name: str,
    host: str,
    port: int,
    version: str,
    requires_token: bool,
) -> Any:
    """Construct the ``_holdspeak._tcp`` :class:`zeroconf.ServiceInfo`.

    Pure + importable for tests (no network touched). Raises if zeroconf is not
    installed — callers in the advertiser path guard the import and degrade.
    """
    from zeroconf import ServiceInfo

    safe_name = device_name.strip() or "HoldSpeak"
    # The instance name must be unique within the service type.
    service_name = f"{safe_name}.{MESH_SERVICE_TYPE}"
    properties = {
        "name": safe_name,
        "version": version,
        # TXT values are bytes on the wire; "1"/"0" is the conventional flag form.
        "requiresToken": "1" if requires_token else "0",
    }
    addresses = []
    packed = _local_ip_for_host(host)
    if packed is not None:
        addresses.append(packed)
    return ServiceInfo(
        MESH_SERVICE_TYPE,
        service_name,
        port=int(port),
        properties=properties,
        addresses=addresses or None,
        server=f"{safe_name}.local.",
    )


class MeshAdvertiser:
    """Best-effort Bonjour advertiser tied to the web-server lifecycle.

    ``start`` registers the service (only off-loopback); ``stop`` unregisters and
    closes the zeroconf instance. Every failure is swallowed with a warning so
    advertising can never block or crash the server it advertises.
    """

    def __init__(
        self,
        *,
        device_name: str,
        host: str,
        port: int,
        version: str,
        requires_token: bool,
    ) -> None:
        self.device_name = device_name
        self.host = host
        self.port = port
        self.version = version
        self.requires_token = requires_token
        self._zeroconf: Optional[Any] = None
        self._info: Optional[Any] = None

    @property
    def active(self) -> bool:
        return self._zeroconf is not None and self._info is not None

    def start(self) -> bool:
        """Register the service. Returns True iff it actually advertised."""
        if not should_advertise(self.host):
            log.debug("Mesh advertising skipped (loopback bind %r)", self.host)
            return False
        try:
            from zeroconf import Zeroconf
        except Exception as exc:  # pragma: no cover - exercised via import patch
            log.warning(
                "Mesh advertising unavailable (zeroconf not installed: %s). "
                "Install the [meeting] extra to advertise on the LAN.",
                exc,
            )
            return False
        try:
            info = build_service_info(
                device_name=self.device_name,
                host=self.host,
                port=self.port,
                version=self.version,
                requires_token=self.requires_token,
            )
            zc = Zeroconf()
            zc.register_service(info)
        except Exception as exc:
            log.warning("Mesh advertising failed to register: %s", exc)
            # Tidy up a half-built Zeroconf so we don't leak a socket.
            try:
                if "zc" in locals() and zc is not None:
                    zc.close()
            except Exception:
                pass
            return False
        self._zeroconf = zc
        self._info = info
        log.info(
            "Mesh advertising as %r on %s:%s (requiresToken=%s)",
            resolve_device_name(self.device_name),
            self.host,
            self.port,
            self.requires_token,
        )
        return True

    def stop(self) -> None:
        """Unregister + close. Idempotent and best-effort."""
        zc = self._zeroconf
        info = self._info
        self._zeroconf = None
        self._info = None
        if zc is None:
            return
        try:
            if info is not None:
                zc.unregister_service(info)
        except Exception as exc:
            log.debug("Mesh unregister failed: %s", exc)
        try:
            zc.close()
        except Exception as exc:
            log.debug("Mesh zeroconf close failed: %s", exc)
        log.debug("Mesh advertising stopped")
