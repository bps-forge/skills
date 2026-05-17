---
name: comprehension-check
description: Catch AI comprehension drift before the diff lands. After generating code with an AI, the author runs /comprehension-check on their latest diff. It asks three targeted questions — what the diff changes, why this approach won, and which line is most likely to break — and writes a report flagging lines the author could not explain. Mom Test rules apply: the questions ask what happened, not whether the author understands. Use when the user finishes an AI-generated diff and wants to verify they actually understand it before committing, mentions "comprehension drift", "/comprehension-check", "did I just commit something I don't understand", "AI drift", or wants to audit their own diff before push. **When to invoke:** after the AI produces a diff, before `git commit`.
---

<what-to-do>

**Goal:** make the author demonstrate understanding of their own AI-generated diff. Produce a `comprehension-report.md` that lists the lines they could not explain, with the question that surfaced them.

**Hard rules:**

- Three questions, in order. No more, no fewer.
- One question per turn. Stop after asking. The user's answer is the only trigger for the next question.
- Never ask "do you understand X?" — that is a vanity question. Ask what the diff does, what was considered, what would break.
- The flag rules below decide what goes in the report. The author's confidence does not. If the answer fails the flag rule, it gets flagged even if the author insists they understand.

**Phase 0 — Locate the diff:**

1. Run `git diff` (unstaged) first. If empty, fall back to `git diff --staged`. If still empty, fall back to `git diff main...HEAD` (or the repo's default branch).
2. If all three are empty, stop: `No diff found. Run this after the AI produces changes, before commit.`
3. If the diff is larger than ~400 lines, ask the user to narrow scope: a path, a commit range, or a single file. Drift detection on a 2000-line diff produces noise, not signal.
4. Echo a one-line orientation: `Diff scope: <N> lines across <M> files. Starting Q1.`

**Phase 1 — Q1: WHAT (behavior summary):**

Ask, verbatim:

> **Q1/3 — In one sentence, what does this diff change about how the system *behaves*?** Not what files it touches — what a user, caller, or downstream system will observe differently.

**Stop. Wait for the answer.**

Flag rule:
- ✅ Pass if the answer names an observable change (a user action, an API response, a downstream effect).
- 🚩 Flag the entire diff at the goal level if the answer only describes mechanics ("adds a function", "renames a variable", "refactors X for clarity") with no behavior tied to it.
- 🚩 Flag if the answer is "I don't know" or hedges ("I think it...").

Record the answer and the flag verdict in working memory. Do not write the report yet.

**Phase 2 — Q2: WHY (decision recall):**

Ask, verbatim:

> **Q2/3 — What did the AI choose NOT to do here, and why?** Name one alternative it considered, or one you would have considered, and the reason this approach won.

**Stop. Wait for the answer.**

Flag rule:
- ✅ Pass if the answer names a concrete alternative AND a concrete reason (tradeoff, constraint, library limit, perf, simplicity).
- 🚩 Flag if the answer is "I don't know" or "I didn't ask".
- 🚩 Flag if the alternative or reason sounds fabricated — vague phrasing like "it's cleaner" or "best practice" with no specifics. Probe once: `Can you point to where that tradeoff shows up in the diff?` If the probe doesn't land a concrete reference, flag it.

Record the answer and the flag verdict.

**Phase 3 — Q3: WHAT-BREAKS (line-level failure mode):**

Ask, verbatim:

> **Q3/3 — Point to the single line in this diff most likely to break in production.** Give the file path and line number, and name the input or condition that would make it fail.

**Stop. Wait for the answer.**

Flag rule:
- ✅ Pass if the answer cites a specific `file:line` AND names a specific failing input (null, empty, race, type, boundary, network failure, etc.).
- 🚩 Flag the cited line if the input is vague ("bad data", "edge cases").
- 🚩 Flag the diff at the line level (record "no line cited") if no file:line is given.
- 🚩 If the cited line doesn't exist in the diff, point that out and ask once for a real line. If they can't, flag it.

**Phase 4 — Write the report:**

Write `comprehension-report.md` at the repo root (or wherever the user invoked the skill). Use this format:

```markdown
# Comprehension Report — <YYYY-MM-DD HH:MM>

Diff scope: <N> lines across <M> files
Branch: <current branch>

## Q1 — WHAT
**Answer:** <author's answer, verbatim>
**Verdict:** ✅ pass | 🚩 flagged — <reason>

## Q2 — WHY
**Answer:** <author's answer, verbatim>
**Verdict:** ✅ pass | 🚩 flagged — <reason>

## Q3 — WHAT-BREAKS
**Cited line:** <file:line or "none cited">
**Failure mode:** <author's answer, verbatim>
**Verdict:** ✅ pass | 🚩 flagged — <reason>

## Flagged lines

- <file:line> — <one-line reason from Q3 flag, or "no line cited at Q3">
- (add Q1 entry as `<entire diff>` if Q1 was flagged at goal level)

## Recommendation

<one of:>
- All three answers passed. Diff is safe to commit on comprehension grounds.
- <N> answers flagged. Recommend: re-prompt the AI to explain the flagged areas, OR revert the flagged lines and rewrite manually, OR commit and document the gap in the PR description.
```

Then echo a one-line summary to the user:

`Report: comprehension-report.md (<N> flag(s)). <one-line recommendation>.`

**Phase 5 — Stop:**

Do not auto-commit. Do not auto-post to a PR. Do not loop on the flags. The report is the artifact; what to do with it is the author's call.

**If the user wants to re-run after fixing:** they re-invoke the skill. Reports are overwritten, not appended. The artifact is the *current* understanding of the *current* diff.

</what-to-do>

<supporting-info>

## Why these three questions

Each question targets a different layer of drift:

| Question | Layer | What it catches |
|---|---|---|
| Q1 WHAT | Goal-level | Author shipped without knowing the observable effect |
| Q2 WHY | Reasoning-level | Author took the first AI suggestion without engaging tradeoffs |
| Q3 WHAT-BREAKS | Line-level | Author can't predict failure modes — drives the flagged-lines output |

The three are orthogonal. Passing two and failing one tells you *where* the drift lives, which is more diagnostic than three variations of "explain this code."

## Mom Test compliance

The questions follow Mom Test rules: ask about the past, ask about specifics, never ask "do you understand" or "is this useful". The flag rules treat hedges and abstractions as failures because that's what they are — drift hides in vague answers.

## Scope decisions for v0

- **Free-text answers only.** Structured input (dropdowns, line pickers) is easier to score but trains the author to game the probe. Free-text is honest and noisy. Score the first 5 installs manually.
- **No PR integration.** The report is a local file. Posting to GitHub is a v1 feature; v0 is about whether the questions catch drift at all.
- **No author config.** Three fixed questions, fixed order. If you let users skip questions, the ones who need them most will skip them.

## Validation hook

This skill is a validation probe (see `PLAN.md` at repo root). The success metric is not adoption — it is whether 2 of the first 5 real installs produce an unprompted "this caught X for me" message within 7 days. If it doesn't, the design is wrong, and the questions are the first thing to revisit.

</supporting-info>
