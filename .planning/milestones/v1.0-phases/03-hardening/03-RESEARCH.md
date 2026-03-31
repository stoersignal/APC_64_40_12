# Phase 3: Hardening - Research

**Researched:** 2026-03-31
**Domain:** Per-instance state machine isolation, multi-track simultaneous holds, edge-case timing coverage
**Confidence:** HIGH — based on direct source analysis of the completed Phase 2 implementation and the full test suite

---

## Summary

Phase 2 produced a complete implementation of `ToggleMomentaryChannelStripComponent`. Each of the 8 channel strip instances owns its own state variables (`_solo_ticks_delay`, `_mute_ticks_delay`, `_solo_momentary_active`, `_mute_momentary_active`, `_solo_state_before_press`, `_mute_state_before_press`). There is no shared mutable state between instances. The Framework timer callback is also registered per-instance — `SpecialChanStripComponent.__init__` calls `_register_timer_callback(self._on_timer)`, and each instance has its own `_on_timer` call chain. As a result, MULTI-01, MULTI-02, and MULTI-03 are architecturally satisfied by design: two strips pressing Solo simultaneously are two independent state machines that never interact.

The hardening work for Phase 3 is therefore primarily verification work, not code change work. The planner needs to write tests that exercise two `ToggleMomentaryChannelStripComponent` instances simultaneously and confirm the per-instance isolation holds in practice. One narrow real code gap does exist: the `disconnect()` method resets tick counters but does not revert active momentary state if called mid-hold. This is a minor hardening item.

**Primary recommendation:** Write a new test file `tests/test_task3_multi_track.py` that exercises two strip instances simultaneously for each MULTI requirement. Verify zero code changes are needed for the multi-track requirements; fix the disconnect-mid-hold gap as a hardening bonus if desired.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MULTI-01 | User can hold Solo momentary on multiple tracks simultaneously | Per-instance state machine already isolates solo state; `_solo_ticks_delay` and `_solo_momentary_active` are instance attributes — verified in ToggleMomentaryChannelStripComponent.py lines 17-19 |
| MULTI-02 | User can hold Mute momentary on multiple tracks simultaneously | Same per-instance isolation applies to `_mute_ticks_delay` and `_mute_momentary_active` — verified in ToggleMomentaryChannelStripComponent.py lines 21-23 |
| MULTI-03 | User can hold Solo on one track and Mute on another simultaneously | Solo and Mute counters within a single instance also use independent `if` blocks (not `if/elif`) in `_on_timer` — both decrement simultaneously; cross-instance interaction cannot exist |
</phase_requirements>

---

## Multi-Track Architecture Analysis

### Question 1: Does the per-instance state machine already support multi-track holds?

**Answer: YES — by design.** (HIGH confidence — verified by reading source)

Each `ToggleMomentaryChannelStripComponent` instance is an independent object. The six state variables are all instance attributes set in `__init__`:

```python
self._solo_ticks_delay = -1
self._solo_state_before_press = False
self._solo_momentary_active = False
self._mute_ticks_delay = -1
self._mute_state_before_press = False
self._mute_momentary_active = False
```

There are no class-level (shared) variables used as state. No singleton or class-level counter exists. The Framework timer fires per-instance because `_register_timer_callback` registers each instance's own `_on_timer` method, not a shared function.

When track A and track B both have Solo held:
- Strip A: `_solo_ticks_delay` counts down independently
- Strip B: `_solo_ticks_delay` counts down independently
- They do not share references, locks, or shared state

This is the same per-instance isolation that `SpecialChanStripComponent` already uses for fold-delay tracking across 8 tracks — a proven working pattern in this codebase.

### Question 2: Are there race conditions between `_on_timer` ticks and button events?

**Answer: NO** — and this is guaranteed by the Framework, not by the implementation. (HIGH confidence)

The Framework's timer callback fires from the same single main thread that delivers MIDI events. There is no threading. All state mutations happen in the same thread context:
- `_solo_value(127)` (MIDI press) mutates state on main thread
- `_on_timer()` (tick) mutates state on main thread
- `_solo_value(0)` (MIDI release) mutates state on main thread

