---
name: responsibility-driven-design
description: Align on what responsibilities already live where in a codebase, then decide where new or changed responsibilities belong — keeping existing roles, adding new ones, or moving things around. Produces a plan doc that captures the current map, the delta being added, and any refactor moves. Use when the user wants to design or redesign a feature by responsibilities, mentions "RDD", "responsibility-driven design", "where does this belong", "what owns this", "Wirfs-Brock", or wants to align on roles before TDD. **When to invoke:** after the team has agreed what to build but before writing the first test — RDD produces the design, TDD produces the code.
---

<what-to-do>

**Goal:** produce a design doc where every new responsibility has a named home before any code is written.

**Quick mode:** If you have one responsibility and just want a placement recommendation, skip the plan doc. Say `quick: [responsibility]` and get a recommendation with rationale in one turn.

The goal of this skill is to produce a **plan doc** with three things:

1. A map of responsibilities that already exist in the area (brownfield) or a sketch of what the system has to do (greenfield).
2. The new or changed responsibilities the user is adding.
3. For each item in (2), where it lives — existing role, new role, or "this triggers a move".

Stereotypes and collaboration graphs are *tools for breaking ties*, not phases you must walk through. Reach for them only when "where does this belong" stops being obvious.

**Phase 0 — Orient:**

1. Ask the user for **scope** in one sentence — what feature, area, or change are we designing. Then kick off an `Explore` subagent to detect codebase shape (greenfield vs brownfield, language/paradigm, existing domain docs like CONTEXT.md, ADRs, glossary) using that scope as context.
2. When both return, create the plan doc using [PLAN-FORMAT.md](./PLAN-FORMAT.md) at a path the user picks (default `docs/design/<short-name>.md`). Fill scope; leave the rest empty.
3. Announce the detected mode in one line: `Mode: brownfield (Python/Django, found CONTEXT.md + 2 ADRs). Correct?` Wait for confirm or correction. If the user flips it, switch mode before Phase 1.

**Phase 1 — Map what exists:**

*Brownfield:* have an `Explore` subagent recover the current responsibility map in the area — which modules/classes/functions currently own which behaviour and which state. Write it into the plan doc as the **Existing map**. Note any obvious leakage (a controller doing persistence, a value object making decisions) but don't fix it yet — you're cataloging, not redesigning.

*Greenfield:* skip the map. Instead, sketch the scenarios the system has to handle ("Walk me through the happy path. Now the cancel path. Now what if the system crashes mid-way."). Capture what the system needs to *do* and what it needs to *know* — but only enough to ground the next phase.

If a domain term comes up that should be in CONTEXT.md, flag it and keep moving.

After the map is written, surface a one-line win before moving on:

`Map complete: [N] roles identified[, M leakage candidates flagged]. Ready to name the delta?`

**Phase 2 — Name the delta:**

Ask: "What new responsibilities does this change introduce?" Get a list of concrete, verb-or-noun-sized items — not feature descriptions. Examples:
- "Decide whether a refund is allowed"
- "Remember the last sync timestamp"
- "Translate the webhook payload into a domain event"

Write each one into the **Delta** section of the plan doc as you go. One responsibility per line. If the user says something compound ("validate and persist the order"), split it.

A responsibility is compound if it contains "and" or names two verbs/nouns at different levels of decision. Split until each line is either one decision (doing) or one piece of state (knowing). One-liner test: could two different roles plausibly own the two halves? If yes, split.

Echo each captured item back as one line so the user sees the list growing without re-opening the doc:

`+ [4] "Remember last sync timestamp" (knowing)`

Format: `+ [#] "<responsibility>" (<kind>)`. Nothing else — no commentary, no re-asking.

**Phase 3 — Place each item:**

Before the first question, echo the captured count and **stop**:

`Delta: <N> items captured. Starting placement.`

Wait for the user's go-ahead (or their first answer) before producing item [1/N]. The Phase 2 list-dump is not license to batch Phase 3.

Then ask one question per Delta item, in this shape every time:

```
[#/total] "<responsibility>"
  → Recommend: <RoleName> (existing | new | move) — <one-line rationale>.
  OK / pick different role / triggers a move?
```

**One question per turn. Stop after asking.** Do not produce the next item's question, a future placement echo, or any commentary in the same turn. The user's answer is the trigger for the next question — there is no other trigger.

Same three lines, same order, every item. The user learns to answer in one beat. The three answer paths are:

