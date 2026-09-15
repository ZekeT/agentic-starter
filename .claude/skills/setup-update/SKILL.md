---
name: setup-update
description: Update a project from a local template using explicit ownership and installed upstream baselines.
disable-model-invocation: true
---

# Template update

Read `.harness/docs/installation.md` for the shared update contract and recovery.
Run from the template checkout with Python 3.12+:

```bash
python factory update /path/to/project
```

Review ADD/MERGE/PRESERVE/CONFLICT/SKIP actions and resolve every conflict before
applying. Preserve project instructions, canonical checks, CI, docs, application
requirements, environments and locks. Unknown legacy customizations are not
pristine evidence. Do not regenerate downstream baselines to make a conflict vanish.

```bash
python factory update /path/to/project --apply
```

Apply requires clean committed Git, revalidates inputs, runs offline doctor and
reports affected paths and a recovery commit. Treat write/postcheck failures as
failures. Prepare external OpenSpec/Graft dependencies explicitly; never run
upstream Graft init or copy its cache. Run the canonical project checks plus
`make factory-check`, explicit Graft freshness checks and applicable evals. Leave
changes uncommitted for human review.

The legacy `scripts/setup_update.py TARGET --dry` form remains a read-only adapter.
Default legacy invocation also plans; use `--apply` explicitly. `--force` is refused.
There is no second overwrite algorithm or unconditional version-stamp writer.