No mutex, lock, or atomic operation is needed. The single-thread constraint is enforced by the Framework's architecture and is verified by PITFALLS.md (Pitfall 6 confirms threading is prohibited and unnecessary).

### Question 3: What edge cases exist for rapid consecutive presses on the same button?

**Answer: All covered by existing tests** — but worth confirming with explicit multi-press tests. (HIGH confidence)

The existing tests verify:
- Tick counter resets to `-1` on release (`test_release_always_resets_ticks_delay`)
- Second press after release starts fresh (`test_timer_inactive_solo_not_decremented`)

What is NOT explicitly tested and should be:
- **Rapid press-release-press** (two short presses back to back): second press must behave identically to the first
- **Press while momentary active** (pathological: press during another press — can happen if the controller firmware emits a note-on before note-off on retrigger): the `_solo_momentary_active` guard in `_handle_toggle_momentary` sets it to `False` on release, so a second press starts clean

**One edge case to verify in tests:** If `_solo_momentary_active` is `True` when a new press arrives (hardware sends note-on without prior note-off — MIDI clock jitter scenario), what happens? The current `_handle_toggle_momentary` code checks `value != 0` first and proceeds to invert state and reset `_solo_ticks_delay = LONG_PRESS_DELAY`. The `_solo_momentary_active` flag is NOT cleared on press-down, only on release. This is actually correct — the flag stays set and the release handler will still revert. But it deserves a test to document and protect this behavior.

### Question 4: Does the existing test suite cover multi-track scenarios?

**Answer: NO.** (HIGH confidence — verified by reading all test files)

Current coverage (43 tests across 2 files):
- `test_task1_toggle_momentary_values.py` — single-strip behavioral tests for press/release paths
- `test_task2_timer_and_shift_guards.py` — single-strip timer countdown and shift guard tests

**Completely absent:** Any test that creates two `ToggleMomentaryChannelStripComponent` instances and drives them simultaneously. This is the primary Phase 3 testing gap.

### Question 5: What code changes (if any) are needed?

**Answer: Zero code changes are required to satisfy MULTI-01/02/03.** One optional hardening improvement exists.

**Required changes:** None. The per-instance architecture already satisfies all three MULTI requirements.

**Optional hardening — `disconnect()` mid-hold revert:** The current `disconnect()` method:
```python
def disconnect(self):
    self._solo_ticks_delay = -1
    self._mute_ticks_delay = -1
    SpecialChanStripComponent.disconnect(self)
```
It resets tick counters but does NOT revert `self._track.solo` or `self._track.mute` if a momentary hold is in progress when disconnect fires. This mirrors what `set_solo_button(None)` does handle (it checks `_solo_momentary_active` and reverts). For a live performance scenario where the controller is physically disconnected mid-hold, the track would be left in the momentary-inverted state permanently. This is a minor hardening improvement that the planner may include as an optional task.

---

## Standard Stack

No new libraries needed. The existing test infrastructure handles Phase 3 tests with no additions.

| Component | Version | Purpose | Status |
|-----------|---------|---------|--------|
| Python 3 unittest | stdlib | Test runner | Already in use |
| `tests/framework_stubs.py` | Project-local | Framework simulation without Live | Sufficient — no additions needed |
| `tests/__init__.py` | Project-local | Test package marker | Already present |

**Test run command:**
```bash
python3 -m unittest discover tests -v
```

---

## Architecture Patterns

### Pattern: Two-Instance Simultaneous Test

The test harness already knows how to create one strip instance. Creating two is identical — just call `_make_strip()` twice and drive both independently:

