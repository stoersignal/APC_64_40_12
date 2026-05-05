# Quick Task 260505-sb9: Status Bar Messages — Context

**Gathered:** 2026-05-05
**Status:** Ready for planning

<domain>
## Task Boundary

Make broad use of Live's bottom status bar for transient feedback. When
the user changes mode, presses certain modifier combos, recalls a
snapshot, or moves any APC40-bound parameter, a one-line message
appears at the bottom of Live's window summarising what just changed.

Display API: `Application.show_message(text)` — Live's standard
transient-notification call. Live auto-fades the message after a few
seconds. No persistent (set_status_text) UI in this iteration.

</domain>

<decisions>
## Implementation Decisions (locked)

### D-01 — Display API: transient `Application.show_message(text)`

- Use `self.application().show_message(text)` from any component that
  inherits from `ControlSurfaceComponent`.
- Do NOT use `Application.View.set_status_text()` (persistent) — would
  conflict with Live's own status messages.
- Each call replaces the previously-displayed text.

### D-02 — Events that trigger a status message

User-locked event list:

1. **Drum Rack Mode** enter / exit
   - Auto-engage on selecting a drum-rack track
   - Manual exit via Shift + Detail View
   - Wired in `DrumRackModeComponent`
2. **AutoFilter Mode** (Shift + Send A) enter / exit
   - Wired in `EncoderAutoFilterComponent`
3. **EQ Smart Control** (Shift + Send B) enter / exit
   - Wired in `EncoderEQComponent`
4. **Matrix-mode swaps** (Variations 6 / 7, Sequencer 8, Note, Clip Stop,
   Activator, Solo, Pan, Send-A, Send-B, Send-C — whatever modes the
   matrix supports today)
   - Wired in `MatrixModesComponent`
5. **Snapshot save / recall** (rack macros via Shift+Tap-Tempo / Nudge)
   - Wired in `MatrixModesComponent` or wherever the Variations
     save/recall is implemented
6. **Encoder sub-mode flips** (Pan / Send A / B / C buttons)
   - Wired in `EncModeSelectorComponent`
7. **Lock to device** (Shift + Nudge-Back) toggle
   - Wired wherever lock-to-device lives — likely `APC_64_40_9` or a
     dedicated component
8. **Parameter value changes — every APC40-bound parameter**
   - Whenever the user moves a fader / encoder, show
     `"<param name>: <formatted value>"` (e.g. `"Cutoff: 1.20 kHz"`,
     `"Drive: -2.4 dB"`, `"Volume: -6.3 dB"`)
   - Use `param.str_for_value(param.value)` if available — that's
     Live's own formatted string with units. Fall back to plain
     `repr(param.value)` if not.

### D-03 — Centralized messenger helper

- Add a single helper module (`StatusBarMessenger.py`) with a small API:
  - `show_mode(mode_name, entered: bool)` → e.g. "Drum Rack Mode
    entered" / "Drum Rack Mode exited"
  - `show_param(param_name, formatted_value)` → e.g. "Cutoff: 1.20 kHz"
  - `show_event(text)` → arbitrary one-shot text
- Constructor takes a `parent` (the ControlSurface) so it can call
  `parent.application().show_message(...)`.
- All other components receive a messenger instance via dependency
  injection (constructor argument). NO global / singleton.

### D-04 — Throttling for parameter-value messages

- Encoder turns generate dozens of value events per second.
- Implement debounce in `StatusBarMessenger.show_param`:
  - Track `_last_param_id` and `_last_emit_time`.
  - If same param within `THROTTLE_MS` (default 50ms), suppress.
  - Different param OR time-elapsed > 50ms → emit immediately.
- Mode-event messages (`show_mode`, `show_event`) bypass throttling
  (they fire infrequently).

### D-05 — Parameter-value listener pattern

- For every parameter the script binds to a fader / encoder, add a
  parallel `param.add_value_listener(callback)` that calls
  `messenger.show_param(name, str_for_value(value))`.
- Listener bookkeeping per existing project conventions (list of
  `(param, callback)` pairs, removed on disconnect / re-bind).
- Apply to:
  - 8 track faders (per-track volume) — owned by
    `SpecialMixerComponent` / `SpecialChanStripComponent`. May need to
    extend those, OR install listeners on each `mixer_strip.set_volume_control`
    binding from `APC_64_40_9._setup_mixer_control`.
  - 8 Track Control encoders (Pan / Send A / B / C) — owned by
    `EncModeSelectorComponent` and friends.
  - Drum Rack Mode chain bindings (chain.mixer_device.{volume, panning,
    sends}, chain.mute, chain.solo) — extend the existing per-slot
    listener bookkeeping in `DrumRackModeComponent`.
  - AutoFilter Mode encoders (Drive, Env Attack, Env Release, LFO Rate,
    Frequency, Resonance, Env Amount, LFO Amount, etc.) —
    `EncoderAutoFilterComponent`.
  - EQ Smart Control encoders — `EncoderEQComponent`.

### D-06 — Message format conventions

| Event class | Format |
|---|---|
| Mode enter | `"<Mode Name>"` (e.g. `"Drum Rack Mode"`) |
| Mode exit | `"<Mode Name> exited"` (e.g. `"AutoFilter Mode exited"`) |
| Encoder sub-mode | `"Encoder mode: <Pan/Send A/B/C>"` |
| Matrix-mode swap | `"Matrix: <Mode Name>"` (e.g. `"Matrix: Variations"`) |
| Snapshot save | `"Snapshot <N> stored"` |
| Snapshot recall | `"Snapshot <N> recalled"` |
| Lock to device | `"Lock to device: ON/OFF"` |
| Parameter change | `"<Param Name>: <formatted value>"` (e.g. `"Cutoff: 1.20 kHz"`) |

