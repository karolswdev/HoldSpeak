# PARKED 2026-11-09 (fences diet, pipe/fences-diet): a path citation of the phase-143 surface-fallback census, which is parked itself.
# Nothing replaces it: a shape fence.
# 7 [P3] the census lives outside pm/roadmap


def test_the_census_fence_reads_the_maintained_copy() -> None:
    from tests.unit import test_phase143_surface_fallback_census as census

    assert census.ARTIFACT.relative_to(census.REPO).as_posix() == "docs/internal/surface-fallback-census.md"
