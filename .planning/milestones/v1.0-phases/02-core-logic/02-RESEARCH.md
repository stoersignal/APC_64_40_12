# Phase 2: Core Logic - Research

**Researched:** 2026-03-31
**Domain:** Ableton _Framework ChannelStripComponent override — toggle/momentary state machine
**Confidence:** HIGH — all findings verified against live source files in the project repo

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**State Machine Flow**
- D-01: Toggle immediately on press-down — state change fires at button press, not at threshold. Zero latency on all paths.
- D-02: On release: if `_ticks_delay > 0` (less than 400ms held), state stays toggled (short press = toggle). If `_ticks_delay <= 0` (reached threshold), revert to `_state_before_press` (long press = momentary revert).
- D-03: Strict threshold boundary — if released before tick count reaches 0, it's a toggle. No fuzzy grace window.
- D-04: Press-down starts the tick countdown at `LONG_PRESS_DELAY` (4). Timer decrements each tick. At 0, the press is classified as "long" for release behavior.

**Already-Active Handling**
- D-05: Same pattern for already-active tracks — press-down always inverts current state immediately. If track is already soloed, press-down unsolos. Release after threshold restores solo. Release before threshold keeps unsolo (toggle off).
- D-06: Short press on already-soloed/muted track toggles it off (unsolo/unmute) — same as current behavior, no special casing.

**Shift Button Guard**
- D-07: Basic reset guard when `set_solo_button(None)` or `set_mute_button(None)` is called mid-hold: reset tick counter to -1, if `_momentary_active` is True revert state to `_state_before_press`, set `_momentary_active = False`. Prevents stuck states from shift transitions.

**Implementation Split**
- D-08: Shared helper method `_handle_toggle_momentary(value, track_property, ticks_attr, state_attr, momentary_attr)` called by both `_solo_value` and `_mute_value`. DRY — one place to fix bugs.
- D-09: `_on_timer` also uses shared approach: check both solo and mute tick counters, decrement if active.

**LED Feedback**
- D-10: No additional LED code needed — framework's `_on_solo_changed`/`_on_mute_changed` listeners fire automatically when `track.solo`/`track.mute` changes, updating LEDs in real-time. Confirmed in Phase 1 research.

### Claude's Discretion
- Method parameter naming and internal variable naming within the shared helper
- Whether to use `getattr`/`setattr` or explicit attribute access in the helper
- Comment style within the new methods

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CORE-01 | Short press (<400ms) on Solo button toggles solo state on/off | D-01/D-02: toggle fires at press-down; release before threshold keeps it (no revert) |
| CORE-02 | Long press (>=400ms) on Solo button acts momentary — solo activates on press-down, reverts on release | D-01/D-02/D-04: state inverted at press-down, tick countdown, revert at release when threshold crossed |
| CORE-03 | Short press (<400ms) on Mute button toggles mute state on/off | Same state machine mirrored to mute; `_mute_value` override |
| CORE-04 | Long press (>=400ms) on Mute button acts momentary — mute activates on press-down, reverts on release | Same state machine mirrored to mute |
| CORE-05 | State change fires immediately at press-down (no classification delay) | D-01 locked; state written in `value != 0` branch before timer starts |
| CORE-06 | Long press on already-soloed track temporarily unsolos while held, restores on release | D-05: `not current_state` inversion — works uniformly whether track is active or inactive |
| CORE-07 | Long press on already-muted track temporarily unmutes while held, restores on release | Same inversion logic applied to mute |
| LED-01 | Solo button LED reflects real-time solo state during momentary holds | D-10: `_on_solo_changed` fires on every `track.solo` write; no manual LED calls needed |
| LED-02 | Mute button LED reflects real-time mute state during momentary holds | D-10: `_on_mute_changed` fires on every `track.mute` write; no manual LED calls needed |
| INTG-01 | Existing toggle behavior preserved for short presses (no regression) | Shift guard in `set_solo_button`/`set_mute_button` overrides; `_shift_pressed` attribute available from parent |
</phase_requirements>

