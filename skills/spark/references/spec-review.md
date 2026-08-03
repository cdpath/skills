# Spec review

Run this after a spec draft lands in `docs/`. Goal: verify the spec is complete, consistent, and ready for implementation planning.

## Five dimensions

1. **Complete** — every section is drafted; no placeholders left behind.
2. **Consistent** — no section contradicts another.
3. **Clear** — requirements are not open to multiple interpretations.
4. **Bounded** — scope is explicit, and out-of-scope is stated.
5. **Lean** — free of unneeded complexity.

## What counts as a blocker

Only flag issues that would cause real problems during implementation:

- absent sections,
- contradictory directives,
- requirements open to multiple interpretations.

Do not block on cosmetics. Cosmetic concerns should not prevent acceptance.

## Deliverable

Return a status and a list:

- **Status:** `Approved` or `Issues Found`.
- **Material problems:** the blockers above, each with where it occurs.
- **Non-blocking advice:** optional, clearly labeled as such.

If the status is `Issues Found`, fix the material problems in the spec and re-run this review before sign-off.
