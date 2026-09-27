# 03: Derive verification requirements from role and ownership

**Spec:** [Consumer verification and optional navigation](../spec.md)

**What to build:** Verification planning decides required checks from the
installation role and each changed path's ownership instead of the path prefix.
A consumer project can change its configuration and verify it with its normal
checks plus Engineering health checks. Editing managed implementation in a
consumer project is rejected with the supported route. Maintainer source in the
maintainer checkout still requires the maintainer suites.

**Blocked by:** 01 (Record the installation role), 02 (Make Engineering configuration project-owned).

**Status:** implemented — awaiting independent verification

- [x] A generated consumer project changes application roots or maintainability settings and prepares a valid plan with `make check` and `make engineering-check`, requiring no nonexistent target.
- [x] Invalid project configuration fails verification visibly.
- [x] A consumer change to managed implementation is rejected with an explanation and the update/upstream route; the outcome is INCOMPLETE, never PASS.
- [x] Maintainer source changes in the maintainer checkout still require `make engineering-test` and `make engineering-evals`.
- [x] The maintainer checkout's own configuration change requires only `make check` and `make engineering-check`.
- [x] Removing a maintainer Make target cannot lower the required checks.
- [x] Generated and adopted consumer projects classify identically.
- [x] Requirements never depend on which Make targets happen to exist.
- [x] Command-level `verify prepare` fixture tests cover each case above.
- [x] Verification documentation, `/review` guidance and project instructions describe role-based requirements; affected evals updated.
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review.

## Comments

### Decisions (grilled 2026-09-27, human-approved)

- **Recorded role is trusted.** No extra check refuses `maintainer` outside the starter repository (ADR 0001 rejects inference). A wrong role fails closed: a consumer declaring `maintainer` is required to run maintainer suites it lacks; a maintainer checkout declaring `consumer` has its tooling edits rejected as managed-implementation edits. Document this; a role change is visible in the PR diff.
- **Project configuration = every manifest `preserve` entry** (currently `.engineering/config.toml`, `.engineering/dependencies.toml`, Graft package pins, `docs/agents/domain.md`, `docs/agents/issue-tracker.md`). Required: `make check` plus `make engineering-check`.
- **`section` and `hooks` files** (`CLAUDE.md`, `AGENTS.md`, `Makefile`, `.gitignore`, `.claude/settings.json`) are treated like project configuration: `make check` plus `make engineering-check`. Doctor already detects tampered managed sections or inactive hooks, so no second section parser is added.
- **Maintainer source (role `maintainer` only)** = all `file`-mode manifest entries plus non-distributed starter tooling (`.engineering/template/**`, `.engineering/tests/**`, `.engineering/evals/**`, `.engineering/scripts/**`, `.engineering/migrations/**`). Requires `make engineering-test` and `make engineering-evals` in addition. `preserve`/`section`/`hooks` paths follow the same rules in both roles.
- **Consumer edits to `file`-mode managed implementation** are rejected with the supported update/upstream route; outcome INCOMPLETE.

### Decisions (2026-09-27, security review follow-up, human-approved)

1. **No update-output exemption.** Any consumer change (edit or deletion) to a path whose ownership is `file` in the base or proposed manifest is rejected with the update/upstream route; outcome INCOMPLETE, regardless of manifest hashes (the proposed manifest is consumer-controlled). Consumer starter-update PRs are not yet verifiable; follow-up [08](08-verified-starter-update-evidence.md).
2. **Effective role = stricter of base and proposed role** (`maintainer` is stricter), mirroring the base∪proposed manifest rule; a role change takes effect only after it merges (supersedes "maintainer declaring `consumer` has tooling edits rejected" above). With no base install state or role, the proposed role applies (missing-role blocking still applies to proposed content). The recorded role is otherwise trusted.
3. **Installation metadata** (`.engineering/manifest.json`, `.engineering/state/install.json`) requires `make check` plus `make engineering-check`.

### Decisions (2026-09-28, behavioral review follow-up, human-approved)

4. **Q4 — maintainer installation metadata is maintainer source.** With effective
   role `maintainer`, changes to `.engineering/manifest.json` and
   `.engineering/state/install.json` require `make engineering-test` and
   `make engineering-evals` in addition to `make check` and
   `make engineering-check`: that manifest is the ownership contract every
   consumer receives. (Behavioral review: a manifest-only change dropping the
   `growth.py` entry and switching `cli.py` to `preserve` was accepted with only
   `make check`.) Consumer role keeps decision 3 (`make check` +
   `make engineering-check`).