---

## Summary

Phase 2 implements the core toggle/momentary state machine inside the already-scaffolded `ToggleMomentaryChannelStripComponent`. The state machine is symmetrical: press-down immediately inverts current track state and starts a 4-tick countdown; release before countdown reaches 0 is a short press (state stays inverted = toggle); release after countdown reaches 0 is a long press (state reverts = momentary). All state variables for solo and mute are already initialized in Phase 1 scaffolding.

The critical design insight (D-08) is a shared helper method `_handle_toggle_momentary` that accepts the five state attributes as parameters. Both `_solo_value` and `_mute_value` call this helper. The `_on_timer` similarly handles both channels via the same helper or two symmetric calls. This avoids duplicated logic and ensures bug fixes propagate to both buttons.

LED updates require no additional code. `ChannelStripComponent._on_solo_changed` and `_on_mute_changed` are registered Live listeners that fire automatically whenever `track.solo` or `track.mute` is written, calling `turn_on()`/`turn_off()` on the button LED. The shift guard is implemented by overriding `set_solo_button` and `set_mute_button` to reset timer state before calling the parent setter.

**Primary recommendation:** Override `_solo_value` and `_mute_value` to call a shared helper — do NOT call super for these methods, as the base class does an immediate toggle that conflicts. Override `set_solo_button`/`set_mute_button` to add the D-07 reset guard before calling super. Extend `_on_timer` by calling parent then adding countdown logic.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `_Framework.ChannelStripComponent` | Live 12.1 (decompiled 2025-03-17) | Base class owning `_solo_value`, `_mute_value`, `_on_solo_changed`, `_on_mute_changed`, `_shift_pressed` | Only mechanism for intercepting button values from the MIDI routing layer |
| `SpecialChanStripComponent` | Project-local | Direct parent; provides timer registration, `_on_timer`, fold-delay pattern | Already has tick-countdown pattern; Phase 2 extends it |

### No New Dependencies

This phase adds no new imports. All required APIs (`getattr`/`setattr` if used for the helper, built-in Python) are already available in the existing file.

---

## Architecture Patterns

### File Under Modification
```
ToggleMomentaryChannelStripComponent.py   # only file modified in Phase 2
```

### Pattern 1: Press-Down State Inversion (D-01, D-05)

**What:** State change (solo/mute) fires at button press-down (`value != 0`), not at release or threshold.
**When to use:** Always. Every code path writes `track.solo` or `track.mute` inside the `value != 0` branch.

```python
# Source: ChannelStripComponent.py lines 296-305 (verified in-repo)
# _solo_value original — we REPLACE entirely, not call super:
def _solo_value(self, value):
    if self.is_enabled() and self._track is not None:
        if value != 0:  # press-down
            self._solo_state_before_press = self._track.solo
            self._track.solo = not self._track.solo   # immediate inversion
            self._solo_ticks_delay = LONG_PRESS_DELAY
        else:           # release
            if self._solo_momentary_active:
                self._track.solo = self._solo_state_before_press  # revert
                self._solo_momentary_active = False
            # elif _ticks_delay > 0: already toggled — keep it (short press path)
            self._solo_ticks_delay = -1  # always reset
```

### Pattern 2: Tick Countdown in `_on_timer` (D-04, D-09)

**What:** Timer decrements `_solo_ticks_delay` each tick. At tick 0, the press has crossed the threshold; set `_momentary_active = True`. Already-inverted state was applied at press-down, so no state change is needed at threshold — only the flag changes.
**When to use:** Inside `_on_timer`, after the parent call.

