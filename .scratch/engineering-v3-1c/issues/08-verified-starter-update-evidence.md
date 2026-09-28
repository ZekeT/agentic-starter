# 08: Verify consumer starter-update output against its source

**Spec:** Follow-up from the ticket 03 security review (2026-09-27); not part of the [spec](../spec.md) slices.

**What to build:** A consumer pull request that applies `./engineering update`
output becomes verifiable. Today ticket 03 rejects every consumer change to a
`file`-mode managed path, because the proposed `.engineering/manifest.json` is
consumer-controlled and cannot vouch for the bytes it describes. Accept such a
change only when the verification plan names the starter source checkout as an
explicit input and the proposed bytes (and removals) match that source's
manifest, not the proposed one.

**Blocked by:** 03 (merged), 10 (Make generation and update agree on the distributed file set).

**Status:** ready-for-agent

## Design question

What identifies a trustworthy starter source: a local checkout path, a pinned
commit or tag of the starter repository, or a signed/released manifest? How is
it fingerprinted in the plan so reviewers see which source vouched for the
update, and how does a stale or altered source fail closed?

## Decisions (triage 2026-09-28, human-approved)

- **Source of truth:** a pinned starter commit or tag named in the plan, fetched
  and compared — not a local checkout path (trusts whatever is on disk) and not a
  signed release manifest (no release signing exists yet). The pinned source is
  fingerprinted in the evidence so reviewers see which source vouched for the
  update; an unreachable, moved or altered source fails closed (INCOMPLETE).
- **Split:** the generation-versus-update distributed file-set mismatch moved to
  ticket 10, which blocks this ticket.
- **Priority:** after slice B (review tiers), ticket 06 and ticket 09.

## Acceptance ideas

- [ ] The plan names a pinned starter commit or tag as the update source; without it, a managed-file change stays rejected (INCOMPLETE).
- [ ] Proposed managed bytes and removals are compared against the source's manifest and distribution, never the proposed manifest.
- [ ] A forged proposed manifest digest or a dropped entry is still rejected.
- [ ] An update PR produced by `./engineering update --apply` from that source prepares a valid plan requiring `make check` and `make engineering-check`.
- [ ] Documentation replaces "consumer starter-update PRs are not yet verifiable" with the supported route.