</decisions>

<specifics>
## Specific Implementation Notes

### Live API — `Application.show_message`

```python
self.application().show_message('Drum Rack Mode')
```

- Available on every `ControlSurfaceComponent` via `self.application()`.
- No return value. Always succeeds (Live handles fade timing).
- Live's UI shows the text in the bottom-left status bar for ~3 seconds
  then fades it.

### Parameter formatting — `param.str_for_value`

```python
formatted = param.str_for_value(param.value)
# e.g. "1.20 kHz" for Cutoff at 1200 Hz
# e.g. "-6.3 dB" for Volume at -6.3 dB
```

- Available on Live's `DeviceParameter` and `MixerDevice` parameter
  objects.
- Returns a string with units, matching Live's UI exactly.
- Fall back to `repr(param.value)` if `str_for_value` raises.

### Throttling implementation sketch

```python
import time

class StatusBarMessenger:
    THROTTLE_MS = 50

    def __init__(self, parent):
        self._parent = parent
        self._last_param_id = None
        self._last_emit_ms = 0.0

    def _now_ms(self):
        return time.time() * 1000.0

    def _emit(self, text):
        try:
            self._parent.application().show_message(text)
        except Exception:
            pass

    def show_mode(self, mode_name, entered):
        text = mode_name if entered else (mode_name + ' exited')
        self._emit(text)

    def show_event(self, text):
        self._emit(text)

    def show_param(self, param_name, formatted_value, param_id=None):
        now = self._now_ms()
        # Same param within throttle window → drop.
        if param_id is not None and param_id == self._last_param_id:
            if now - self._last_emit_ms < self.THROTTLE_MS:
                return
        self._last_param_id = param_id
        self._last_emit_ms = now
        self._emit(param_name + ': ' + formatted_value)
```

### Listener bookkeeping pattern (mirror existing project conventions)

For every parameter we bind in a component:

```python
# Existing binding:
control.connect_to(param)

# New status-message listener:
def _mk_value_cb(p=param, name=param.name):
    def cb():
        try:
            v = p.str_for_value(p.value)
        except Exception:
            v = repr(p.value)
        self._messenger.show_param(name, v, param_id=id(p))
    return cb

cb = _mk_value_cb()
try:
    param.add_value_listener(cb)
    self._param_value_listeners.append((param, cb))
except Exception:
    pass
```

Tear-down on disconnect / re-bind:

```python
for param, cb in self._param_value_listeners:
    try:
        param.remove_value_listener(cb)
    except Exception:
        pass
self._param_value_listeners = []
```

### Components that need wiring

| Component | What to add |
|---|---|
| `StatusBarMessenger.py` | NEW — the centralized helper |
| `APC_64_40_9.py` | Instantiate the messenger; pass to every component that needs it |
| `DrumRackModeComponent` | Mode enter/exit message; param-value listeners on chain volume/pan/sends/mute/solo |
| `EncoderAutoFilterComponent` | Mode enter/exit message; param-value listeners on the 8 encoders + 4 buttons |
| `EncoderEQComponent` | Mode enter/exit message; param-value listeners on the EQ encoders |
| `EncModeSelectorComponent` | Encoder sub-mode flip message; param-value listeners on Pan / Send encoders |
| `MatrixModesComponent` | Matrix-mode swap messages; snapshot save/recall messages |
| `SpecialMixerComponent` / `SpecialChanStripComponent` | Param-value listeners on track volume/pan/sends/mute/solo (when not Drum-Rack-overridden) |
| Lock-to-device wiring | Status message on toggle (find current owner via grep) |

### Parameter-id throttling rationale

Encoder turns generate ~100 events per second when twisting fast. Without
throttling, `show_message` would be called 100x/sec — which Live handles
fine but is wasteful. The 50ms debounce caps it at ~20 messages per
second per parameter, which keeps the message readable (otherwise the
text changes faster than the eye can read).

When the user switches to a DIFFERENT parameter (e.g. lets go of cutoff,
turns resonance), the throttle DOES NOT block — the new param's message
shows immediately. This is the right UX: feedback is immediate when
changing focus, smoothed when staying on one param.

### Shared anti-patterns to apply

- Wrap every `add_value_listener` / `show_message` / `str_for_value` call
  in try/except — the project's fail-quiet idiom.
- Strip listeners on disconnect / re-bind to avoid double-fires.
- Don't use `parameter.is_enabled` to gate messages — that lies on
  UI-greyed controls (project anti-pattern note).
- For mode messages, fire on mode TRANSITIONS only (pressed=down events),
  not on every value change of the mode-selector button.

</specifics>

<canonical_refs>
## Canonical References

- Live API: `Application.show_message(text)`,
  `Application.View.set_status_text(text)`, `param.str_for_value(value)`,
  `param.add_value_listener(callback)`.
- `DrumRackModeComponent.py` — recently shipped, has clean mode
  enter/exit hooks (`_engage` / `_disengage`) — mirror its pattern.
- `EncoderAutoFilterComponent.py` — has clean mode enter/exit too.
- `MatrixModesComponent.py` — already gates many actions on
  `_mode_index` changes; the message-on-transition pattern fits naturally.
- Project anti-pattern list (resolved debug sessions):
  - `parameter.is_enabled` lies
  - `connect_to(None)` is silent
  - `param.add_value_listener` is reliable across Live versions
  - `str_for_value` typically returns Live-style formatted strings;
    fall back to `repr(value)` if it raises
- `APC40_User_Manual.md` — Phase 6 will need to document the new
  status-message UX. Add a TODO marker in this task too.

</canonical_refs>
