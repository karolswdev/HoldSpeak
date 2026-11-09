# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_one_clock_one_id.py to restore.

# ruff: noqa


# --- test_each_now_shape_is_the_old_text: P3/P5: re-derives each stamp with Python's own isoformat/strftime; test_the_shapes_stay_apart pins the stored texts
@pytest.mark.parametrize("name", sorted(OLD_BODIES))
@pytest.mark.parametrize("at", [FRACTION, WHOLE], ids=["fraction", "whole"])
def test_each_now_shape_is_the_old_text(frozen, name, at) -> None:
    frozen.at = at
    assert getattr(timestamps, name)() == OLD_BODIES[name](at)


# --- test_the_seconds_z_shape_is_also_the_isoformat_copies_text: P3/P5: re-derives each stamp with Python's own isoformat/strftime; test_the_shapes_stay_apart pins the stored texts
def test_the_seconds_z_shape_is_also_the_isoformat_copies_text(frozen) -> None:
    # Five copies wrote it as isoformat(seconds).replace, four as strftime.
    assert timestamps.utc_now_z() == FRACTION.isoformat(timespec="seconds").replace("+00:00", "Z")


# --- test_the_module_name_is_the_one_function: P8: a hand-kept list of 50 private alias names that must resolve to one function (an HS-S54 refactor census)
@pytest.mark.parametrize(
    "home,name", [(home, name) for home, names in ONE_HOME.items() for name in names],
    ids=lambda v: v if isinstance(v, str) else v.__name__,
)
def test_the_module_name_is_the_one_function(home, name) -> None:
    assert _resolve(name) is home