```python
# Source: SpecialChanStripComponent.py lines 46-52 (fold-delay pattern — exact model)
def _on_timer(self):
    SpecialChanStripComponent._on_timer(self)  # preserve fold-delay
    if self.is_enabled() and self._track is not None:
        if self._solo_ticks_delay > -1:
            if self._solo_ticks_delay == 0:
                self._solo_momentary_active = True
                # State was already inverted at press-down — no re-write needed
            self._solo_ticks_delay -= 1
        # Mute: same block
        if self._mute_ticks_delay > -1:
            if self._mute_ticks_delay == 0:
                self._mute_momentary_active = True
            self._mute_ticks_delay -= 1
```

**Note on tick sequencing:** `_on_timer` runs every 100ms. `LONG_PRESS_DELAY = 4`. Starting at 4, the sequence is: tick→3, tick→2, tick→1, tick→0 (fires momentary flag), tick→-1 (disarmed). Four decrements = 400ms before the flag is set. This matches the requirement exactly.

### Pattern 3: Shared Helper for DRY Implementation (D-08)

**What:** A single private method handles both solo and mute press logic by accepting attribute names as parameters.
**When to use:** `_solo_value` and `_mute_value` both delegate to this helper.

Two implementation options — both valid, planner chooses based on Claude's Discretion:

**Option A: `getattr`/`setattr` approach (more DRY)**
```python
def _handle_toggle_momentary(self, value, track_attr, ticks_attr, state_attr, momentary_attr):
    if value != 0:  # press-down
        current = getattr(self._track, track_attr)
        setattr(self, state_attr, current)
        setattr(self._track, track_attr, not current)
        setattr(self, ticks_attr, LONG_PRESS_DELAY)
    else:  # release
        if getattr(self, momentary_attr):
            setattr(self._track, track_attr, getattr(self, state_attr))
            setattr(self, momentary_attr, False)
        setattr(self, ticks_attr, -1)

def _solo_value(self, value):
    if self.is_enabled() and self._track is not None:
        self._handle_toggle_momentary(
            value, 'solo',
            '_solo_ticks_delay', '_solo_state_before_press', '_solo_momentary_active'
        )

def _mute_value(self, value):
    if self.is_enabled() and self._track is not None:
        self._handle_toggle_momentary(
            value, 'mute',
            '_mute_ticks_delay', '_mute_state_before_press', '_mute_momentary_active'
        )
```

**Option B: Explicit attribute access (more readable, less DRY)**
```python
# Two separate near-identical methods, each reading/writing attributes by name.
# Acceptable given there are only two buttons; decision per Claude's Discretion.
```

### Pattern 4: Shift Guard in Button Setters (D-07)

**What:** Override `set_solo_button` and `set_mute_button` to clean up in-flight press state before calling the parent setter. This fires when shift is pressed (ShiftableSelectorComponent calls `set_solo_button(None)` for each strip).
**When to use:** Any call to `set_solo_button(None)` or `set_mute_button(None)`.

```python
# Source: ChannelStripComponent.py lines 157-163 (set_solo_button) — we wrap it
def set_solo_button(self, button):
    # Reset timing state to prevent stuck momentary condition (D-07)
    if self._solo_momentary_active:
        if self._track is not None:
            self._track.solo = self._solo_state_before_press
        self._solo_momentary_active = False
    self._solo_ticks_delay = -1
    ChannelStripComponent.set_solo_button(self, button)

def set_mute_button(self, button):
    if self._mute_momentary_active:
        if self._track is not None:
            self._track.mute = self._mute_state_before_press
        self._mute_momentary_active = False
    self._mute_ticks_delay = -1
    ChannelStripComponent.set_mute_button(self, button)
```

**Important:** Call `ChannelStripComponent.set_solo_button` (grandparent), NOT `SpecialChanStripComponent.set_solo_button` — the intermediate class does not override these setters, so skipping to grandparent is safe and avoids one MRO lookup. Alternatively `SpecialChanStripComponent.set_solo_button(self, button)` works too since it will chain up. Either is correct.

### Anti-Patterns to Avoid

