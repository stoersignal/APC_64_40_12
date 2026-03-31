# Milestones

## v1.1 16Macros (Shipped: 2026-03-31)

**Phases completed:** 2 phases, 5 plans, 5 tasks

**Key accomplishments:**

- Pan16DeviceComponent subclass with set_device() re-assertion override and 7 unit tests verifying bank-0/bank-1 isolation using _Framework stubs injected via sys.modules
- Promoted device_param/bank_button locals to instance variables in APC_64_40_9 and injected Pan16DeviceComponent references into EncModeSelectorComponent via new set_pan16_components() setter
- Rewrote EncModeSelectorComponent.update() to assign both encoder rows to Pan16DeviceComponent instances in Pan mode and added on_enabled_changed() to prevent stale encoder bindings on shift mode changes
- One-liner:
- One-liner:

---

## v1.0 Toggle/Momentary (Shipped: 2026-03-31)

**Phases completed:** 3 phases, 3 plans, 6 tasks

**Key accomplishments:**

- ToggleMomentaryChannelStripComponent subclass created with six press-state variables, timer stub calling parent fold-delay logic first, and SpecialMixerComponent factory switched to new class
- Toggle/momentary state machine: press-down inversion, 4-tick countdown via _on_timer, release-time revert, shift guard in set_solo/mute_button — 43 unit tests all passing
- 18-test multi-track suite proves MULTI-01/02/03 per-instance isolation via two simultaneous strip instances; disconnect() hardened with momentary revert guards matching the set_solo_button() pattern

---
