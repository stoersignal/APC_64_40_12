# Feature Landscape: Toggle/Momentary Dual-Mode Button Behavior

**Domain:** MIDI control surface script — dual-behavior (toggle/momentary) button press detection
**Researched:** 2026-03-31
**Confidence:** MEDIUM — Core behavior patterns verified against multiple sources; specific timing conventions informed by professional console industry norms and community implementations

---

## Table Stakes

Features users expect. Missing = the toggle/momentary dual mode feels broken or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Short press toggles state | This is the existing behavior. Preserving it is the contract with existing users. Any regression breaks trust immediately. | Low | Must be invisible change — existing behavior must work identically for taps under threshold |
| Long press activates momentary | The fundamental new behavior. Hold = active only while held, release = revert. This is the industry-standard definition of "momentary" across pro consoles (Avid VENUE, Yamaha, Pro Tools). | Medium | Threshold must feel natural — not so long it's annoying, not so short it triggers accidentally |
| State reverts on release | When held state ends, return to what was true before the press. Not to a fixed "off" state — to the previous state. A soloed track that was long-pressed should return to soloed. An unsoloed track should return to unsoloed. | Medium | Requires capturing pre-press state on button-down for use at button-release |
| Long press on already-active state inverts | If a track is already muted and you long-press mute, momentarily unmute it while held, then re-mute on release. Documented in PROJECT.md as a validated requirement. Consistent with the "inversion" pattern found in DJ/performance tools (verified: DJ TechTools, 2012). | Medium | Same mechanism as normal momentary — just the starting state differs |
| LEDs reflect real state in real time | LED must show the live track state at all times — including during a hold. If you're holding momentary solo on a track, the LED should light. When you release and it reverts, the LED should go dark. No lag, no stuck states. | Low | The existing `_Framework` update mechanism already fires on state change; the LED update path is inherited |
| No introduced latency on short press | Toggle response must be immediate on release (or on press, matching current behavior). A timing-based approach that waits to classify a press must not delay the short-press response path. | Medium | The classification decision (was this a short or long press?) happens at release-time for short presses, so no latency is introduced for short presses if implemented correctly |
| Shift-modified behaviors still work | Shift + Solo and Shift + Mute have existing behaviors. The new long-press logic must not conflict with shift interactions. | Low-Medium | Shift is a separate button; the new feature only needs to respect the existing `_shift_pressed` flag |

---

## Differentiators

Features that improve the experience beyond baseline. Not expected, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Threshold tuned to 400ms specifically | 400ms is the project's chosen value. Research confirms this sits in the "natural feel" range — long enough to feel deliberate, short enough to not be annoying. Pro consoles use 1 second (Avid VENUE), but that is far too slow for performance use. Community consensus clusters around 300-500ms for performance controllers. | Low | This is a configuration constant, not a runtime feature. Nail the value, don't make it user-configurable (out of scope). |
| State captured at press-down (not release) | Capturing the pre-press state at press-down ensures that if something external changes the track state while you're holding the button, release still reverts to what you intended, not an undefined state. | Low | An implementation detail that makes behavior predictable under edge cases |
| Consistent behavior across Solo and Mute | Both button types behave identically. A performer learning the solo behavior can immediately apply it to mute. Cognitive load stays low. | Low | The same component logic or pattern should serve both; avoid two parallel implementations that can diverge |
| LED updates without flash or flicker on classify | At the 400ms threshold moment, classification happens internally. No visible state change should occur at the threshold itself — the LED state at that moment is already correct (button has been held, state is already active). | Low | The LED reflects Live state directly; as long as the momentary activation fired at press-down (not at threshold), there is no visual artifact |

---

## Anti-Features