```python
# Source: tests/test_task2_timer_and_shift_guards.py — existing _make_strip pattern
def test_two_strips_solo_simultaneously(self):
    strip_a = _make_strip(track_solo=False)
    strip_b = _make_strip(track_solo=False)
    # Both press Solo at the same time (same timer tick is irrelevant — per-instance)
    strip_a._solo_value(127)
    strip_b._solo_value(127)
    # Both tracks inverted on press-down
    self.assertTrue(strip_a._track.solo)
    self.assertTrue(strip_b._track.solo)
    # Let both reach threshold
    strip_a._solo_momentary_active = True
    strip_b._solo_momentary_active = True
    # Release strip A; strip B still held
    strip_a._solo_value(0)
    self.assertFalse(strip_a._track.solo)   # A reverted
    self.assertTrue(strip_b._track.solo)    # B still held — unaffected
    # Release strip B
    strip_b._solo_value(0)
    self.assertFalse(strip_b._track.solo)   # B reverted
```

### Pattern: Cross-Button Simultaneous Test (MULTI-03)

Solo on strip A and Mute on strip B are not just different instances — they use different state variables even within one instance. The existing `test_both_counters_decrement_independently` in `test_task2` already covers the within-instance case. The Phase 3 test adds the cross-instance case:

```python
def test_solo_on_one_track_mute_on_another(self):
    strip_a = _make_strip(track_solo=False)
    strip_b = _make_strip(track_mute=False)
    strip_a._solo_value(127)   # Solo held on track A
    strip_b._mute_value(127)   # Mute held on track B
    # Both active
    self.assertTrue(strip_a._track.solo)
    self.assertTrue(strip_b._track.mute)
    # Release solo on A
    strip_a._solo_momentary_active = True
    strip_a._solo_value(0)
    self.assertFalse(strip_a._track.solo)   # A solo reverted
    self.assertTrue(strip_b._track.mute)    # B mute unaffected
    # Release mute on B
    strip_b._mute_momentary_active = True
    strip_b._mute_value(0)
    self.assertFalse(strip_b._track.mute)   # B mute reverted
```

### Anti-Patterns to Avoid

- **Adding shared class-level state:** Do not introduce `ToggleMomentaryChannelStripComponent._active_holds = []` or similar. This would break per-instance isolation.
- **Testing only one instance:** Multi-track tests with a single instance only prove single-track behavior. Two instance objects are required to prove MULTI-01/02/03.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Simulating simultaneous timer ticks across instances | Custom tick dispatcher | Just call `_on_timer()` on each instance separately | Ticks are independent; "simultaneous" in hardware is just two separate calls in the same 100ms window |
| Cross-instance state inspection | Shared registry or observer | Direct attribute reads on each instance | Test isolation is cleaner; the stubs already expose all state |

---

## Common Pitfalls

### Pitfall A: Concluding Multi-Track Works Without Proof

**What goes wrong:** Reasoning "it must work because the state is per-instance" without writing a test that actually runs two instances simultaneously. The architecture supports it, but a coding mistake in the helper could accidentally reference a class-level variable.

**Prevention:** Write the two-instance tests before considering MULTI-01/02/03 done.

### Pitfall B: disconnect() Leaving Track in Momentary State

**What goes wrong:** Controller physically disconnected or script reloaded while a button is held. `disconnect()` resets tick counters but does not check `_solo_momentary_active` or `_mute_momentary_active`. Track stays in the inverted state permanently.

**Why it happens:** `set_solo_button(None)` handles this case correctly (lines 53-59 in the current implementation) but `disconnect()` only zeros the counters (lines 70-73).

**How to avoid:** In `disconnect()`, add the same guard that `set_solo_button()` uses before calling `SpecialChanStripComponent.disconnect(self)`.

**Warning signs:** Track stuck muted/soloed after controller reconnect with no obvious cause.

### Pitfall C: Rapid Consecutive Press Accumulation

**What goes wrong:** Second press on same button within one timer tick window. The tick counter starts at `LONG_PRESS_DELAY = 4` on press-down and is reset to `-1` on release. If a release and re-press happen in the same 100ms tick, the counter resets correctly because `_solo_value(0)` is called before `_solo_value(127)`. MIDI protocol guarantees note-off before note-on for retrigger.

**Status:** This is NOT a real risk given MIDI ordering guarantees, but worth a test comment documenting the assumption.

---

## Code Examples

### Existing `disconnect()` (current — has gap)

