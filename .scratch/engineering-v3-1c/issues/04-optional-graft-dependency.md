# 04: Make Graft an optional capability in dependencies and doctor

**Spec:** [Consumer verification and optional navigation](../spec.md)

**What to build:** A project with navigation provider `none` sets up, reports
dependency status and passes doctor without Graft. The dependency registry marks
Graft with a generic navigation capability so it is required only while
navigation selects it. Doctor reports navigation as disabled, ready, enabled
without roots (warning) or enabled but broken.

**Blocked by:** None (can start immediately).

**Status:** implemented — awaiting independent verification

- [x] The registry supports a generic optional capability field; Graft declares the navigation capability.
- [x] Dependency status, setup and doctor treat a capability dependency as required only while its provider selects it.
- [x] With provider `none`, setup, dependency status and doctor succeed without Graft installed; doctor reports navigation disabled.
- [x] With provider `graft`, roots configured and valid pins, doctor passes.
- [x] With provider `graft` and no roots, doctor passes with a non-blocking warning and next step.
- [x] With provider `graft` and missing, stale or mispinned installation, doctor fails with fixes including setting `none`.
- [x] Verification still requires the Graft check only when Graft is selected and roots exist.
- [x] Command-level doctor and deps fixture tests cover each state.
- [x] Dependency and doctor documentation describe the capability rule; affected evals updated.
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review.

## Comments

- Implementation (branch `feat/v3-1c-04-optional-graft-dependency`): generic
  `capability` registry field and `CAPABILITIES` provider table in settings;
  `required`/`selected` rule shared by `deps status`, `deps install/update`
  (setup) and doctor; doctor reports navigation disabled (INFO), enabled without
  roots (WARN) and broken (ERROR with `provider = "none"` as a fix); pin,
  launcher and runtime checks run only while Graft is selected; the verification
  Graft-check rule also requires provider `graft`.
- Evidence: command-level fixture tests in `test_doctor.py`,
  `test_dependencies.py` and `integration/test_verification.py`; `make
  engineering-test` passed locally. Independent verification, human acceptance,
  publication and merge remain outstanding.
- Remaining for ticket 05: template default `none`, conditional Graft managed
  content (launcher, skill, package pins) and agent-policy guidance.
