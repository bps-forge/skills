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

    def register(self, skill_dir: str) -> None:
        path = self._repo_root / ".claude-plugin" / "marketplace.json"
        data = json.loads(path.read_text())
        if data.get("plugins"):
            data["plugins"][0].setdefault("skills", []).append(f"./{skill_dir}")
        path.write_text(json.dumps(data))


class ReadmeIndex:
    """Reads README.md and exposes its text for searching."""

    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root

    def text(self) -> str:
        return (self._repo_root / "README.md").read_text()

    def add_mention(self, skill_name: str) -> None:
        path = self._repo_root / "README.md"
        content = path.read_text()
        if "## Skills" in content:
            content = content.rstrip("\n") + f"\n- {skill_name}\n"
        else:
            content = content.rstrip("\n") + f"\n\n## Skills\n\n- {skill_name}\n"
        path.write_text(content)


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
        fix_mode: bool = False,
        registry: MarketplaceRegistry | None = None,
        readme_index: ReadmeIndex | None = None,
    ) -> None:
        self._scanner = scanner
        self._registration = registration
        self._mention = mention
        self._out = out
        self._fix_mode = fix_mode
        self._registry = registry
        self._readme_index = readme_index

    def run(self) -> int:
        violations = list(self._violations())
        for v in violations:
            print(v, file=self._out)
        return 1 if violations else 0

    def _violations(self) -> Iterator[str]:
        for skill in self._scanner.scan():
            if not self._registration.is_registered(skill):
                if self._fix_mode and self._registry:
                    self._registry.register(skill.dir_name)
                else:
                    yield f"{skill.dir_name}: not registered in marketplace.json"
            if not self._mention.is_mentioned(skill):
                if self._fix_mode and self._readme_index:
                    self._readme_index.add_mention(skill.name)
                else:
                    yield f"{skill.dir_name}: not mentioned in README.md"


def main(repo_root: Path, out: TextIO = sys.stdout, fix: bool = False) -> int:
    scanner = SkillScanner(repo_root)
    registry = MarketplaceRegistry(repo_root)
    readme_index = ReadmeIndex(repo_root)
    registration = RegistrationCheck(registry.registered_dirs())
    mention = MentionCheck(readme_index.text())
    return LintRunner(
        scanner, registration, mention, out,
        fix_mode=fix, registry=registry, readme_index=readme_index,
    ).run()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Lint skill registration and README mentions.")
    parser.add_argument("--fix", action="store_true", help="Auto-fix violations instead of reporting them.")
    args = parser.parse_args()
    sys.exit(main(Path(__file__).resolve().parent.parent, fix=args.fix))
