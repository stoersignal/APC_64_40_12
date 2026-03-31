# Phase 4: 16-Parameter Encoder Mapping - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.

**Date:** 2026-03-31
**Phase:** 4-16-Parameter Encoder Mapping
**Areas discussed:** Component design, Mode switching, Bank navigation

---

## Component Design

| Option | Description | Selected |
|--------|-------------|----------|
| New Pan16DeviceComponent (Recommended) | New file, ~50 lines. Two instances. Mirrors EncoderDeviceComponent pattern. | ✓ |
| Extend EncoderDeviceComponent | Add 16-param mode to existing component | |
| You decide | Claude picks | |

**User's choice:** New Pan16DeviceComponent

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, both track device (Recommended) | Both instances listen for appointed_device changes | ✓ |
| Only bottom row tracks | Top row stays fixed | |

**User's choice:** Both track device

---

## Mode Switching

| Option | Description | Selected |
|--------|-------------|----------|
| Replace pan with device params (Recommended) | Pan mode maps device params instead of per-track pan | ✓ |
| Keep pan on different row | Move pan to sliders | |

| Option | Description | Selected |
|--------|-------------|----------|
| Fully disconnect (Recommended) | release_parameter() on all 16, disable both instances | ✓ |
| Keep device encoders mapped | Only disconnect top 8 | |

---

## Bank Navigation

**User clarification:** Device encoders have their own buttons (device/on-off/prev bank/next bank). Top encoders have Pan/Send A/B/C. These are separate control groups.

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-set to bank 1 (Recommended) | Entering Pan mode forces device encoders to bank 1 (params 9-16). Bank buttons work deeper. | ✓ |
| Keep current bank | User manually navigates | |

## Claude's Discretion

- Pan16DeviceComponent internal structure (extend vs wrap DeviceComponent)
- Handling devices with <16 parameters
- Internal naming

## Deferred Ideas

None
