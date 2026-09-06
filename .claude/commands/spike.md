# /spike

Settle a **how** before it becomes a change. Use this when the *what* is roughly
clear but the approach is not — the shape of the state model, whether an
integration works the way the docs claim, which of three designs survives
contact with real data.

Usage:
- `/spike <slug> <question>` — start a spike, e.g.
  `/spike event-ordering can we keep ordering guarantees without a broker?`
- `/spike <slug>` — resume one already in progress

Three durable outputs, and only three:

| Artifact | Holds | Read by |
|---|---|---|
| `openspec/changes/<slug>/intent.md` | the *what* and why, as `/explore` would have written it | `/crystallize` |
| ADR in `docs/decisions/` | the decision and what lost | forever, by anyone |
| `openspec/changes/<slug>/design.md` | the approach, in enough detail to build from | `/crystallize`, then `/dev-change` |

A spike is the exploratory stage, so it hands over the same artifact `/explore`
does, plus the two the experiment earned. If `intent.md` already exists because
`/explore` ran first, extend its **Open questions** rather than rewriting it.

The ADR is *why*; `design.md` is *how*. A decision on its own does not survive
the trip to implementation — `design.md` is OpenSpec's own artifact for the
approach, and writing it here is what makes the spike's work reusable rather
than a paragraph someone has to re-derive.

Prototype code stays on the `spike/<slug>` branch and is never merged. Nothing
here writes `openspec/specs/`, `tasks.md`, a proposal, or a delta spec — a spike
answers *how*, and the change loop still owns *what*.

Use the same `<slug>` you intend to give the change: `design.md` lands in the
folder `/crystallize` will populate.

---

```bash
bash .harness/scripts/cmd_spike.sh $ARGUMENTS
```

After the preamble runs:

1. **Interview before you build.** Invoke the **`grilling`** skill and work the
   design tree in rounds. Most of what looks like a coding question is an
   undecided requirement, and an interview settles those far faster than a
   prototype does. Facts are yours to find; decisions are the user's.
2. Invoke **`domain-modeling`** alongside it. When a term settles, write it to
   `CONTEXT.md` there and then. When the user's word conflicts with the
   glossary, say so immediately — that conflict is usually the real question.
3. **Prototype only what the interview cannot settle.** For each question that
   genuinely needs running code, invoke the **`prototype`** skill. Throwaway
   from day one, no persistence, no tests, no abstractions; surface the state
   after every action so the user can see what changed. Commit prototypes to
   this branch — that is what the branch is for.
4. **Time-box it and say so.** State up front how long you expect to spend and
   what would make you stop. A spike that cannot answer its question is a
   result: record what you ruled out.
5. **Write or extend `intent.md`** to the shape in the `explore` skill's
   `INTENT-FORMAT.md`. A spike answers *how*, but the change still needs its
   *what* on record, and `/crystallize` reads the Classification line from here.
6. **Write the ADR** in `docs/decisions/`, following that directory's
   `index.md` convention, and add its index row in the same commit. Record what
   lost and why — the rejected option is what stops the question being reopened
   in six months. Name this branch, so the prototype stays findable.
7. **Write `openspec/changes/<slug>/design.md`.** This is the handover, and it
   is the artifact that decides whether the spike was worth running:

   - **Approach** — the shape that won, concrete enough to build from: the
     components, where the state lives, what talks to what.
   - **Tried and rejected** — each alternative, and the evidence that killed
     it. "Slower" is not evidence; a number or an observed failure is.
   - **Still unknown** — what the spike did not settle, and what would settle
     it. An honest gap here becomes an open question in `intent.md`; a hidden
     one becomes a task that dissolves in week three.
   - **Prototype** — `spike/<slug>`, and which commit demonstrates what.

8. **Stop at the gate.** Show the user all three files and wait. An unaccepted
   ADR is not a decision, and the change loop must not consume one.
9. Once accepted, move the documents onto a mergeable branch — the prototypes
   stay behind:

   ```bash
   git switch -c docs/<slug> main
   git checkout spike/<slug> -- docs/decisions openspec/changes/<slug>
   ```

   Then `/commit-push-pr`, and once that merges:

   ```
   /crystallize <slug>
   ```

   `/crystallize` finds `intent.md` and `design.md` already written, and builds
   the proposal, delta specs and tasks around them. Do not write any of those
   here.

**Leave `spike/<slug>` unmerged.** It is a primary source, not work in flight:
the decision reaches `main` as two reviewed documents, and the throwaway code
stays where it can be read but never runs in production. Delete the branch only
when the ADR that cites it is superseded.
