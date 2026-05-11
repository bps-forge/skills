# Plan Doc Format

Create this file at the start of the session. Fill in inline as decisions land — never batch.

```markdown
# RDD: <short name>

**Scope:** <one sentence — what's in, what's deliberately out>
**Codebase:** greenfield | brownfield
**Paradigm:** OO | functional | mixed

## Existing map
<brownfield only — subagent's recovered responsibility map; delete this section for greenfield>

| Location | Currently owns |
|---|---|
| `path/to/file.ext` | <responsibilities — doing and/or knowing> |
| ... | |

Leakage / smells observed (catalog only, don't fix yet):
- ...

## Scenarios in scope
<greenfield: required. brownfield: optional, only if it helps ground the delta>

- **Happy path:** <one-line walk-through>
- **<other path>:** ...

## Delta — new or changed responsibilities

| # | Responsibility | Kind | Placement | Notes |
|---|---|---|---|---|
| 1 | Decide whether a refund is allowed | doing | `RefundPolicy` (new role) | use-case decision |
| 2 | Remember last sync timestamp | knowing | `SyncState` (existing) | already fits |
| 3 | Translate webhook payload to domain event | doing | `WebhookGateway` (existing) | currently in `WebhookController` — see Move M1 |
| ... | | | | |

**Kind** is `doing` (verb) or `knowing` (noun/state).
**Placement** is one of: `<RoleName> (existing)`, `<RoleName> (new)`, or `see Move M#`.

## Moves triggered

Refactors exposed by placing the delta. Each is a responsibility leaving its current home.

| # | Responsibility | From | To | Reason |
|---|---|---|---|---|
| M1 | Translate webhook payload | `WebhookController` | `WebhookGateway` | translation belongs at the boundary, not in the controller |
| ... | | | | |

## New roles introduced

| Role | Intent (one line) | Stereotype | Justification |
|---|---|---|---|
| `RefundPolicy` | Decides if a refund is allowed given order + customer history | Controller | Directs other objects on the use-case outcome — not just returning a verdict (ROLE-STEREOTYPES.md §5) |
| ... | | | |

**Stereotype** is optional — leave blank if you didn't consult `ROLE-STEREOTYPES.md`. If filled, **Justification** is required: a short paraphrase or citation from the doc. "Looks like a Controller" is not a justification.

## Open questions / decisions deferred

- [ ] Should `RefundPolicy` consult `LoyaltyTier` directly, or receive it as input?
- [ ] ...

## Next: TDD entry points

Start tests at whatever owns the new use-case decision.

1. `RefundPolicy.evaluate` — happy path: eligible order → approved
2. `RefundPolicy.evaluate` — outside refund window → rejected with reason
3. ...

Stop here. Implementation is out of scope for this session.
```

## Notes on filling it in

- **Number Delta items and Moves** (1, 2, ...; M1, M2, ...). Numbers let placement and refactor references stay short.
- **One row per responsibility.** "Validate and persist the order" is two responsibilities — split them.
- **Stereotypes require justification.** The column is optional, but if you fill it you must cite a rule, smell, or decision-tree step from `ROLE-STEREOTYPES.md` in the Justification column. No citation, no label.
- **Name-smell defaults.** New roles named `*Rule`, `*Policy`, `*Validator`, `*Check`, `*Specification`, `*Calculator`, `*Formatter`, or `*Resolver` default to Service Provider unless they actually direct other objects.
- **Collaboration edges go in Notes**, not as a separate section. Only draw them when "where does this belong" was ambiguous and the call pattern settled it.
- **Open questions are valid output.** Not every decision has to resolve in one session.