- **Calling `super._solo_value`:** The base class toggles `track.solo` immediately on press-down — calling it causes a double-inversion and breaks the state machine. Replace entirely.
- **Writing LED state manually:** Do not call `self._solo_button.turn_on()` / `turn_off()` inside value handlers. The `_on_solo_changed` listener handles this automatically when `track.solo` is written.
- **Capturing pre-press state at release time:** `_solo_state_before_press` must be set in the `value != 0` branch, not `else`. If set at release time, external solo changes during the hold will corrupt the revert target.
- **Not resetting `_ticks_delay` unconditionally on release:** Reset must happen regardless of which branch (short or long). Conditional reset causes state drift on consecutive presses.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Millisecond timer | `threading.Timer`, `time.sleep` | `_register_timer_callback` tick counter (already in SpecialChanStripComponent) | threading is not thread-safe against Live API; timer callback runs on Live's main thread |
| Press duration classification | Custom MIDI timestamp logic | Tick countdown from `LONG_PRESS_DELAY` | Framework timer is the only reliable timing mechanism in the Live environment |
| LED updates | `self._solo_button.turn_on()` / `turn_off()` in value handlers | `_on_solo_changed` / `_on_mute_changed` (inherited, fires automatically) | Already wired to Live's track property listeners; manual calls cause double-fire and race conditions |

**Key insight:** The Framework's `_register_timer_callback` at 100ms per tick is the only safe, cancellable timing mechanism. It runs on the main thread, respects component enabled state through the `is_enabled()` guard, and is already registered by the parent class.

---

## Common Pitfalls

### Pitfall 1: Double-Inversion from Calling Super in `_solo_value`
**What goes wrong:** `ChannelStripComponent._solo_value` toggles `track.solo` at `value != 0`. If called before the override's own logic, the track state flips twice and remains unchanged (net no-op), with LEDs flickering.
**Why it happens:** Natural instinct to call `super()` for extensibility.
**How to avoid:** Do NOT call `ChannelStripComponent._solo_value` or `SpecialChanStripComponent._solo_value`. Replicate the `is_enabled()` and `self._track is not None` guards from scratch.
**Warning signs:** Pressing solo has no visible effect; LED flickers; `track.solo` unchanged after press.

### Pitfall 2: Shift-Mode Regression (`_shift_pressed` not checked)
**What goes wrong:** `_solo_value` fires when shift is held (before `set_solo_button(None)` fires). The toggle/momentary logic runs on a shift-modified press, breaking sequencer loop-length assignment.
**Why it happens:** Not reading `_shift_pressed` state. `ChannelStripComponent` sets `self._shift_pressed = True` via `_shift_value` when the shift button is held (wired at `strip.set_shift_button(self._shift_button)`, APC_64_40_9.py line 159). The attribute IS available in the subclass.
**How to avoid:** Add `if self._shift_pressed: return` as first guard inside the `is_enabled()` block in `_solo_value` and `_mute_value`.
**Warning signs:** Step sequencer loop-length page control stops working; shift + solo triggers unexpected solo behavior.

### Pitfall 3: Tick Counter Drift on Consecutive Presses
**What goes wrong:** `_solo_ticks_delay` is not reset to `-1` unconditionally on release. Next press starts countdown from a non-`LONG_PRESS_DELAY` value, causing the second press to be misclassified.
**How to avoid:** End of every `value == 0` branch: `self._solo_ticks_delay = -1` unconditionally — regardless of whether the short or long press path was taken.
**Warning signs:** First press correct; second consecutive press behaves as long press even when tapped quickly.

### Pitfall 4: `_on_timer` Not Calling Parent
**What goes wrong:** Forgetting `SpecialChanStripComponent._on_timer(self)` at the start of the override. The fold-delay for foldable tracks stops working.
**How to avoid:** First line of the overridden `_on_timer` must be the parent call.
**Warning signs:** Track fold-toggle (hold select on a group track) stops working after Phase 2 changes.

