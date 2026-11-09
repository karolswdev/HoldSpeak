# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_architecture_tools.py to restore.

# ruff: noqa


# --- test_candidate_patterns_do_not_claim_proof: P1: asserts a dev census tool's regex and category constants
def test_candidate_patterns_do_not_claim_proof():
    mod=module('philo_boundary_census')
    import re
    assert re.search(mod.PATTERNS['http_client'],'import httpx')
    assert re.search(mod.PATTERNS['process_or_shell'],'subprocess.run(args)')
    assert not re.search(mod.PATTERNS['credential_store'],'normal_settings = {}')


# --- test_repository_categories_separate_runtime_and_evidence: P1: asserts a dev census tool's regex and category constants
def test_repository_categories_separate_runtime_and_evidence():
    mod=module('philo_repository_census')
    assert mod.category('holdspeak/kernel/broker.py')=='python-kernel'
    assert mod.category('pm/roadmap/holdspeak/evidence.png')=='roadmap-and-evidence'
    assert mod.category('apple/Sources/Client.swift')=='apple-clients-and-native-runtime'
