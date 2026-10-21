# Remaining Work — What the Spec Still Asks For

**Date:** 21 October 2026
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

Phases 1 and the whole of the spec's test suite are done. The list below is
what is left for phases 2 to 6.

---

## §4 Authentication

1. **TODO — the focus does not start in the Email field.** `ui/pages/login.py`
   binds Enter but never calls `focus_set()` on the first field.
2. **PART — the sign-in button is called "Sign In".** The spec (§4.1) and the
   navigation bar both say **"Log In"**. One word to change.
3. **DEV — there is no first-run "Create Admin Account" screen.** The spec
   (§4.3) asks for one; the agreed deviation is that the first-run password
   is printed in the console instead. `python -m cleanhome.reset_password`
   now covers the recovery case. Build the screen only if you want it.

## §5 Interface

4. **PART — an invalid input does not get a red border.** The spec (§5.4)
   wants a red border on a field that failed validation. Today the error
   message is red, the border is not. Needs an `Invalid.TEntry` style and a
   `FormField.set_error()` that switches to it.
5. **PART — the focus ring is one pixel.** The spec (§5.4) asks for a 2px
   PRIMARY ring; `theme.py` changes the 1px border colour on focus.
6. **TODO — no `hand2` cursor on the buttons.** The spec (§5.4) wants the
   hand cursor on clickable things. Only the nav items have it.
7. **TODO — the tab order is not set.** The spec (§5.4) wants a logical tab
   order. Today it is the order the widgets were created in.
8. **TODO — the page background is flat.** The reference image has a soft
   gradient (≈`#E8EAEE` in the top-left corner, easing to `#F5F7F9` on the
   right). `theme.BG_PAGE` is a single flat colour. Phase 3 can fake the
   gradient with a canvas or a flat approximation.

## §5.7 Required UX

9. **TODO — the Home page has no promotions section.** The spec (§7.4.1)
   asks for hero, featured services, **active promos**, why-choose-us, and
   footer. The hero, three featured services, and how-it-works are there;
   the promos are not.
10. **TODO — the Home page has no why-choose-us section.** Same clause.
11. **PART — "Book Now" and "View Details" are not the same width.** The spec
    (§5.7) wants them equal and aligned on the service card. They are two
    different buttons with different labels.
12. **PART — three admin pages still use `messagebox.showerror`.** The spec
    (§5.7) wants a toast or an inline message, and keeps `messagebox` only
    for destructive confirmations. The three calls are in
    `admin_customers.py`, `admin_promotions.py`, and `admin_services.py`.
13. **PART — archiving a service and deactivating a customer ask for no
    confirmation.** The spec (§5.7) says to confirm before destructive
    actions and names archive service explicitly.
14. **PART — the Home page says "up to a year ahead".** The booking window is
    `config.BOOKING_WINDOW_DAYS` = 30 days. The copy has to match the rule.

## §7 Business logic

15. **PART — the booking summary is missing three of the six lines.** The
    spec (§7.2) wants service, date/time, address, price, discount, and
    total before the customer confirms. The price card in
    `ui/pages/book.py` shows price, discount, and total only.
16. **TODO — the admin Bookings screen has no date filter.** The spec
    (§7.5.2) wants a filter by status, by date, and a search by customer.
    Status and search are there; date is not.
17. **PART — a service has no "inclusions" list.** The spec (§5.7) wants
    inclusions on the service details page. The schema has no column for
    them, so this needs a migration as well as the screen.

## §8 / §11 Project shape

18. **TODO — there is no `main.py` in the project root.** The spec (§11.1)
    says the app is launched with `python main.py`. Right now it is
    `python -m cleanhome.main` (or `python cleanhome/main.py`). A three-line
    shim at the root would satisfy the spec.

## Phase 3 — matching the reference image

19. **The reference image is now in the project root** as
    `ui that i like.webp` (1600 × 1073). It was missing during phases 0–2,
    so the screens were built from the token table in the spec (§5.1) alone.
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

20. **TODO — the screens have not been compared with the image section by
    section.** Phase 3 should walk Home, Services, and Service details
    against the image, fix the arrangement, the spacing, the card padding,
    and the section order, and keep the Tkinter limits in mind: flat cards,
    1px borders, no blur, no true rounded corners.

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
