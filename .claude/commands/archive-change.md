# /archive-change

Close the loop on a completed change: merge its delta specs into
`openspec/specs/` and archive the change folder.

This is the step that makes `openspec/specs/` a living statement of what the
system does rather than a snapshot that rots. It is **human-gated on purpose** —
a command, never a hook. `openspec/specs/` is the project's durable truth, and
nothing should mutate it as a side effect of a session ending.

Usage: `/archive-change <slug>`

---

```bash
bash .harness/scripts/cmd_archive_change.sh $ARGUMENTS
```

After the preamble runs:

1. **Show the user the spec diff and stop for confirmation.** Summarise what
   `openspec/specs/` will gain, lose, or change, and whether that matches the
   proposal's stated impact. A mismatch means either the proposal was wrong or
   the implementation drifted — say which, and do not archive until it's
   resolved.
2. On confirmation, archive via the OpenSpec CLI — never hand-merge the deltas:

   ```bash
   openspec archive <slug> --yes
   ```

   This merges the delta specs into `openspec/specs/` and moves the change to
   `openspec/changes/archive/YYYY-MM-DD-<slug>/`. For a change with no deltas,
   add `--skip-specs`.
3. Print the resulting diff so it lands in the transcript:

   ```bash
   git diff --stat openspec/specs/
   git diff openspec/specs/
   ```
4. **Product-truth check — ask once, not continuously.** In a single message:
   - Does this change alter `docs/product.md` (what the product is or isn't)?
   - Does it alter `docs/architecture.md` (containers, boundaries, constraints)?
   - Did implementation settle a durable decision that needs an ADR in
     `docs/decisions/`?

   Apply whatever the user confirms. If they say no to all three, move on — the
   spec diff is already the record.
5. Commit:

   ```bash
   git add openspec/ docs/
   git commit -m "chore(<slug>): archive change, merge deltas into specs"
   ```
6. Report: capabilities added/modified, the archive path, and any remaining
   active changes (`openspec list`).

## Constraints

- **Never edit `openspec/specs/` by hand**, here or anywhere. The CLI's merge is
  what keeps the archived change and the resulting spec consistent.
- Idempotent: re-running on an already-archived change exits 0 having done
  nothing.
- Refuses while any task is unchecked, and refuses if the change fails
  validation.
