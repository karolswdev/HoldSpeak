"""Static host contract for HS-92-02's one-way pairing-token migration."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / "apple/App/MeetingCapture/ProfileKeyStore.swift"
PEER = ROOT / "apple/App/MeetingCapture/CompanionMesh.swift"
DESK = ROOT / "apple/App/MeetingCapture/DeskDioramaStage.swift"


def test_pairing_bearer_uses_device_only_keychain() -> None:
    source = STORE.read_text()
    peer_store = source.split("enum PeerTokenStore", 1)[1]
    assert 'service = "dev.holdspeak.peer.web-auth-token"' in peer_store
    assert "kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly" in peer_store
    assert "migrateFromDefaults" in peer_store
    assert "removeObject(forKey: legacyDefaultsKey)" in peer_store


def test_no_live_surface_persists_pairing_token_in_defaults() -> None:
    companion = PEER.read_text()
    desk = DESK.read_text()
    assert 'defaults.set(token, forKey: "hs.peer.token")' not in companion
    assert '@AppStorage("hs.peer.token")' not in desk
    assert "PeerTokenStore.migrateFromDefaults(defaults)" in companion
    assert "pairedPeer.token" in desk


def test_profile_key_service_is_unchanged_and_separate() -> None:
    source = STORE.read_text()
    profile_store, peer_store = source.split("enum PeerTokenStore", 1)
    assert 'service = "dev.holdspeak.runtimeprofile.key"' in profile_store
    assert 'service = "dev.holdspeak.peer.web-auth-token"' in peer_store