### Pitfall 5: `set_solo_button` Guard Not Reverting Track State
**What goes wrong:** The reset guard in `set_solo_button(None)` resets the tick counter and `_momentary_active` flag but does not revert `track.solo` to `_state_before_press`. Track is left in the inverted state when shift is pressed mid-hold.
**How to avoid:** Check `if self._solo_momentary_active` and write `self._track.solo = self._solo_state_before_press` before clearing the flag. Also guard `self._track is not None`.
**Warning signs:** After pressing shift during a long-hold, the track remains soloed (or un-soloed) permanently.

---

## Code Examples

### Exact `_solo_value` Signature (from ChannelStripComponent source)

```python
# Source: /Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/ChannelStripComponent.py lines 296-305
def _solo_value(self, value):
    if self.is_enabled() and self._track != None and (self._track != self.song().master_track):
        self._solo_pressed = value != 0 and self._solo_button.is_momentary()
        if value != 0 or not self._solo_button.is_momentary():
            # ... exclusive solo logic across all tracks ...
```

**Key facts confirmed from source:**
- Called with MIDI value: `value > 0` = press-down, `value == 0` = release (for momentary buttons)
- Parent updates `self._solo_pressed` (class-level static counter for exclusive solo logic)
- Parent iterates ALL tracks for exclusive solo logic — this is replaced entirely by the override
- `self._track != self.song().master_track` guard should be preserved in the override

### Exact `_mute_value` Signature

```python
# Source: ChannelStripComponent.py lines 276-283
def _mute_value(self, value):
    if self.is_enabled() and self._track != None and (self._track != self.song().master_track) and self._mute_button.is_momentary() and (value != 0):
        self._track.mute = not self._track.mute
```

**Key facts confirmed from source:**
- Parent only fires on `value != 0` (ignores release for mute — no release logic in base)
- Parent checks `self._mute_button.is_momentary()` — override should preserve `is_momentary()` check
- The override must handle both press AND release (adding the release path)

### Existing State Variables (Phase 1 scaffolding — already in file)

```python
# Source: ToggleMomentaryChannelStripComponent.py lines 17-23
self._solo_ticks_delay = -1         # countdown: -1 = inactive, >0 = counting, 0 = threshold hit
self._solo_state_before_press = False  # snapshot of track.solo at press-down
self._solo_momentary_active = False  # True once countdown reaches 0
self._mute_ticks_delay = -1
self._mute_state_before_press = False
self._mute_momentary_active = False
```

### `_on_solo_changed` LED Update (no code change needed)

```python
# Source: ChannelStripComponent.py lines 351-364
def _on_solo_changed(self):
    if not self.is_enabled() or self._solo_button != None:
        if self._track != None or self.empty_color == None:
            if self._track in chain(self.song().tracks, self.song().return_tracks) and self._track.solo:
                self._solo_button.turn_on()
            else:
                self._solo_button.turn_off()
```

This fires whenever `track.solo` is written. Writing `self._track.solo = not self._track.solo` in the override triggers this listener automatically. No LED code in Phase 2.

### ShiftableSelectorComponent Solo Button Disconnect (context only)

```python
# Source: ShiftableSelectorComponent.py lines 108-110
# Called when shift is pressed (mode_index == 1):
for index in range(len(self._solo_buttons)):
    self._mixer.channel_strip(index).set_solo_button(None)
```

This is the trigger for the D-07 reset guard. Each of the 8 strips gets `set_solo_button(None)`. The override handles this.

### Timer Registration (inherited — no change in Phase 2)

```python
# Source: SpecialChanStripComponent.py lines 16, 19
# __init__:
self._register_timer_callback(self._on_timer)
# disconnect:
self._unregister_timer_callback(self._on_timer)
```

