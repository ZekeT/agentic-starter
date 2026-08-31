# change-submission Specification

## Purpose
Defines how a change is committed and proposed for review, so a reviewer can
check what was verified without asking the author what they ran.

## Requirements

### Requirement: Pull requests state how the change was verified
Every pull request SHALL state how the change was tested, covering automated
tests and any manual verification. Where a change was verified manually, the PR
SHALL record the steps taken and the observed result, not merely assert that
checking occurred.

#### Scenario: A change with no automated test
- **WHEN** a change cannot be covered by an automated test
- **THEN** the PR states why, and records the manual steps and their result

#### Scenario: Reviewer checks the compliance pass
- **WHEN** a reviewer runs `REVIEW.md`'s Pass 4
- **THEN** the PR body already names which tests cover the new behaviour

### Requirement: Commits follow Conventional Commits
Commit subjects SHALL follow `type(scope): description` in the imperative mood.
The body SHALL explain why the change was made where that is not obvious from
the diff.

#### Scenario: A commit that only restates the diff
- **WHEN** a commit body describes what changed rather than why
- **THEN** it is incomplete: the diff already shows what changed
