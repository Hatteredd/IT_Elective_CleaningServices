# Remaining Work — What the Spec Still Asks For

**Date:** 22 October 2026
**Spec:** `CLEANHOME_IMPROVEMENT_SPEC.md`
**Rule for this file:** anything already built, tested, and working is not
repeated here. Only the gaps are listed.

---

## How to read this

| Marker | Meaning |
|--------|---------|
| **TODO** | not built yet — work to do |
| **PART** | partly built — the part listed is what is missing |
| **DEV** | a deliberate deviation, already agreed — do not build unless asked |

Phases 1–2 and the spec's test suite are done. The items below are what is
left, grouped by the spec section that asks for them.

---

## §5 Interface

1. **TODO — the page background is flat.** The reference image has a soft
   gradient (≈`#E8EAEE` in the top-left corner, easing to `#F5F7F9` on the
   right). `theme.BG_PAGE` is a single flat colour. Phase 3 can fake the
   gradient with a canvas or accept the flat approximation.

2. **TODO — the screens have not been compared with the image section by
   section.** The reference image is in the project root as
   `ui that i like.webp` (1600 × 1073). Phase 3 should walk Home, Services,
   and Service details against it and fix arrangement, spacing, card
   padding, and section order, keeping the Tkinter limits in mind: flat
   cards, 1px borders, no blur, no true rounded corners.

    What was measured from the image:

    | What | Measured |
    |------|----------|
    | Canvas | 1600 × 1073 |
    | Page background | a soft gradient, `#E8EAEE` top-left → `#F5F7F9` right |
    | Section rules | full-width 1px rules at y ≈ 112, 416, 640, 928 |
    | Footer | a bordered block from y ≈ 1008 to 1040 |
    | Primary buttons | ≈ 132 × 32 px (blue `#0A6CF0`), with rounded corners |
    | Large heading | ≈ 240 × 48 px of near-black text, lower third of the page |
    | Card grid | four columns in the first card row, three in the lower rows |

## §7 Business logic

3. **TODO — a service has no "inclusions" list.** The spec (§5.7) wants
   inclusions on the service details page. The schema has no column for
   them, so this needs a migration as well as the screen.

---

## Not being built (agreed)

* No online payment.
* No email or SMS.
* No server, no multi-user sync, no web version.

## Not planned (still true after phase 6)

* No bulk cancel.
* No per-booking team assignment.
* No pagination in the admin tables.
* English only.