- **Existing role** — the current module/class/function it joins. Fine if it fits the role's existing intent.
- **New role** — no current role is a good home. Name it and give a one-line description of its intent.
- **Move triggered** — the new responsibility exposes that something else is in the wrong place. Record the move as a refactor item.

Update the plan doc inline — never batch.

After each placement lands, echo one line so the user sees what was written and how far we are:

`✓ [3/7] "Translate webhook payload" → WebhookGateway (existing) — see Move M1`

Format: `✓ [done/total] "<responsibility>" → <placement> [— <note>]`. Use the Delta count for the total. This is the only feedback per item — don't summarize the doc, don't repeat the question.

**When the user defers an item** ("skip for now", "not sure yet"): move it to the **Open questions / decisions deferred** section of the plan doc with a one-line reason and continue. Don't loop on it.

**When placement is hard:** reach for [ROLE-STEREOTYPES.md](./ROLE-STEREOTYPES.md) as vocabulary ("this sounds like a Controller decision living inside an Information Holder — promote it or extract it"). Draw a directed-edge collaboration (`Caller → Callee: "reason"`) only when two placements are both plausible and the call pattern would settle it. Most items won't need either.

**Name-smell nudge.** When you're about to introduce a *new* role whose name contains `Rule`, `Policy`, `Validator`, `Check`, `Specification`, `Calculator`, `Formatter`, or `Resolver`, **default the recommendation to Service Provider** and say so out loud — e.g. `Recommend: MarketplaceRule (new, Service Provider — *Rule names default to SP per ROLE-STEREOTYPES.md)`. The user can still override. This catches the most common stereotype miss before it lands in the doc.

**Phase 4 — Stereotype audit:**

Before starting the audit, surface a one-line win:

`All [N] items placed. One quick audit, then you're done.`

After every Delta item has a placement, audit the **New roles** table before moving on. This is a forced re-read, not a vibe check.

1. Open [ROLE-STEREOTYPES.md](./ROLE-STEREOTYPES.md) and walk the **quick decision tree** at the bottom.
2. For each row in the New roles table, run the role through the tree and the smell list. Cite the rule that justifies the label (one short paraphrase or quote from the doc) in the row's Notes — or in a `**Audit:**` line under the table for compactness. Example: `Notes: SP per "Rule names default to Service Provider"`.
3. If a label changes, update it inline and announce: `↻ <Role>: <old> → <new> — <smell or rule cited>`.
4. If a label survives, say so: `✓ audit clean (10 roles)`.

Skip this phase only if no new roles were introduced. Don't skip it because the labels "look right" — the failure mode this catches is exactly the labels looking right from memory.

**Phase 5 — Stop at the design:**

When every Delta item has a placement and any triggered moves are recorded, write a short **Next: TDD entry points** section — the first 2–3 tests to write, usually targeting the role that owns the new use-case decision.

Do not start writing tests or production code in this session. Stop here and return the design doc.

**Ground rules:**

- One question at a time. The user's answer is the only trigger for the next question — never read ahead, never batch, never preview the next item.
- Always give your recommended answer with the question — make it easy to say "yes" or correct you.
- If a question can be answered by reading the code, read the code instead of asking.
- Update the plan doc inline AND echo a one-line confirmation of what was written. Never batch, never silent.
- Phases are a default, not a gate. If the user wants to skip ahead ("the map is obvious, just place these three new things"), do it. Phase 4 (stereotype audit) is the one exception: if any new roles were introduced, run it.
- Announce each phase transition with a one-line banner before the first question of that phase: `— Phase 2: name the delta —`. Use it as a heading, not a sentence. Skip the banner if the user explicitly skipped ahead.
- Stereotype labels are not free. Don't fill the stereotype column from memory — every label must cite a rule, a smell, or a decision-tree step from `ROLE-STEREOTYPES.md`. If you can't cite, leave it blank.

</what-to-do>

<supporting-info>

## Role stereotypes (optional vocabulary)

See [ROLE-STEREOTYPES.md](./ROLE-STEREOTYPES.md). Use these only when placement is genuinely ambiguous, or to articulate *why* something is in the wrong place when a move is triggered.

## Plan doc format

See [PLAN-FORMAT.md](./PLAN-FORMAT.md).

## Source

Roles, responsibilities, and the Doings/Knowings split come from Rebecca Wirfs-Brock's *Object Design: Roles, Responsibilities, and Collaborations* (2002). Treat as inspiration, not scripture — this skill narrows the workshop down to the placement decision.

</supporting-info>
