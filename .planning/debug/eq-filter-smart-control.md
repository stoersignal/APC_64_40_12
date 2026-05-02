---
slug: eq-filter-smart-control
status: resolved
trigger: |
  DATA_START
  Alternate Device & EQ/Filter Smart Control
  DATA_END
created: 2026-05-02T11:05:52Z
updated: 2026-05-02T11:30:00Z
diagnose_only: false
tdd_mode: false
---

# Debug: EQ/Filter Smart Control mapping mismatch

## Symptoms

Issue type: Wrong behavior
Timeline: Don't know
Reproducibility: Reliably, every time

### Expected vs actual

DATA_START
the combo to enter that mode should be shift+Note 89 (not Note 60). the kill
switches from EQ3 are working, but the levels for bass, mids and highs not.
they should be mapped to bass:CC53, Mids:CC54, Highs:CC55.
DATA_END

### Decoded symptom matrix

| Aspect              | Expected      | Actual         | Status        |
|---------------------|---------------|----------------|---------------|
| Activation combo    | Shift+Note 89 | Note 60        | Wrong binding |
| EQ3 kill switches   | Functional    | Functional     | OK            |
| Bass encoder        | CC53          | (not working)  | Wrong / unmapped |
| Mids encoder        | CC54          | (not working)  | Wrong / unmapped |
| Highs encoder       | CC55          | (not working)  | Wrong / unmapped |

## Investigation context

