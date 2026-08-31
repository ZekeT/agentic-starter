## Why
Eval suites rot silently: a case that never fails looks healthy but may just be
asserting something no longer reachable. Without a stated cadence, nobody prunes.

## What Changes
- States the eval review cadence and the deletion criterion.
- Not architecture-affecting.

## Capabilities

### New Capabilities
- `harness-evals`: how the harness regression-tests its own agent configuration

### Modified Capabilities

## Impact
Documentation only. No code, no dependencies.
