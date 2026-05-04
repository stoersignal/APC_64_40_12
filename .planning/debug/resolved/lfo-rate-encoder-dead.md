---
slug: lfo-rate-encoder-dead
status: resolved
trigger: |
  DATA_START
  LFO Rate is not working in the new Auto Filter mode
  DATA_END
created: 2026-05-04T15:15:00Z
updated: 2026-05-04T16:30:00Z
diagnose_only: false
tdd_mode: false
quick_task: 260504-k6p
last_commit: ee7c5ae
final_fix: LFO_T_MODE_PARAM_KEYS dict (6 verified labels) + listener-driven encoder rebind on LFO T Mode change. UAT-passed across all 6 modes.
rounds: 4
lesson: Always run a diagnostic dump of value_items for any enum-driven binding before guessing prefix patterns. Two false starts (LFO Frequency, then 4-mode prefix list) burned because the source-of-truth was Live's actual value_items, not external Ableton refs or guessed mode names.
---

# Debug: LFO Rate encoder dead in AutoFilter Mode (Shift + Send A)

## Symptoms

Issue type: Wrong behavior (encoder dead — no parameter movement)
Timeline: First test of the new AutoFilter mode (commit b1c3dd8, today 2026-05-04)
Reproducibility: Reliably, every time

### Expected vs actual

DATA_START
**Expected:** Top-row encoder 4 should bind to AutoFilter2's `LFO Rate` parameter.
Twisting encoder 4 should move LFO Rate in Live's UI on the selected track's AutoFilter device.

**Actual:** Encoder 4 is dead — turning it produces NO parameter movement in Live's UI.
The other three top-row encoders (1=Drive, 2=Env Attack, 3=Env Release) all work correctly.
Broken on EVERY filter type (not just Vowel/DJ — so the Vowel/DJ encoder-swap branch is NOT
implicated; that branch only touches encoders 5/6).
DATA_END

### Errors / Log

DATA_START
Live's Log.txt is clean — no AttributeError, no exception when entering Mode 2 or twisting
encoder 4. This means `connect_to` did not raise, which means either:
  (a) the parameter lookup returned a real Parameter object that was bound,
      but encoder 4 isn't actually that encoder (wrong index / off-by-one), OR
  (b) the parameter lookup returned None and connect_to(None) silently no-ops, OR
  (c) the encoder is bound but immediately overwritten / released by a later code path.
DATA_END

### Reproduction

DATA_START
1. Reload the APC40 script in Live (Live 11+, AutoFilter2)
2. Select a track containing an AutoFilter device
3. Press Shift + Send A to enter Mode 2 (AutoFilter cockpit)
4. Verify encoders 1, 2, 3 move Drive, Env Attack, Env Release respectively (they do).
5. Twist encoder 4 — nothing moves. LFO Rate stays put.
DATA_END

### Project context

DATA_START
- Quick task: `260504-k6p` (replace MODE 2 Alternate Device with AutoFilter mode)
- Last commit: `b1c3dd8` — corrected AutoFilter2 param names and added Vowel/DJ encoder swap
- Component: `EncoderAutoFilterComponent.py`
- Wired in: `APC_64_40_9.py` (TRACK CONTROL MODE 2 / Shift + Send A)
- Sister component (reference): `EncoderEQComponent.py` for Mode 3
- Decision: AutoFilter detection accepts both `'AutoFilter'` and `'AutoFilter2'` class_names

Top-row encoder mapping per .continue-here.md:
  enc1 = Drive, enc2 = Env Attack, enc3 = Env Release, enc4 = LFO Rate
Bottom-row encoder mapping:
  enc5 = Frequency (or Pitch on Vowel / Control on DJ)
  enc6 = Resonance (or Formant on Vowel / unbound on DJ)
  enc7 = Env Amount, enc8 = LFO Amount