- Project is the APC40 MIDI Remote Script for Ableton Live (Python 3, runs in Live's embedded interpreter).
- Likely-relevant source files (untracked at repo root, present on disk):
  - `EncoderEQComponent.py` — EQ encoder mode component
  - `EncModeSelectorComponent.py` — encoder-mode dispatcher (Pan / SendA / SendB / SendC / User1..3)
  - `ShiftableSelectorComponent.py` — shift-modified mode dispatch
  - `Matrix_Maps.py` — Note Mode 1-6 PATTERN_N / NOTEMAP_N / CHANNEL_N tables
  - `MatrixModesComponent.py` — matrix mode selection
  - `APC_64_40_9.py` — top-level wiring (mode selector instantiation, control bindings)

## Current Focus

hypothesis: |
  Activation is correctly wired to Shift+Note 89 (mode index 2 of EncoderUserModes,
  driven by the global bank-button strip notes 87..90 = Pan/SendA/SendB/SendC under
  shift). The level-encoder bindings ARE in principle correct (param_controls[5..7]
  = CC53/54/55) — but `TrackEQComponent.set_gain_controls()` raises an exception
  unconditionally due to malformed Python `raise <bool> or AssertionError` lines,
  so the gain controls never actually get assigned to parameters.
test: confirmed by reading source — see Evidence below
expecting: confirmed
next_action: applied
reasoning_checkpoint: ""
tdd_checkpoint: ""

## Evidence

- timestamp: 2026-05-02T11:25:00Z
  observation: |
    `_setup_global_control` in APC_64_40_9.py (line 269-276) creates the 8 global
    encoders as RingedEncoderElement at MIDI_CC_TYPE channel 0, identifier `48 + index`.
    -> Index 5 = CC53, index 6 = CC54, index 7 = CC55. This matches the user's
    expected bass/mid/high mapping exactly. The global bank buttons (line 280)
    are at MIDI_NOTE_TYPE channel 0, identifier `87 + index` -> Notes 87, 88, 89, 90.
- timestamp: 2026-05-02T11:25:30Z
  observation: |
    `EncoderEQComponent._update_controls_and_buttons` (lines 503-505) wires:
      cut_buttons       = buttons[1..3]       (passed by caller)
      gain_controls     = param_controls[5..7]  -> CC53/54/55 ✓ matches expected
      filter freq/reso  = param_controls[0], param_controls[4]  -> CC48, CC52
      sends             = param_controls[1..3]  -> CC49/50/51
    So the design intent IS bass=CC53, mids=CC54, highs=CC55.
- timestamp: 2026-05-02T11:26:00Z
  observation: |
    Activation path: ShiftableEncoderSelectorComponent toggles between
    EncModeSelector (shift NOT held) and EncoderUserModesComponent (shift held).
    EncoderUserModesComponent.number_of_modes() = 4 with mode index 2 enabling
    `_encoder_eq_modes` (line 149-151). The 4 mode-buttons are the bank buttons
    at notes 87/88/89/90, so mode 2 = Note 89 = "SendB while shift held".
    ⇒ Activation IS already on Shift+Note 89. The user's "Note 60" claim does
    not correspond to any binding in the code. Note 60 only appears in
    Matrix_Maps.py as a NOTEMAP_N matrix-cell entry, unrelated to EQ activation.
- timestamp: 2026-05-02T11:26:30Z
  observation: |
    SMOKING GUN: `TrackEQComponent.set_gain_controls` (EncoderEQComponent.py
    lines 124-137 — pre-fix) used the broken pattern:
        raise controls != None or AssertionError
        raise isinstance(controls, tuple) or AssertionError
    In Python, `raise <expr>` requires <expr> to be an exception. Here:
      - if controls is non-None: `controls != None or AssertionError` → True → raise True → TypeError
      - if controls is None:     `False or AssertionError` → AssertionError → raise AssertionError
    Either way the function aborts before reaching `self._gain_controls = controls`
    and `self.update()`. Result: gain encoders are NEVER bound to bass/mid/high
    parameters when EQ Smart Control is entered. Cut buttons are wired by
    `set_cut_buttons` (line 109-122), which uses correct `if not (...): raise
    AssertionError` syntax — so kills work. This perfectly matches the symptom
    split (kills OK, levels broken).

## Eliminated

- Activation-binding hypothesis: there is no Note 60 binding for EQ Smart Control
  anywhere in the codebase. The activation has been Shift+Note 89 the whole time.
  The user's report on this point is descriptive noise — the actual reproducible
  bug is the second symptom (broken levels), and that has a different cause.
- Wrong CC numbers / wrong parameter names: EQ_DEVICES['FilterEQ3'] correctly
  lists ['GainLo','GainMid','GainHi'] and the encoder index slice [5:8] yields
  CC53/54/55, exactly as expected.
- Filter / sends path wired separately: not the cause; they share the same broken
  `_update_controls_and_buttons` path but the user only reported levels.

## Resolution

root_cause: |
  `TrackEQComponent.set_gain_controls` in EncoderEQComponent.py used malformed
  Python `raise <bool> or AssertionError` lines that unconditionally raise an
  exception (Python 3 turns `raise True` into TypeError; otherwise AssertionError).
  The function aborted before assigning `self._gain_controls`, so the bass/mid/high
  encoders were never bound to GainLo/GainMid/GainHi on the FilterEQ3 device.
  The kill-switch path uses a different, correctly-written method
  (`set_cut_buttons`), explaining why kills worked but levels did not.

  Activation is already correctly wired to Shift+Note 89 via
  ShiftableEncoderSelectorComponent → EncoderUserModesComponent mode index 2,
  with the global bank buttons at notes 87..90. No "Note 60" binding exists in
  the source for EQ activation; that part of the user report does not correspond
  to a code-level bug.

fix: |
  Rewrote `TrackEQComponent.set_gain_controls` (EncoderEQComponent.py lines
  124-138) to use the same idiom as `set_cut_buttons`:
      if not (controls == None or isinstance(controls, tuple)):
          raise AssertionError
      ...
      if controls != None:
          for control in controls:
              if not isinstance(control, EncoderElement):
                  raise AssertionError
  Now the function completes, assigns `self._gain_controls`, and calls
  `self.update()` which connects each gain encoder (CC53, CC54, CC55) to the
  corresponding FilterEQ3 parameter (GainLo, GainMid, GainHi).

  No change was needed for the activation combo (Shift+Note 89) — it was already
  correctly wired.

verification: |
  - Static check: `python3 -m py_compile EncoderEQComponent.py` → clean.
  - Runtime check (manual, in Ableton): with shift held, press Note 89 (SendB
    button on the APC40). The Pan/SendA/SendB/SendC button row should switch to
    indicate EQ Smart Control is active (Pan acts as lock, SendA/B/C act as
    band-kill buttons). Turning the rightmost three top-row encoders (CC53/54/55)
    should now move the GainLo / GainMid / GainHi parameters of the last
    FilterEQ3 device on the selected track. Kill buttons should continue to work
    as before (regression check).

files_changed:
  - EncoderEQComponent.py
