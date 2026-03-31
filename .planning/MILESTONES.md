# Milestones

## v1.0 Toggle/Momentary (Shipped: 2026-03-31)

**Phases completed:** 3 phases, 3 plans, 6 tasks

**Key accomplishments:**

- ToggleMomentaryChannelStripComponent subclass created with six press-state variables, timer stub calling parent fold-delay logic first, and SpecialMixerComponent factory switched to new class
- Toggle/momentary state machine: press-down inversion, 4-tick countdown via _on_timer, release-time revert, shift guard in set_solo/mute_button — 43 unit tests all passing
- 18-test multi-track suite proves MULTI-01/02/03 per-instance isolation via two simultaneous strip instances; disconnect() hardened with momentary revert guards matching the set_solo_button() pattern

---