```python
# ToggleMomentaryChannelStripComponent.py lines 69-72
def disconnect(self):
    self._solo_ticks_delay = -1
    self._mute_ticks_delay = -1
    SpecialChanStripComponent.disconnect(self)  # handles _unregister_timer_callback
```

### Optional hardened `disconnect()` (add momentary revert)

```python
def disconnect(self):
    # Revert any active momentary hold before disconnecting
    if self._solo_momentary_active and self._track is not None:
        self._track.solo = self._solo_state_before_press
        self._solo_momentary_active = False
    if self._mute_momentary_active and self._track is not None:
        self._track.mute = self._mute_state_before_press
        self._mute_momentary_active = False
    self._solo_ticks_delay = -1
    self._mute_ticks_delay = -1
    SpecialChanStripComponent.disconnect(self)
```

---

## State of the Art

| Area | Current State | Phase 3 Action |
|------|--------------|----------------|
| MULTI-01 (simultaneous solo holds) | Architecturally satisfied, not test-verified | Write two-instance solo test |
| MULTI-02 (simultaneous mute holds) | Architecturally satisfied, not test-verified | Write two-instance mute test |
| MULTI-03 (cross-type simultaneous) | Architecturally satisfied, not test-verified | Write cross-instance solo+mute test |
| disconnect() mid-hold | Minor gap — reverts counters, not momentary state | Optional hardening task |
| Rapid consecutive presses | Covered by existing tests (reset confirmed) | Document assumption only |
| Test infrastructure | 43 tests, all green, `python3 -m unittest discover tests` | No changes to runner needed |

---

## Open Questions

1. **Should disconnect() hardening be a required task or optional?**
   - What we know: The gap exists. The revert code pattern is already proven in `set_solo_button()`.
   - What's unclear: In practice, the controller sends MIDI note-off on physical disconnect before the script fires `disconnect()`, which would trigger `_solo_value(0)` and clean up the momentary state naturally. This would make the `disconnect()` gap theoretical rather than observable.
   - Recommendation: Include as a single-task hardening item clearly labeled "optional/low risk" — easy to implement, zero risk of regression.

2. **Should TrackStub be extended with a `name` attribute for multi-instance test readability?**
   - What we know: Tests currently use `strip._track.solo` which is sufficient for assertions.
   - Recommendation: Not needed — the test pattern of `strip_a` / `strip_b` local variable names is clear enough.

---

## Sources

### Primary (HIGH confidence)

- `/Users/stoersignal/Dev/APC_64_40_12/ToggleMomentaryChannelStripComponent.py` — Complete Phase 2 implementation, verified by reading source directly
- `/Users/stoersignal/Dev/APC_64_40_12/tests/test_task1_toggle_momentary_values.py` — 19 existing tests, all passing
- `/Users/stoersignal/Dev/APC_64_40_12/tests/test_task2_timer_and_shift_guards.py` — 24 existing tests, all passing (confirmed: `python3 -m unittest discover tests` = 43 tests OK)
- `/Users/stoersignal/Dev/APC_64_40_12/tests/framework_stubs.py` — Stub infrastructure, reusable as-is
- `.planning/research/PITFALLS.md` — Pitfall 6 confirms single-thread safety; Pitfall 10 documents disable-mid-press scenario

### Secondary (MEDIUM confidence)

- `.planning/research/ARCHITECTURE.md` — Architecture decision to use per-instance state, confirmed by reading the resulting implementation
- `.planning/phases/02-core-logic/02-CONTEXT.md` — D-08, D-09 decisions that produced the DRY helper pattern

---

## Metadata

**Confidence breakdown:**
- Multi-track isolation claim: HIGH — verified by reading every state variable in the implementation; no class-level mutable state exists
- Test coverage gap claim: HIGH — verified by reading all test files; no two-instance test exists anywhere
- disconnect() gap: HIGH — verified by reading the method; `_solo_momentary_active` is not checked
- Race condition absence: HIGH — confirmed by Framework single-thread architecture documented in PITFALLS.md

**Research date:** 2026-03-31
**Valid until:** Indefinite — the conclusions are structural facts about the current codebase, not external library claims