Features to explicitly NOT build. These would add complexity, maintenance burden, or UX confusion without proportionate value.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Configurable threshold | Adds a settings system (file, SysEx, or in-script constant) where none exists. The project has already decided on 400ms. Configurability adds testing surface for minimal user benefit. | Hard-code 400ms as a named constant (e.g., `LONG_PRESS_THRESHOLD`). Document the value. Move on. |
| Double-tap detection | Introduces mandatory latency on every short press — the script must wait to confirm no second tap is coming before firing the toggle. Destroys the immediate feel of the toggle mode. Research confirms: long-press avoids this latency problem entirely; double-tap does not. | Use long-press (already chosen). Do not add double-tap as an alternative mode. |
| Visual "loading" indicator during hold | Some controllers show a progress LED during a hold to signal "you're approaching long-press territory." Adds MIDI output complexity, may look odd on the APC40 hardware, and is not consistent with how any of the existing buttons behave. | Trust the user. The 400ms threshold is short enough that no affordance is needed. |
| Extending to Track Activator (arm) buttons | PROJECT.md explicitly scopes this out. Arm buttons have different state semantics and may interact with recording state in ways that require separate validation. | Leave it out. Note in code that the pattern could be applied later if needed. |
| Extending to clip launch, transport, or other buttons | Every additional button type multiplies testing and interaction complexity. None are requested. | Keep feature to Solo and Mute only. |
| Per-track configuration | Allowing some tracks to be toggle-only and others to be dual-mode. No use case given, adds state management complexity. | All 8 Solo buttons behave identically. All 8 Mute buttons behave identically. |
| "Hold to unsolo all" shortcut | Some consoles implement hold-on-solo-button as "clear all solos." This is a separate feature from momentary behavior and would conflict with it. | Do not implement. If desired in future, it requires its own scoped milestone. |

---

## Feature Dependencies

```
Capture pre-press state at button-down
    --> Momentary activation on button-down (state flips immediately on press)
        --> Revert to pre-press state on release
            --> LED reflects Live state in real time (inherited, no extra work)

Press duration timer starts at button-down
    --> If release < 400ms: classify as short press (toggle fire at release)
    --> If still held at 400ms: already in momentary mode (activation already fired)

Shift-pressed flag check
    --> Must be respected before entering toggle/momentary classification logic
    --> Shift + button = existing behavior, no change
```

**Critical dependency:** Momentary activation must fire at press-down, not at the 400ms threshold. This means the implementation cannot wait to classify before doing anything — it must start acting immediately. A common naive implementation fires the action at threshold (causing 400ms latency on all long presses). The correct pattern:

1. Button-down: record pre-press state, immediately apply the new state (same as a normal press)
2. Start a timer
3. If released before 400ms: treat as toggle (state stays changed — it is already the toggled value)
4. If still held at 400ms: transition to momentary mode (note the hold started)
5. Button-up after threshold: revert to pre-press state

This means no user-visible latency on either path.

---

## MVP Definition

For this milestone (toggle/momentary dual-mode), MVP is the full feature set. There is no "partial" version that delivers value — either the dual mode works correctly and feels right, or it does not.

**Must ship:**
1. Short press toggle (preserved, unchanged)
2. Long press momentary with immediate activation
3. Revert-to-prior-state on release
4. Long press inverts on already-active state
5. Real-time LED accuracy
6. Zero latency on short press classification
7. Shift compatibility preserved

**Defer (future milestone, not this one):**
- Configurable threshold
- Track Activator (arm) buttons
- Any additional button types

---

## Sources

- Ableton official: Toggle vs Momentary MIDI functions — https://help.ableton.com/hc/en-us/articles/209774945-Toggle-and-Momentary-MIDI-functions
- Avid VENUE Manual (momentary solo = hold >1 second, latch = press/release) — https://www.manualslib.com/manual/678243/Avid-Technology-Venue.html?page=130 (MEDIUM confidence — page content partially inaccessible)
- Steinberg Nuendo forums: Solo modes (Latch, X-OR, Momentary) behavioral definitions — https://forums.steinberg.net/t/solo-options-latch-x-or-momentary/126648
- DJ TechTools: Momentary FX in Ableton Live — inversion pattern, performance use cases — https://djtechtools.com/2012/08/19/momentary-fx-in-ableton-live-advanced-midi-mappings/
- BeepStreet forums: Long press vs double-tap latency tradeoff — https://forum.beepstreet.com/discussion/1574/double-tap-and-long-press-midi-map-learn-actions
- Mixxx community: Long/short/double press code snippet patterns — https://mixxx.org/forums/viewtopic.php?f=7&t=7681
- Ableton Forum: Momentary buttons and MIDI controller behavior — https://forum.ableton.com/viewtopic.php?t=95571
