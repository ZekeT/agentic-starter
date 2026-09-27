# 05: Enable and disable navigation

**Spec:** [Consumer verification and optional navigation](../spec.md)

**What to build:** Navigation-specific managed content — the Graft skill,
launcher, package pins and agent-policy navigation guidance — exists only while
navigation selects Graft. New consumer projects start with navigation `none` and
none of that content. Enabling uses the existing dependency preview and install;
disabling uses an update whose preview lists the removals, keeping the Graft
index and root settings.

**Blocked by:** 02 (Make Engineering configuration project-owned), 04 (Make Graft an optional capability in dependencies and doctor).

**Status:** implemented — awaiting independent verification

- [x] A newly generated consumer project defaults to provider `none` and contains no Graft skill, launcher, package pins or navigation guidance.
- [x] Agent-policy navigation guidance is its own managed section, present only while Graft is selected; otherwise policy directs agents to ordinary search and source reading.
- [x] Setting provider `graft` and applying the dependency flow previews then installs the pinned package, launcher, skill, pins and guidance together.
- [x] Setting provider `none` and updating previews and removes that content and its gate obligations.
- [x] Disabling never removes the Graft index or application-root values.
- [x] With provider `none`, the Graft launcher and navigation command refuse to run with a clear "navigation disabled" message, and verification rejects a plan that lists the Graft check (ticket 04 security review: the launcher currently ignores the provider).
- [x] Capability validation fails with a configuration error, not an unhandled exception, for any capability section — including ones added later (ticket 04 maintainability review: the capability loop relies on the section being listed in the validated fields).
- [x] After disabling, no Graft skill or guidance remains loadable by agents; doctor no longer inspects unselected Graft (ticket 04), so leftover or locally modified Graft content must not stay silently in use.
- [x] Template contents, setup, doctor, dependency status and verification agree about navigation optionality.
- [x] Command-level generation, update and deps fixture tests cover default, enable and disable.
- [x] Generated README and onboarding reflect the `none` default; affected policy evals updated.
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review.

## Comments

- Implementation (branch `feat/v3-1c-05-toggle-navigation`, local commit only):
  navigation content (Graft package pins, skill, launcher and a `navigation`
  section in `CLAUDE.md`) is defined by the navigation module (`graft.CONTENT`)
  and installed together as the Graft dependency's outputs; section outputs are
  fingerprinted by owned scope. Generation ships none of it (template provider
  `none`; `build_template` strips the guidance section); `engineering update`
  removes pristine content of a deselected capability (new `capabilities.py`),
  conflicts on customization, forgets the dependency record and keeps the Graft
  index and roots; pre-existing launcher baselines transfer visibly (PRESERVE)
  while Graft stays selected. Navigation command refuses when disabled;
  verification rejects a listed Graft check with `none`; doctor fails on leftover
  agent-loadable Graft content and reports MODIFIED/OUTDATED navigation content
  while selected; every capability section is validated as an object.
- Evidence (implementer-run, not independent): `make check` all ✓;
  `make engineering-test` 364 passed; `make engineering-evals` 12/12 static
  passed (new `012-optional-navigation`). Command-level tests in
  `.engineering/tests/test_navigation.py` cover default, enable and disable.
- Remaining: independent maintainability/behavioral verification and human
  review. Upgrade proposal `graft → none` for existing installations is ticket 06.
  Disabling leaves the ignored `.engineering/graft/node_modules/` install in place.
