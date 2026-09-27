# 05: Enable and disable navigation

**Spec:** [Consumer verification and optional navigation](../spec.md)

**What to build:** Navigation-specific managed content — the Graft skill,
launcher, package pins and agent-policy navigation guidance — exists only while
navigation selects Graft. New consumer projects start with navigation `none` and
none of that content. Enabling uses the existing dependency preview and install;
disabling uses an update whose preview lists the removals, keeping the Graft
index and root settings.

**Blocked by:** 02 (Make Engineering configuration project-owned), 04 (Make Graft an optional capability in dependencies and doctor).

**Status:** ready-for-agent

- [ ] A newly generated consumer project defaults to provider `none` and contains no Graft skill, launcher, package pins or navigation guidance.
- [ ] Agent-policy navigation guidance is its own managed section, present only while Graft is selected; otherwise policy directs agents to ordinary search and source reading.
- [ ] Setting provider `graft` and applying the dependency flow previews then installs the pinned package, launcher, skill, pins and guidance together.
- [ ] Setting provider `none` and updating previews and removes that content and its gate obligations.
- [ ] Disabling never removes the Graft index or application-root values.
- [ ] With provider `none`, the Graft launcher and navigation command refuse to run with a clear "navigation disabled" message, and verification rejects a plan that lists the Graft check (ticket 04 security review: the launcher currently ignores the provider).
- [ ] Capability validation fails with a configuration error, not an unhandled exception, for any capability section — including ones added later (ticket 04 maintainability review: the capability loop relies on the section being listed in the validated fields).
- [ ] After disabling, no Graft skill or guidance remains loadable by agents; doctor no longer inspects unselected Graft (ticket 04), so leftover or locally modified Graft content must not stay silently in use.
- [ ] Template contents, setup, doctor, dependency status and verification agree about navigation optionality.
- [ ] Command-level generation, update and deps fixture tests cover default, enable and disable.
- [ ] Generated README and onboarding reflect the `none` default; affected policy evals updated.
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review.

## Comments