5. **Q5 — invalid TOML names the file.** The configuration parse error from
   verification planning is reported as `.engineering/config.toml: <parser message>`.

### Implementation evidence (2026-09-27, commit c5cc605 on `feat/v3-1c-03-role-based-verification`)

Implementation only: not verification, human acceptance, publication or merge.

- Classification lives in `.engineering/engineering/verification_requirements.py`,
  called from `verification_checkout.materialize`, so role (`installation_role`)
  and ownership come from the proposed content on every prepare/status/check/record.
  Ownership is the union of the proposed and base `.engineering/manifest.json`
  (dropping an entry cannot lower requirements); a proposed manifest is required.
  The old `.engineering/` prefix rule in `validate_plan` is removed; the Graft rule
  moved unchanged into the same module. The proposed configuration is fully
  validated (including maintainability) so invalid values fail `prepare`.
- The original "update output" assumption (consumer bytes matching the proposed
  manifest counted as update output) and "metadata is a project path" were
  superseded by the security review follow-up decisions 1 and 3 above.
- Tests: new `.engineering/tests/integration/test_verification_requirements.py`
  (31 command-level `verify prepare` cases on generated, adopted and
  maintainer-checkout fixtures); `test_verification.py` fixture gains a manifest;
  the greenfield journey plan adds `make engineering-check` for its Makefile edit.
- Docs: verification guide requirement table, ENGINEERING.md, CLAUDE.md sentence,
  verifier agent, `/review`; eval 007 asserts the role-based wording.
- Gates run locally after `make fmt` and one `make manifest`: `make check` exit 0;
  `make engineering-test` exit 0 (385 passed); `make engineering-evals` exit 0
  (11/11 static, 5 prompt cases skipped). Independent review not yet done.

### Security review corrections (2026-09-27, commit c863e5b)

Implementation of human-authorized decisions 1–3 above; not verification,
human acceptance, publication or merge. The independent security review had
failed with one HIGH, one MEDIUM and one LOW finding.

- Decision 1: `verification_requirements.classify` no longer consults manifest
  digests; a consumer `file`-mode path whose proposed bytes differ from the base
  commit (edit or deletion) is rejected. Unchanged distributed files listed in a
  plan still need only `make engineering-check`.
- Decision 2: a base `install.json` recording `maintainer` keeps `maintainer`
  whatever the proposed role; otherwise the proposed role applies.
- Decision 3: new category "installation metadata" requires `make engineering-check`.
- Tests first: 9 new `verify prepare` cases (forged digest, deletion plus dropped
  entry, metadata × 2 files, maintainer→consumer switch touching
  `.engineering/tests/**`) all failed before the fix (`assert 0 == 1`: prepare
  accepted). `test_verification.py::test_out_of_scope_role_edit_is_ignored` adds
  `make engineering-check` for its in-scope `install.json`.
- Docs: verification guide (role sentence, table, update-output paragraph) and
  ENGINEERING.md. Follow-up [08](08-verified-starter-update-evidence.md) created.
- Gates after `make fmt` and one `make manifest` (metadata restored from
  `origin/main` first): `make check` exit 0; `make engineering-test` exit 0
  (394 passed); `make engineering-evals` exit 0 (11/11 static, 5 prompt cases
  skipped). Independent reverification not yet done.

### Behavioral review corrections (2026-09-28)

Implementation of human-authorized decisions 4–5 above; not verification,
human acceptance, publication or merge.

- Decision 4: `verification_requirements.validate_requirements` adds
  `make engineering-test` and `make engineering-evals` when the effective role is
  `maintainer` and installation metadata changed (still also requiring
  `make engineering-check`). Consumer requirements unchanged.
- Decision 5: a `TOMLDecodeError` from configuration validation is re-raised as
  `.engineering/config.toml: <parser message>`.
- Tests first: 4 new `verify prepare` cases (maintainer manifest dropping an
  entry and switching `tool.py` to `preserve`; maintainer `install.json`;
  unparseable consumer config × generated/adopted) failed before the fix
  (maintainer: `assert 0 == 1`, prepare accepted; TOML: error was
  `Invalid value (at line 1, column 18)`).
- Docs: verification guide table/wording and ENGINEERING.md. Ticket 06 gained the
  post-update `graft: MISSING` acceptance point and a note that ticket 05 already
  added the navigation guide and prerequisite split.
- Gates after `make fmt` and one `make manifest` (metadata restored from
  `origin/main` first): targeted tests 70 passed; `make check` exit 0;
  `make engineering-test` exit 0 (398 passed); `make engineering-evals` exit 0
  (11/11 static, 5 prompt cases skipped). Independent reverification not yet done.
