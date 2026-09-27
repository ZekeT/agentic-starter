# 04: Make Graft an optional capability in dependencies and doctor

**Spec:** [Consumer verification and optional navigation](../spec.md)

**What to build:** A project with navigation provider `none` sets up, reports
dependency status and passes doctor without Graft. The dependency registry marks
Graft with a generic navigation capability so it is required only while
navigation selects it. Doctor reports navigation as disabled, ready, enabled
without roots (warning) or enabled but broken.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] The registry supports a generic optional capability field; Graft declares the navigation capability.
- [ ] Dependency status, setup and doctor treat a capability dependency as required only while its provider selects it.
- [ ] With provider `none`, setup, dependency status and doctor succeed without Graft installed; doctor reports navigation disabled.
- [ ] With provider `graft`, roots configured and valid pins, doctor passes.
- [ ] With provider `graft` and no roots, doctor passes with a non-blocking warning and next step.
- [ ] With provider `graft` and missing, stale or mispinned installation, doctor fails with fixes including setting `none`.
- [ ] Verification still requires the Graft check only when Graft is selected and roots exist.
- [ ] Command-level doctor and deps fixture tests cover each state.
- [ ] Dependency and doctor documentation describe the capability rule; affected evals updated.
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review.

## Comments
