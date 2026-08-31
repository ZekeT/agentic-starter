---
name: setup-update
description: >
  Update a project created from agentic-starter to the latest template version.
  Use when the starter has newer hooks, commands, skills, or docs than the
  project, or when the user says "update my project from the template",
  "pull template updates", "sync with the starter", or "my starter is newer".
  The companion script does the mechanical hash-compare work; this skill
  handles the guided merges for customized files.
---

# Template Update Skill

Brings a project copied from agentic-starter up to the latest template.
The script (`scripts/setup_update.py`) does everything deterministic;
this skill handles the judgment calls: merging template changes into files
the user has customized.

**How staleness is computed:** the starter ships `template-manifest.json`
(regenerated with `make manifest`) holding the sha256 of every
template-owned file — current version plus historical hashes. A target file
matching an old hash is a pristine copy of an older release (safe to
overwrite); a file matching no known hash was customized (never touched
by the script — flagged for you to merge).

---

## Step 1 — Dry-run the script

Run from the starter checkout against the target project:

```bash
python /path/to/agentic-starter/.claude/skills/setup-update/scripts/setup_update.py /path/to/target --dry
```

Read the report:
- **NEW** — file will be copied (didn't exist in target)
- **AUTO-UPDATE** — pristine older version, will be overwritten
- **CUSTOMIZED** — user-modified, script will NOT touch it; you merge in Step 3
- **up to date** — nothing to do

If the report looks wrong (e.g. a file you know is pristine shows as
CUSTOMIZED), the manifest may predate that file's last template change —
regenerate it in the starter with `make manifest` and re-run.

---

## Step 2 — Apply the mechanical update

```bash
python /path/to/agentic-starter/.claude/skills/setup-update/scripts/setup_update.py /path/to/target
```

This copies NEW and AUTO-UPDATE files, appends missing `.gitignore` lines
(never overwrites it), and stamps `.claude/template-version.json` in the
target so future updates know the baseline.

---

## Step 3 — Guided merge for CUSTOMIZED files (judgment required)

For each flagged file, apply the **template delta**, not the template file:

1. Get the old template version of the file (starter git history — the
   commit tagged with the target's previous version, or the last commit
   where its hash matched the manifest's `previous` entry):
   `git -C /path/to/agentic-starter log --oneline -- <file>`
2. Diff old-template → new-template. That delta is what the update adds.
3. Apply only that delta to the target's customized file — append or
   insert; **never replace the user's content**.
4. If the delta and the user's customization touch the same lines, show
   the user both versions and ask which wins.

**File-specific guidance:**

- **CLAUDE.md** — merge section by section. New template sections get
  appended; changed template sections get updated only if the user never
  edited them. The user's Rules section always wins.
- **docs/product.md, docs/architecture.md** — if these hold real project
  content (planning output), skip them entirely; template changes only matter
  for the placeholder versions.
- **pyproject.toml** — merge missing `[tool.*]` sections only; never touch
  `[project]` or dependencies.
- **.claude/settings.json** — merge new hook entries into the existing
  arrays; preserve the user's own hooks and permissions.
- **Hooks/commands/scripts (.py/.md)** — if the user's edit and the
  template's change conflict, prefer showing a diff and asking.

---

## Step 4 — Update what is never copied

Inside Claude Code (global, once per machine):

```
/plugin update superpowers@superpowers-marketplace
```

---

## Step 5 — Verify

1. `make check` in the target must pass.
2. `bash harness_setup.sh --check` in the target — it asserts the
   post-update structure, hook wiring, and manifest without mutating anything.
3. Tell the user what was auto-updated, what you merged, and anything
   you skipped with the reason.

---

## Guardrails

- **Never overwrite a CUSTOMIZED file** — the script won't; neither should you.
- **Apply deltas, not whole files** in guided merges.
- **Ask on conflicts** — when template delta and user edit collide, the user decides.
- **Maintainers:** after changing template-owned files in the starter, bump
  `TEMPLATE_VERSION` and run `make manifest` — otherwise downstream updates
  will misclassify pristine files as customized.
