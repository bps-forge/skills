default:
    @just --list

# Lint that every skill is registered in marketplace.json and mentioned in README.md
lint:
    python3 scripts/lint_skills.py

# Run the linter's test suite
test:
    cd scripts && python3 -m unittest test_lint_skills.py -v
