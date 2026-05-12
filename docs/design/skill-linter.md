# RDD: skill-linter

**Scope:** Add a linter that verifies every skill in the repo is (1) registered in `.claude-plugin/marketplace.json` and (2) mentioned in `README.md`. Out of scope: linting SKILL.md frontmatter shape, description quality, or anything beyond the two presence checks.
**Codebase:** brownfield (linter target) / greenfield (linter implementation)
**Paradigm:** TBD — likely a script invoked by a new skill, or a pure skill

## Existing map

| Location | Currently owns |
|---|---|
| `*/SKILL.md` | Knowing: each skill's identity (name in frontmatter) and its on-disk location (the directory it sits in) |
| `.claude-plugin/marketplace.json` | Knowing: which skill directories are registered under `plugins[].skills[]` |
| `README.md` | Knowing: human-facing index of the repo — currently only contains install instructions, no skill mentions |

Leakage / smells observed (catalog only, don't fix yet):
- `README.md` doesn't mention any skill today — the linter will fail on first run by design. That's the point.
- `bps-forge-skills/SKILL.md` exists as a skill directory but its role vs the marketplace `plugins[].name: "bps-forge-skills"` is ambiguous (same name, different concept).

## Delta — new or changed responsibilities

| # | Responsibility | Kind | Placement | Notes |
|---|---|---|---|---|
| 1 | Discover all skills on disk | doing | `SkillScanner` (new) | walk repo, find dirs containing `SKILL.md` |
| 2 | Read each skill's identity | doing | `SkillScanner` (new) | extract `name` from frontmatter in same pass |
| 3 | Read registered skill paths from `marketplace.json` | doing | `MarketplaceRegistry` (new) | parse JSON, flatten `plugins[].skills[]` |
| 4 | Read README text | doing | `ReadmeIndex` (new) | normalize whitespace/case for mention check |
| 5 | Decide whether a skill is registered in the marketplace | doing | `RegistrationCheck` (new) | path-in-set comparison |
| 6 | Decide whether a skill is mentioned in the README | doing | `MentionCheck` (new) | matching rule TBD — see open question |
| 7 | Report violations to the user | doing | `LintRunner` (new) | per-skill output + non-zero exit on any failure |
| 8 | Know which skills are exempt from either check | knowing | _deferred_ | YAGNI until first false positive |

## Moves triggered

_None._ The linter is greenfield; no responsibilities are moving out of an existing home.

## New roles introduced

| Role | Intent (one line) | Stereotype | Justification |
|---|---|---|---|
| `SkillScanner` | Walks the repo and yields each skill's path + frontmatter identity | Interfacer | Talks to the filesystem — decision tree step 1 |
| `MarketplaceRegistry` | Reads `marketplace.json` and exposes the set of registered skill paths | Interfacer | Reads a file from disk + translates JSON → domain set — decision tree step 1 |
| `ReadmeIndex` | Reads `README.md` and exposes its text for searching | Interfacer | Reads a file from disk — decision tree step 1 |
| `RegistrationCheck` | Given a skill path and the registered set, returns registered-or-not | Service Provider | Computes a verdict from inputs and stops; `*Check` name-smell default per §5 |
| `MentionCheck` | Given a skill name and README text, returns mentioned-or-not | Service Provider | Same as above — pure verdict, no orchestration |
| `LintRunner` | Drives the scan, runs both checks per skill, prints violations, sets exit code | Controller | Branches on policy ("does this skill pass?") and directs the flow + exit code — decision tree step 3. Rejected Coordinator: the runner is making the pass/fail call itself, not marching through a fixed choreography |

**Audit:** ran Phase 3.5 against ROLE-STEREOTYPES.md decision tree. All 6 labels survived. Name-smell catches landed before placement on `RegistrationCheck` and `MentionCheck` (both `*Check`), so no `↻` flips. ✓ audit clean (6 roles).

## Open questions / decisions deferred

- [ ] **Ship shape:** standalone script chosen for now — but where does it live? `scripts/lint.sh`, `scripts/lint-skills.py`, or a top-level `lint` entry point?
- [ ] **Language:** Bash + `jq`, or Python (stdlib `json` + `re`)? Python is portable and dependency-free; Bash is shorter. No CI config exists yet to constrain this.
- [ ] **What counts as "mentioned" in the README?** Exact directory name? Frontmatter `name:` value? Case-sensitive? Word-boundary match (so `tdd` doesn't false-positive on `tddx`) or substring? Pick a rule before writing test 3.
- [ ] **Exemption mechanism:** `.lintignore`, a list in `marketplace.json`, or skip entirely? Defer until the first real false positive.
- [ ] **Skill exclusions:** is `bps-forge-skills/` itself a real skill that needs to be in the README, or scaffolding? Its name collides with the plugin name in `marketplace.json` — treat it as a skill or exempt?

## Next: TDD entry points

Start tests at `LintRunner` — that's the role owning the use-case decision ("does this repo pass lint?"). The Interfacers and SPs can be stubbed with fixtures.

1. **`LintRunner.run` — all skills registered and mentioned** → exits 0, output indicates pass. Fixture: a temp repo with 2 skills, both in `marketplace.json`, both named in `README.md`.
2. **`LintRunner.run` — one skill missing from marketplace** → exits non-zero, output names the offending skill and which check failed.
3. **`LintRunner.run` — one skill missing from README** → exits non-zero, output names the offending skill and which check failed.

Once those three pass, the open questions on matching rules and ship shape will be concrete enough to close.

Stop here. Implementation is out of scope for this session.