Known anti-patterns from this session (apply to investigation):
  - `parameter.is_enabled` lies (Live keeps it True even on UI-greyed controls)
  - Plain `ButtonElement` has no set_enabled / set_on_off_values
  - `strip.set_send_controls` fights for encoders 1/2/3 unless explicitly nulled
  - AutoFilter2 is the Live 11+ class_name (legacy 'AutoFilter' is Live 9/10)
  - Param names verified earlier this task: `'Env Attack'` not `'Env. Attack'`
DATA_END

## Current Focus

hypothesis: `AUTOFILTER_PARAMS['LFORate']` is `'LFO Rate'`, but Ableton's canonical parameter name is `'LFO Frequency'`. `get_parameter_by_name` returns None, encoder index 3 is left released after `release_parameter()`, no exception is raised, no log line is emitted — encoder is silently dead. Encoders 0/1/2 work because their param names ('Drive', 'Env Attack', 'Env Release') were verified by the earlier dump.
test: Apply fix `'LFO Rate'` → `'LFO Frequency'` and add a one-shot AutoFilter param dump to Log.txt (matches EncoderEQComponent's `_filter_eq3_logged` pattern). UAT in Live: enter Mode 2, twist enc4 — LFO Rate parameter should move.
expecting: Encoder 4 binds to LFO Frequency (which Live displays as "LFO Rate" in the UI on AutoFilter2). Diagnostic dump confirms the canonical name on first activation.
next_action: Edit EncoderAutoFilterComponent.py — fix the dict entry and add the diagnostic dump.

## Evidence

- timestamp: 2026-05-04T15:30:00Z
  observation: Read EncoderAutoFilterComponent.py end-to-end. ENCODER_MAP has `(3, 'LFORate')` — index 3 is wired correctly. AUTOFILTER_PARAMS['LFORate'] = 'LFO Rate'. Bind loop iterates ENCODER_MAP fully (no off-by-one). _bind_freq_reso_encoders only touches indices 4 and 5, not 3 — so it cannot release encoder 3 after the static bind. No code path overwrites encoder 3 after the initial bind.
  conclusion: The bug must be in the param-name lookup. Path (a) and (c) from the Errors/Log section are ruled out — it has to be path (b): `get_parameter_by_name(device, 'LFO Rate')` returns None.

- timestamp: 2026-05-04T15:32:00Z
  observation: Inspected `_Generic.Devices.get_parameter_by_name` — matches against `parameter.original_name`, returns None on miss with no exception. Confirms the silent-dead-encoder failure mode.
  conclusion: Confirms that a param-name miss produces exactly the observed symptom (dead encoder, clean log).

- timestamp: 2026-05-04T15:33:00Z
  observation: Cross-referenced Ableton's own definitions for the canonical AutoFilter LFO-rate parameter name:
    - `_Generic/Devices.py` (Live 12.1 reference): `AFL_BANK1 = ('Frequency', 'Resonance', 'Env. Attack', 'Env. Release', 'Env. Modulation', 'LFO Amount', 'LFO Frequency', 'LFO Phase')` → uses 'LFO Frequency'.
    - `ableton/v3/control_surface/default_bank_definitions.py` (Live 12 v3 modern bank def for AutoFilter): `use('LFO Frequency').if_parameter('LFO Sync').is_available(True)` → uses 'LFO Frequency'.
  conclusion: Two independent Ableton sources name the parameter `'LFO Frequency'`. The user-facing label in Live's GUI is "LFO Rate" (which is what the spec doc and our dict key reflect), but the underlying `original_name` is `'LFO Frequency'`. This is the bug.

- timestamp: 2026-05-04T15:34:00Z
  observation: Note the prior session's "verified param names" list (the now-removed Log.txt dump on first activation) only confirmed Drive / Env Attack / Env Release / Env Amount / S/C On / Soft Clip On — it did NOT verify the LFO Rate name. The string 'LFO Rate' came from the spec document (which uses GUI labels), not from a real param dump. So this is a regression caused by relying on the GUI label as a `original_name` lookup key for one parameter that wasn't in the verification batch.
  conclusion: Fix is high-confidence. To self-verify on next reload, restore the diagnostic param dump (sister-component pattern in EncoderEQComponent._setup_slope_button line 837-848) so any further name mismatches (e.g. 'LFO Amount' might differ on AutoFilter2) surface immediately.

## Eliminated

- hypothesis: Vowel/DJ filter-type encoder swap is interfering with encoder 4
  reasoning: User confirms LFO Rate is broken on EVERY filter type. The swap branch only touches encoders 5/6 (not 4) per the design spec in .continue-here.md. Code-confirmed: `_bind_freq_reso_encoders` only iterates `(4, 5)`.
- hypothesis: Param-name typo causes AttributeError / exception
  reasoning: Live's Log.txt is clean. `connect_to` does not raise on `connect_to(None)`; it silently no-ops. `get_parameter_by_name` also returns None silently. So a wrong param name manifests as a dead encoder, not an exception — exactly matching the symptom.
- hypothesis: ChannelStrip.set_send_controls claiming encoder 4
  reasoning: That conflict applies to encoders 1/2/3 (Send A/B/C), not encoder 4. Also, encoders 1/2/3 are working — meaning sends are correctly nulled. Code-confirmed in EncoderUserModesComponent._set_modes line 116-118.
- hypothesis: Off-by-one in the bind loop
  reasoning: ENCODER_MAP includes `(3, 'LFORate')` and the for-loop iterates the full tuple. No off-by-one possible.
- hypothesis: Encoder index 3 is rebound to None by a later code path
  reasoning: Only `_bind_freq_reso_encoders` releases/reassigns encoders post-bind, and it only touches indices 4 and 5. The teardown path (`_teardown_bindings`) releases all 8 but is only called on disable / re-update — not after the initial bind.

## Resolution

(superseded — see Round 2 below; the first fix was wrong.)

## Round 2 — UAT result + ground truth

- timestamp: 2026-05-04T15:55:00Z
  observation: User reloaded Live with the `'LFO Frequency'` fix applied. UAT result: encoder STILL dead, AND now LED ring is dark too. The diagnostic dump (added by the same commit) ran successfully and dumped the full AutoFilter2 parameter list. The dump definitively rules out both 'LFO Rate' and 'LFO Frequency' as a single canonical rate param.
  conclusion: First-round fix was a regression, not a fix. Need to reinterpret the dump.

- timestamp: 2026-05-04T15:55:00Z
  observation: AutoFilter2 dump excerpt — LFO-related params:
    - 'LFO Amount'
    - 'LFO Wave'
    - 'LFO T Mode'    ← LFO Time-mode selector (Hz / S / 4 / 16)
    - 'LFO Freq'      ← Hz-mode rate
    - 'LFO Time'      ← S-mode (seconds) rate
    - 'LFO Rate'      ← 4-mode (4-bar sync subdivision) rate
    - 'LFO 16th'      ← 16-mode (16th-note sync subdivision) rate
    - 'LFO Phase'
    - 'LFO Offset'
    - 'LFO S Mode'
    - 'LFO Spin'
    - 'LFO Morph'
    - 'LFO Smoothing'
    - 'LFO Q Mode'
    - 'LFO Steps'
    - 'LFO S&H'
  conclusion: AutoFilter2's "LFO Rate" knob in the GUI is a meta-display: its underlying API param depends on the `LFO T Mode` enum value (Hz / S / 4 / 16). The four are NOT aliased — they're four independent params. There is NO single param called 'LFO Frequency' (that's the Live 9/10 AutoFilter name; Live 11+ split it). 'LFO Rate' DOES exist but only governs sync mode 4 (4-bar subdivision); twisting it has no visible effect when AutoFilter is in the default Hz mode. That perfectly matches the user's pre-fix symptom: dead encoder, log clean, no exception.

- timestamp: 2026-05-04T15:55:00Z
  observation: Architectural pattern already exists in this same file: encoders 5/6 swap based on `Filter Type` enum value (Vowel → Pitch/Formant; DJ → Control/—; else → Frequency/Resonance), with a value listener on `Filter Type` re-binding on change. Same pattern applies to encoder 4 vs `LFO T Mode`.
  conclusion: Apply the established pattern: read `LFO T Mode`, resolve to one of (`LFO Freq`, `LFO Time`, `LFO Rate`, `LFO 16th`), bind encoder 4 to the resolved param. Add a value listener on `LFO T Mode` so encoder rebinds on user mode change.

## Round 3 — UAT result + label-prefix gap

- timestamp: 2026-05-04T16:10:00Z
  observation: Hz / 4 / 16 modes work after Round-2 fix. Time mode still fails — encoder doesn't bind to LFO Time when user switches LFO T Mode to Time/S. Hypothesis: AutoFilter2's value_items label for the Time-mode entry is "Time" (not "S" or "Sec"), so the prefix list missed it and fell through to the first-existing-rate-param fallback (LFO Freq) — meaning encoder 3 stayed bound to LFO Freq even in Time mode. Twisting moves LFO Freq's stored value but the visible Time knob doesn't track because Time mode shows LFO Time, not LFO Freq.
  conclusion: Expand LFO_T_MODE_PARAM_KEYS to include 'Time', 'Hertz', '1/16'. Add a one-shot dump of `LFO T Mode.value_items` (analogous to the params dump) so future unmatched labels are immediately visible. Add a `log_message` warning when the fallback path triggers (so silent wrong-bindings can't recur).

## Round 4 — Six modes, not four; switch to exact-match dict

- timestamp: 2026-05-04T16:25:00Z
  observation: User reload + UAT log shows actual `LFO T Mode.value_items = ['Rate', 'Time', 'Synced', 'Triplet', 'Dotted', 'Sixteenth']` (six labels, not four). Round-3 prefix list missed 'Rate', 'Triplet', 'Dotted' (unmatched warnings emitted) and silently bound 'Synced' + 'Sixteenth' to LFOTime via the 'S' prefix collision. Only 'Rate' (lucky fallback to LFOFreq) and 'Time' (matched 'Time' prefix) were correct.
  conclusion: Replace the prefix-startswith list with an exact-match dict keyed by the verified labels. Mapping:
    - 'Rate' / 'Time' / 'Sixteenth' → LFOFreq / LFOTime / LFO16th (the three dedicated rate params)
    - 'Synced' / 'Triplet' / 'Dotted' → LFORate (single beat-subdivision param; T Mode chooses timing interpretation)
    Update `_resolve_lfo_rate_param` to `LFO_T_MODE_PARAM_KEYS.get(label)`.

## Round 4 — Final Resolution

root_cause: AutoFilter2 has FOUR distinct LFO rate parameters, one per `LFO T Mode` setting. There is no single canonical "LFO Rate" param — the GUI knob is a meta-display that maps to whichever underlying param is active. The original `'LFO Rate'` binding was technically successful but bound to the inactive 4-bar-sync rate (so twisting changed an invisible param value with no audible/visible effect — matches "encoder dead, log clean"). The first-round fix to `'LFO Frequency'` made things worse because that param simply does not exist on AutoFilter2 (it's the Live 9/10 name); `get_parameter_by_name` returned None, `connect_to(None)` ran, LED ring went dark.

fix: Apply the same enum-driven re-bind pattern already used for `Filter Type` (encoders 5/6) but for `LFO T Mode` (encoder 4):
  1. Map `'LFO T Mode'` value_items label → underlying rate-param name (Hz→'LFO Freq', S→'LFO Time', 4→'LFO Rate', 16→'LFO 16th').
  2. New helper `_resolve_lfo_rate_param(device)` returns the active rate param.
  3. New helper `_bind_lfo_rate_encoder(device)` releases encoder 3 and binds it to the resolved param.
  4. Add a value listener on `LFO T Mode` (`_attach_lfo_t_mode_listener` / `_detach_lfo_t_mode_listener`) that re-binds encoder 3 on mode change.
  5. Remove encoder 3 from the static ENCODER_MAP (it's now dynamic, like encoders 4/5).
  6. Remove the now-misleading `'LFORate'` AUTOFILTER_PARAMS entry; introduce `'LFO_T_Mode'` and four rate-name entries instead.
