"""Lint that every skill is registered in marketplace.json and mentioned in README.md.

Roles (per docs/design/skill-linter.md):

  Interfacers       SkillScanner, MarketplaceRegistry, ReadmeIndex
  Service Providers RegistrationCheck, MentionCheck
  Controller        LintRunner
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, TextIO


@dataclass(frozen=True)
class Skill:
    path: Path
    name: str

    @property
    def dir_name(self) -> str:
        return self.path.name


class SkillScanner:
    """Walks the repo and yields each skill's path + frontmatter identity."""

    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root

    def scan(self) -> list[Skill]:
        skills: list[Skill] = []
        for skill_md in self._repo_root.glob("*/SKILL.md"):
            name = self._read_frontmatter_name(skill_md)
            if name is not None:
                skills.append(Skill(path=skill_md.parent, name=name))
        return sorted(skills, key=lambda s: s.dir_name)

    @staticmethod
    def _read_frontmatter_name(skill_md: Path) -> str | None:
        text = skill_md.read_text()
        if not text.startswith("---"):
            return None
        end = text.find("\n---", 3)
        if end == -1:
            return None
        for line in text[3:end].splitlines():
            m = re.match(r"\s*name:\s*(\S+)", line)
            if m:
                return m.group(1)
        return None


class MarketplaceRegistry:
    """Reads marketplace.json and exposes the set of registered skill directory names."""

    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root

    def registered_dirs(self) -> set[str]:
        data = json.loads(
            (self._repo_root / ".claude-plugin" / "marketplace.json").read_text()
        )
        dirs: set[str] = set()
        for plugin in data.get("plugins", []):
            for entry in plugin.get("skills", []):
                dirs.add(Path(entry).name)
        return dirs


class ReadmeIndex:
    """Reads README.md and exposes its text for searching."""

    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root

    def text(self) -> str:
        return (self._repo_root / "README.md").read_text()


class RegistrationCheck:
    """Given a skill and the registered set, returns registered-or-not."""

    def __init__(self, registered_dirs: set[str]) -> None:
        self._registered = registered_dirs

    def is_registered(self, skill: Skill) -> bool:
        return skill.dir_name in self._registered


class MentionCheck:
    """Given a skill name and README text, returns mentioned-or-not (word-boundary, case-sensitive)."""

    def __init__(self, readme_text: str) -> None:
        self._readme = readme_text

    def is_mentioned(self, skill: Skill) -> bool:
        return re.search(rf"\b{re.escape(skill.name)}\b", self._readme) is not None


class LintRunner:
    """Drives the scan, runs both checks per skill, prints violations, decides exit code."""

    def __init__(
        self,
        scanner: SkillScanner,
        registration: RegistrationCheck,
        mention: MentionCheck,
        out: TextIO,
    ) -> None:
        self._scanner = scanner
        self._registration = registration
        self._mention = mention
        self._out = out

    def run(self) -> int:
        violations = list(self._violations())
        for v in violations:
            print(v, file=self._out)
        return 1 if violations else 0

    def _violations(self) -> Iterator[str]:
        for skill in self._scanner.scan():
            if not self._registration.is_registered(skill):
                yield f"{skill.dir_name}: not registered in marketplace.json"
            if not self._mention.is_mentioned(skill):
                yield f"{skill.dir_name}: not mentioned in README.md"


def main(repo_root: Path, out: TextIO = sys.stdout) -> int:
    scanner = SkillScanner(repo_root)
    registration = RegistrationCheck(MarketplaceRegistry(repo_root).registered_dirs())
    mention = MentionCheck(ReadmeIndex(repo_root).text())
    return LintRunner(scanner, registration, mention, out).run()


if __name__ == "__main__":
    sys.exit(main(Path(__file__).resolve().parent.parent))
