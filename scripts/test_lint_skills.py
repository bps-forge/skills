import io
import json
import tempfile
import unittest
from pathlib import Path

from lint_skills import main


def write_skill(repo: Path, dir_name: str, frontmatter_name: str) -> None:
    skill_dir = repo / dir_name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {frontmatter_name}\ndescription: test skill\n---\n\nbody\n"
    )


def write_marketplace(repo: Path, skill_paths: list[str]) -> None:
    (repo / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (repo / ".claude-plugin" / "marketplace.json").write_text(
        json.dumps(
            {
                "name": "test",
                "plugins": [{"name": "p", "source": "./", "skills": skill_paths}],
            }
        )
    )


def write_readme(repo: Path, body: str) -> None:
    (repo / "README.md").write_text(body)


class LintRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_passes_when_all_skills_registered_and_mentioned(self) -> None:
        write_skill(self.repo, "alpha", "alpha")
        write_skill(self.repo, "beta", "beta")
        write_marketplace(self.repo, ["./alpha", "./beta"])
        write_readme(self.repo, "Skills: alpha and beta.\n")

        out = io.StringIO()
        exit_code = main(self.repo, out=out)

        self.assertEqual(exit_code, 0)
        self.assertEqual(out.getvalue(), "")

    def test_fails_when_skill_missing_from_marketplace(self) -> None:
        write_skill(self.repo, "alpha", "alpha")
        write_skill(self.repo, "beta", "beta")
        write_marketplace(self.repo, ["./alpha"])  # beta not registered
        write_readme(self.repo, "Skills: alpha and beta.\n")

        out = io.StringIO()
        exit_code = main(self.repo, out=out)

        self.assertEqual(exit_code, 1)
        self.assertIn("beta: not registered in marketplace.json", out.getvalue())
        self.assertNotIn("alpha:", out.getvalue())

    def test_fails_when_skill_missing_from_readme(self) -> None:
        write_skill(self.repo, "alpha", "alpha")
        write_skill(self.repo, "beta", "beta")
        write_marketplace(self.repo, ["./alpha", "./beta"])
        # README mentions "alpha" and a substring collision "betax" but not "beta" as a whole word
        write_readme(self.repo, "Skills: alpha and betax.\n")

        out = io.StringIO()
        exit_code = main(self.repo, out=out)

        self.assertEqual(exit_code, 1)
        self.assertIn("beta: not mentioned in README.md", out.getvalue())
        self.assertNotIn("alpha:", out.getvalue())


class FixModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_fix_adds_missing_mention_to_readme(self) -> None:
        write_skill(self.repo, "alpha", "alpha")
        write_marketplace(self.repo, ["./alpha"])
        write_readme(self.repo, "# skills\n\nInstall instructions.\n")

        exit_code = main(self.repo, out=io.StringIO(), fix=True)

        self.assertEqual(exit_code, 0)
        readme = (self.repo / "README.md").read_text()
        self.assertIn("## Skills", readme)
        self.assertIn("alpha", readme)

    def test_fix_mode_clean_repo_exits_zero(self) -> None:
        write_skill(self.repo, "alpha", "alpha")
        write_marketplace(self.repo, ["./alpha"])
        write_readme(self.repo, "Skills: alpha.\n")

        out = io.StringIO()
        exit_code = main(self.repo, out=out, fix=True)

        self.assertEqual(exit_code, 0)
        self.assertEqual(out.getvalue(), "")

    def test_fix_registers_unregistered_skill(self) -> None:
        write_skill(self.repo, "alpha", "alpha")
        write_marketplace(self.repo, [])  # alpha not registered
        write_readme(self.repo, "Skills: alpha.\n")

        exit_code = main(self.repo, out=io.StringIO(), fix=True)

        self.assertEqual(exit_code, 0)
        data = json.loads(
            (self.repo / ".claude-plugin" / "marketplace.json").read_text()
        )
        registered = {Path(e).name for p in data["plugins"] for e in p["skills"]}
        self.assertIn("alpha", registered)


if __name__ == "__main__":
    unittest.main()
