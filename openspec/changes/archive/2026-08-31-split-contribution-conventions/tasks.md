## 1. Record the sharpened rule

- [x] 1.1 Write `docs/decisions/0002-capability-granularity.md` superseding
      ADR-0001's heuristic, citing `contribution-conventions` as the case that
      exposed it; mark ADR-0001 superseded on that point and update the index
- [x] 1.2 Add the three granularity tests to the `crystallize` skill's
      classification step; verify the skill still parses and stays under ~120 lines

## 2. Apply the split

- [x] 2.1 Archive the change and verify `openspec list --specs` shows
      `test-organisation` and `change-submission` with the requirement counts
      2 and 2, and that requirement text is byte-identical to the original
- [x] 2.2 Resolve whatever `contribution-conventions` becomes once all its
      requirements are REMOVED, and record the observed behaviour in the ADR
- [x] 2.3 Repoint every reference to the old capability path; verify
      `make check` and `make evals` pass