Python virtual dispatch routes `self._on_timer` calls to the overridden method in the subclass. Phase 1 decision D-04 confirmed no additional registration is needed.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `_mute_value` ignores release (base class fires only on press) | Override must handle release explicitly by adding `value == 0` branch | Phase 2 | Must add release logic that base class omits |
| `_solo_value` uses exclusive-solo iteration over all tracks | Override replaces with direct `self._track.solo` write | Phase 2 | Simpler; exclusive-solo behavior (shift-to-exclusive) is bypassed but acceptable for this feature |

**Note on exclusive solo:** The base `_solo_value` iterates all tracks to implement exclusive solo (soloing one track unsolos others when `song().exclusive_solo` is enabled and shift is not held). The override replaces this with a direct `self._track.solo` write. This means the Phase 2 implementation does NOT propagate exclusive-solo behavior. Whether this is acceptable depends on the user's expected behavior — if exclusive solo from hardware buttons is important, the override needs to either call the parent or re-implement the exclusive-solo iteration. Based on CONTEXT.md and REQUIREMENTS.md, this is not mentioned as a requirement; the project focuses on toggle/momentary timing, not exclusive solo semantics.

**Recommendation for planner:** Document this as a known tradeoff in the plan. The simplest safe approach is to write only `self._track.solo` directly (no exclusive solo propagation). If exclusive solo is needed, it can be added as a follow-up.

---

## Open Questions

1. **Exclusive Solo Propagation**
   - What we know: Base `_solo_value` iterates all tracks for exclusive solo. The override replaces this.
   - What's unclear: Whether the user expects hardware solo to still respect `song().exclusive_solo` mode.
   - Recommendation: Implement with direct write first. If exclusive solo regression is noticed in testing, add the iteration back inside the `value != 0` branch.

2. **`_solo_pressed` Static Counter Interaction** — RESOLVED
   - What we know: `ChannelStripComponent._solo_pressed` is set in the base `_solo_value` and used by the static `number_of_solos_pressed()` counter.
   - Resolved: Grepped all .py files in the project — `number_of_solos_pressed` is not called anywhere in this script. Skipping the counter update in the override is safe.
   - No action needed.

---

## Sources

### Primary (HIGH confidence)
- `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/_Framework/ChannelStripComponent.py` — `_solo_value`, `_mute_value`, `_on_solo_changed`, `_on_mute_changed`, `set_solo_button`, `set_mute_button`, `_shift_pressed` — direct source read
- `/Users/stoersignal/Dev/APC_64_40_12/SpecialChanStripComponent.py` — tick-countdown pattern, `_on_timer`, `_register_timer_callback` pair — direct source read
- `/Users/stoersignal/Dev/APC_64_40_12/ToggleMomentaryChannelStripComponent.py` — Phase 1 scaffolding state variables, `_on_timer` stub — direct source read
- `/Users/stoersignal/Dev/APC_64_40_12/ShiftableSelectorComponent.py` — `set_solo_button(None)` / `set_mute_button(None)` trigger in shift mode — direct source read
- `/Users/stoersignal/Dev/APC_64_40_12/APC_64_40_9.py` lines 151-192 — solo/mute button wiring, `set_shift_button` called on each strip — direct source read

### Secondary (MEDIUM confidence)
- `.planning/research/ARCHITECTURE.md` — Integration analysis, data flow, anti-patterns — project research from 2026-03-31
- `.planning/research/PITFALLS.md` — 12 verified pitfalls with source citations — project research from 2026-03-31

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all files read directly from repo; no external dependencies
- Architecture patterns: HIGH — code examples derived from verified source files
- Pitfalls: HIGH — confirmed against _Framework source at `/Users/stoersignal/Dev/AbletonLive12.1_MIDIRemoteScripts/`
- Open questions: LOW — gaps that require a search or testing to close

**Research date:** 2026-03-31
**Valid until:** Stable — this is a static codebase modification; findings do not expire unless Ableton upgrades the _Framework API
