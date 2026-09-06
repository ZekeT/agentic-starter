# Output Formats

The document shapes `rescan-docs` writes. Loaded only when it reaches the
step that writes one — the skill itself carries the method, not the boilerplate.

## `docs/product.md`

```markdown
# Product
> Reverse-engineered from the codebase on {date}. Review and edit before treating as authoritative.

## Problem Statement
{what problem this system solves — from user interview}

## Target Users
{who uses it and how — from user interview + UX surfaces identified in Step 1}

## Current Functionality (implemented)
{bullet list of features that exist in the code — be specific, name endpoints/commands/modules}

## Planned Functionality (not yet implemented)
{bullet list from user interview answer 3 + any TODOs/FIXMEs found in code}

## Success Metrics
{how success is measured — ask if not obvious from code}

## Constraints
{tech constraints from code: language runtime, deployment target, external APIs required}

## Out of Scope
{what this system explicitly does NOT do — infer from missing obvious features}
```

## `docs/architecture.md`

```markdown
# Architecture Document
> Reverse-engineered from codebase on {date}. Review and edit before treating as authoritative.

## System Overview
{2-3 sentence summary of what this system is}

## Tech Stack
| Layer | Technology |
|-------|------------|
| Language | {e.g. Python 3.11} |
| Framework | {e.g. FastAPI, Django, Flask, none} |
| Database | {e.g. PostgreSQL via SQLAlchemy, none} |
| Test runner | {e.g. pytest, jest, go test} |
| Build/package | {e.g. uv + pyproject.toml, npm, cargo} |
| Deployment | {inferred from Dockerfile / fly.toml / render.yaml / Procfile} |

## Component Map
{List top-level modules/packages with one-line description each.
Derive from graphify community clusters or directory listing.}

## Data Flow
{Describe how data enters the system, is processed, and exits.
Identify: inputs → processing → outputs → storage.}

## External Integrations
{List every third-party API, SDK, or service the code calls.}

## Security Boundaries
{Where does untrusted input enter? Where is auth enforced?
Infer from middleware, decorators, env var usage.}

## Known Technical Debt
{From user interview answer 4 + grep for TODO/FIXME/HACK.}

## Open Architecture Questions
{Decisions that aren't clear from the code — flag these for the human to answer.}
```

## `openspec/specs/<capability>/spec.md`

```markdown
# <capability> Specification

## Purpose
One or two sentences (50+ chars) on what this capability is for.

## Requirements

### Requirement: <name>
The system SHALL <observable behaviour>.

#### Scenario: <name>
- **WHEN** <condition>
- **THEN** <expected outcome>
```
