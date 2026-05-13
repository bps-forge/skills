# RDD: linter-update

**Scope:** Update the existing skill linter (`scripts/lint_skills.py`) — exact changes TBD in Phase 2.
**Codebase:** brownfield (Python/stdlib, linter already implemented)
**Paradigm:** OO — Interfacers, Service Providers, Controller (per original RDD)

## Existing map

| Location | Currently owns |
|---|---|
| `Skill` (dataclass) | Knowing: skill path + frontmatter name; exposes `dir_name` |
| `SkillScanner` | Doing: walks repo, finds `*/SKILL.md`, reads frontmatter `name` |
| `MarketplaceRegistry` | Doing: reads `.claude-plugin/marketplace.json`, returns set of registered dir names |
| `ReadmeIndex` | Doing: reads `README.md`, returns raw text |
| `RegistrationCheck` | Doing: decides whether a skill's dir name is in the registered set |
| `MentionCheck` | Doing: decides whether a skill's name appears in README text (word-boundary, case-sensitive regex) |
| `LintRunner` | Doing: orchestrates scan + both checks per skill, prints violations, returns exit code |
| `main()` | Doing: wires dependencies, calls `LintRunner.run()` |

Leakage / smells observed (catalog only):
- None. Clean separation: Interfacers read, SPs decide, Controller orchestrates.

## Delta — new or changed responsibilities

| # | Responsibility | Kind | Placement | Notes |
|---|---|---|---|---|
| 1 | Parse `--fix` flag from CLI args | doing | `main()` (existing) | |
| 2 | Add a skill dir name into `marketplace.json` | doing | `MarketplaceRegistry` (existing) | |
| 3 | Add a skill name into `README.md` | doing | `ReadmeIndex` (existing) | |
| 4 | Decide whether to fix or report a violation | doing | `LintRunner` (existing) | |

## Moves triggered

_None yet._

## New roles introduced

| Role | Intent (one line) | Stereotype | Justification |
|---|---|---|---|

## Open questions / decisions deferred

## Next: TDD entry points

Start tests at `LintRunner` — it owns the fix-or-report decision.

1. **`LintRunner.run` — fix mode, skill not registered** → adds skill dir to `marketplace.json`, exits 0.
2. **`LintRunner.run` — fix mode, skill not mentioned** → adds skill name to `README.md`, exits 0.
3. **`LintRunner.run` — fix mode, violation fixed then re-run** → subsequent run exits 0 with no violations.

Stop here. Implementation is out of scope for this session.
