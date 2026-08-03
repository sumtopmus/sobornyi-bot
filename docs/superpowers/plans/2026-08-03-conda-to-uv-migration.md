# Conda to uv Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace conda with uv as the project's package and interpreter manager, consolidate five config files into one `pyproject.toml`, and bring every dependency to its current release without regressing the test suite.

**Architecture:** Three inviolable phases. Phase 1 moves tooling with dependency versions frozen at today's exact pins. Phase 2 changes versions with tooling already proven. Phase 3 applies the formatter reformat alone. No phase mixes two kinds of change, so any failure is attributable to exactly one cause.

**Tech Stack:** uv 0.11.18, Python 3.13, pytest, pre-commit, GNU Make.

## Global Constraints

- **Baseline, non-negotiable:** every task ends with `uv run pytest` reporting **350 passed, 2 skipped**. This was measured on `develop` before any change. A different count is a regression, including a *higher* pass count (it means collection changed).
- **Branch:** all work happens on `refactor/uv-migration`. Never commit to `develop` or `main`.
- **Phase boundaries are inviolable.** Never change tooling and dependency versions in the same commit. Within a phase, each task commits separately — this refines the spec's "three commits" to "three phases" for bisectability; the attributability property the spec requires is fully preserved.
- **Do not delete the conda environment** named `sobornyi-bot` at any point in this plan. It is the rollback path and is removed only after production is verified, outside this plan.
- **Do not modify any file under `src/`** in Phase 1 or Phase 2. Phase 3 modifies `src/` for formatting only.
- **Python:** `requires-python = ">=3.13,<3.14"`, `.python-version` contains `3.13`.
- **Never commit machine-local paths** (`/Users/...`, umbrella directory names, `worktrees/` prefixes) into any tracked file. All paths in committed content are relative to the repository root.
- Every `python`, `pytest`, `ptw`, and `pre-commit` invocation in tracked files must be prefixed with `uv run`.

**Reference:** the approved spec is `docs/superpowers/specs/2026-08-03-conda-to-uv-migration-design.md`.

---

## File Structure

| File | Responsibility | Phase |
|---|---|---|
| `pyproject.toml` | **New.** Single source of truth: project metadata and version, runtime deps, dev dep group, uv settings, pytest config, coverage config, black config, isort config. | 1 creates, 2 modifies |
| `uv.lock` | **New, committed.** Exact resolved versions with hashes. Generated, never hand-edited. | 1 creates, 2 regenerates |
| `.python-version` | **New, committed.** Interpreter pin uv reads to provision CPython. | 1 |
| `.gitignore` | **Modified.** Must stop ignoring `.python-version`. | 1 |
| `pytest.ini` | **Deleted.** Contents move to `[tool.pytest.ini_options]`. | 1 |
| `.coveragerc` | **Deleted.** Contents move to `[tool.coverage.*]`. | 1 |
| `environment.yaml` | **Deleted.** Conda environment definition. | 1 |
| `requirements.txt` | **Deleted.** Contents move to `[project.dependencies]`. | 1 |
| `requirements-dev.txt` | **Deleted.** Contents move to `[dependency-groups] dev`. | 1 |
| `Makefile` | **Modified.** Developer interface. Conda targets removed, `uv run` added, `lock` target added, `VERSION` derived from `pyproject.toml`. | 1 |
| `.pre-commit-config.yaml` | **Modified.** Dead hook removed, pytest hook rewired, lock-drift guard added. Formatter revs bumped in Phase 3. | 1, then 3 |
| `README.md` | **Modified.** Setup instructions and Makefile reference table. | 1 |
| `CLAUDE.md` | **Modified.** Agent-facing command list and worktree note. | 1 |

Ordering rationale: `pytest.ini` and `.coveragerc` must be deleted in the *same* task that adds their `pyproject.toml` equivalents. Both files take precedence over `pyproject.toml` in their respective tools, so leaving them in place would make the new config inert and the verification meaningless.

---

## Phase 1 — Tooling migration at frozen versions

### Task 1: pyproject.toml, interpreter pin, and config consolidation

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Modify: `.gitignore` (remove the `.python-version` entry and its `# pyenv` heading)
- Delete: `pytest.ini`
- Delete: `.coveragerc`
- Generated: `uv.lock`

**Interfaces:**
- Consumes: nothing. First task.
- Produces: `pyproject.toml` with a `[dependency-groups]` table named `dev` (Task 2's `uv sync` relies on this name), `[project].version = "1.1.0"` (Task 2's `uv version --short` reads this), and `[tool.uv] package = false`.

- [ ] **Step 1: Confirm the baseline before changing anything**

```bash
"${CONDA_EXE:-conda}" run -n sobornyi-bot python -m pytest -q --no-header -p no:cacheprovider 2>&1 | tail -3
```

Expected: `350 passed, 2 skipped`. If this does not match, stop — the baseline is wrong and every later gate is invalid.

- [ ] **Step 2: Fix `.gitignore`**

Delete these two lines (currently at lines 103-104):

```
# pyenv
.python-version
```

This is load-bearing. Without it `.python-version` is silently never committed, and a fresh clone or the production host resolves to an arbitrary Python.

- [ ] **Step 3: Verify the ignore rule is actually gone**

```bash
touch .python-version && git check-ignore -v .python-version; echo "exit=$?"
```

Expected: no output and `exit=1` (meaning *not* ignored). If it prints a `.gitignore:` line, the wrong line was deleted.

- [ ] **Step 4: Write `.python-version`**

```bash
echo "3.13" > .python-version
```

- [ ] **Step 5: Create `pyproject.toml` with today's exact pins**

Versions here are deliberately identical to the current `requirements.txt` and `requirements-dev.txt`. Do not modernise them in this phase.

```toml
[project]
name = "sobornyi-bot"
version = "1.1.0"
description = "Telegram bot to control the Sobornyi group"
readme = "README.md"
requires-python = ">=3.13,<3.14"
dependencies = [
    "dynaconf==3.2.10",
    "python-telegram-bot[callback-data,job-queue]==22.0",
]

[dependency-groups]
dev = [
    "black==25.1.0",
    "isort==6.0.1",
    "pre-commit==4.1.0",
    "pyright==1.1.408",
    "pytest==8.3.4",
    "pytest-asyncio==0.23.5",
    "pytest-cov==4.1.0",
    "pytest-env==1.1.5",
    "pytest-testmon==2.1.3",
    "pytest-watcher==0.6.3",
]

[tool.uv]
package = false

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
python_classes = ["Test*"]
addopts = "-v"
markers = [
    "asyncio: marks a test as an asyncio coroutine",
    "integration: marks a test as an integration test (deselect with '-m \"not integration\"')",
]
env = ["DYNACONF_ENV=dev"]
asyncio_mode = "auto"
filterwarnings = ["ignore::telegram.warnings.PTBUserWarning"]

[tool.coverage.run]
source = ["src"]
omit = [
    "*/site-packages/*",
    "*/dist-packages/*",
    "*/tests/*",
    "*/__pycache__/*",
    "*/.pytest_cache/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "pass",
    "raise ImportError",
    "except ImportError",
    "raise AssertionError",
]

[tool.black]
target-version = ["py313"]

[tool.isort]
profile = "black"
```

`package = false` is required: `src/` is not an installable package and there is no build backend. Without it uv looks for one and fails.

The `asyncio` marker is carried over verbatim even though pytest-asyncio registers it itself. Removing redundancy is a Phase 2 concern; Phase 1 is a faithful port.

- [ ] **Step 6: Delete the superseded config files**

```bash
git rm -q pytest.ini .coveragerc
```

Both take precedence over `pyproject.toml` in their tools. They must go now or Step 8 proves nothing.

- [ ] **Step 7: Create the environment and lockfile**

```bash
uv sync
```

Expected: `Creating virtual environment at: .venv`, then resolved/installed package lines. `uv.lock` appears. No build-backend error.

- [ ] **Step 8: Run the suite through uv**

```bash
uv run pytest
```

Expected: `350 passed, 2 skipped`.

This is the real gate for the config port — pytest is now reading `[tool.pytest.ini_options]`, so a wrong `pythonpath`, a missing `env` entry, or a dropped `asyncio_mode` shows up here as errors or collection changes.

- [ ] **Step 9: Confirm coverage config ported correctly**

```bash
uv run pytest --cov=src --cov-report=term 2>&1 | tail -5
```

Expected: a coverage table listing only `src/` modules. If `tests/` or site-packages appear, `[tool.coverage.run] omit` is wrong.

- [ ] **Step 10: Confirm the new files are tracked, not ignored**

```bash
git check-ignore -v .python-version uv.lock; echo "exit=$?"
```

Expected: no output, `exit=1`. Both files must be committable.

- [ ] **Step 11: Commit**

```bash
git add pyproject.toml uv.lock .python-version .gitignore
git add -u
git commit -m "chore: consolidate packaging config into pyproject.toml

Adds pyproject.toml as the single source of truth for dependencies,
pytest, coverage, black and isort. Dependency versions are unchanged
from requirements.txt and requirements-dev.txt.

Removes pytest.ini and .coveragerc, whose presence would take
precedence over the new pyproject.toml sections.

Stops gitignoring .python-version so the interpreter pin is committed."
```

---

### Task 2: Rewire the Makefile and delete the conda files

**Files:**
- Modify: `Makefile`
- Delete: `environment.yaml`
- Delete: `requirements.txt`
- Delete: `requirements-dev.txt`

**Interfaces:**
- Consumes: `pyproject.toml` from Task 1 — specifically `[project].version` (read by `uv version --short`) and the `dev` dependency group (installed by `uv sync` without extra flags).
- Produces: a `make lock` target wrapping `uv lock --upgrade`, used by Task 4.

- [ ] **Step 1: Replace the version and conda variables**

Find (lines 11-15):

```make
# Project version - update this when releasing new versions
VERSION := 1.1.0

# Conda executable — use $CONDA_EXE env var set by conda init, fall back to 'conda'
CONDA := $(or $(CONDA_EXE),conda)
```

Replace with:

```make
# Project version — single source of truth is pyproject.toml
VERSION := $(shell uv version --short)
```

Verified working against a non-package project on uv 0.11.18. If it ever fails, the tooling-free fallback is
`VERSION := $(shell awk -F'"' '/^version = /{print $$2; exit}' pyproject.toml)`.

- [ ] **Step 2: Update `.PHONY`**

Find (line 17), and remove `check-conda`, add `lock`:

```make
.PHONY: env init-dev run debug backup clean clean-state clean-cache clean-logs clean-data clean-conversations test test-unit test-integration test-cov test-watch migrate migrate-help config help setup check-deps version docs lock
```

- [ ] **Step 3: Update the help text**

Find:

```make
	@echo "  ${BOLD}make env${RESET}                   - 📦 Create conda environment and install dependencies"
```

Replace with:

```make
	@echo "  ${BOLD}make env${RESET}                   - 📦 Create virtual environment and install dependencies"
```

Find and delete this line entirely:

```make
	@echo "  ${BOLD}make check-conda${RESET}           - 🐍 Check if conda is installed"
```

Find:

```make
	@echo "  ${BOLD}make docs${RESET}                  - 📚 Generate project documentation"
```

Insert immediately after it:

```make
	@echo "  ${BOLD}make lock${RESET}                  - 🔒 Upgrade and relock dependencies"
```

- [ ] **Step 4: Replace `setup`, delete `check-conda`, rewrite `check-deps`**

Find (lines 48-61):

```make
setup: check-conda env check-deps config
	@echo "${GREEN}🎉 Project setup complete! Run 'make run' to start the bot.${RESET}"

check-conda:
	@echo "✅ Checking for conda..."
	@$(CONDA) --version > /dev/null || (echo "${RED}❌ conda is not installed. Please install miniconda or anaconda first.${RESET}" && exit 1)
	@echo "${GREEN}✅ conda is installed.${RESET}"

check-deps:
	@echo "✅ Checking for required dependencies..."
	@$(CONDA) --version > /dev/null || (echo "${RED}❌ conda is not installed. Please install miniconda or anaconda first.${RESET}" && exit 1)
	@which python > /dev/null || (echo "${RED}❌ python is not installed. Please install python first.${RESET}" && exit 1)
	@which pip > /dev/null || (echo "${RED}❌ pip is not installed. Please install pip first.${RESET}" && exit 1)
	@echo "${GREEN}✅ All required dependencies are installed.${RESET}"
```

Replace with:

```make
setup: check-deps env
	@echo "${GREEN}🎉 Project setup complete! Run 'make run' to start the bot.${RESET}"

check-deps:
	@echo "✅ Checking for required dependencies..."
	@uv --version > /dev/null 2>&1 || (echo "${RED}❌ uv is not installed. Install it from https://docs.astral.sh/uv/getting-started/installation/${RESET}" && exit 1)
	@echo "${GREEN}✅ All required dependencies are installed.${RESET}"
```

`config` is dropped from `setup`'s prerequisites because `env` already depends on it. Checking for `python` and `pip` separately is now pointless — `uv run` provisions both.

- [ ] **Step 5: Rewrite `env` and `init-dev`, add `lock`**

Find (lines 76-85):

```make
env: config
	@echo "📦 Creating conda environment and installing dependencies..."
	$(CONDA) env create -f environment.yaml
	@echo "${GREEN}✅ Dependencies installed successfully.${RESET}"

init-dev: env
	@echo "🛠️  Setting up development environment with pre-commit hooks..."
	pip install -r requirements-dev.txt
	pre-commit install
	@echo "${GREEN}✅ Development environment set up successfully.${RESET}"
```

Replace with:

```make
env: config
	@echo "📦 Creating virtual environment and installing dependencies..."
	uv sync
	@echo "${GREEN}✅ Dependencies installed successfully.${RESET}"

init-dev: env
	@echo "🛠️  Setting up development environment with pre-commit hooks..."
	uv run pre-commit install
	@echo "${GREEN}✅ Development environment set up successfully.${RESET}"

lock:
	@echo "🔒 Upgrading and relocking dependencies..."
	uv lock --upgrade
	@echo "${GREEN}✅ uv.lock updated. Run 'uv sync' to apply.${RESET}"
```

`uv sync` installs the `dev` group by default, so `init-dev` no longer needs a separate install step — only the hooks.

- [ ] **Step 6: Prefix every interpreter invocation with `uv run`**

Ten recipe lines change. **Each is an exact whole-line match, and every one begins
with a TAB character** — Make requires the tab, and matching on the whole line is
what keeps `@pytest` from also matching `@pytest -m integration`. Do not do a
substring replace.

Current lines (tab, then the text shown):

```make
	@ENV_FOR_DYNACONF=prod python src/bot.py
	@ENV_FOR_DYNACONF=dev python src/bot.py
	@python tools/migration.py
	@python tools/migration.py --help
	@python tools/generate_config.py
	@ptw . -- --testmon
	@pytest
	@pytest -m "not integration"
	@pytest -m integration
	@pytest --cov=src --cov-report=term --cov-report=html
```

Replace with, respectively (tab preserved on each):

```make
	@ENV_FOR_DYNACONF=prod uv run python src/bot.py
	@ENV_FOR_DYNACONF=dev uv run python src/bot.py
	@uv run python tools/migration.py
	@uv run python tools/migration.py --help
	@uv run python tools/generate_config.py
	@uv run ptw . -- --testmon
	@uv run pytest
	@uv run pytest -m "not integration"
	@uv run pytest -m integration
	@uv run pytest --cov=src --cov-report=term --cov-report=html
```

Verify each replacement landed on exactly one line before moving on:

```bash
grep -c "uv run" Makefile
```

Expected: `11` — the ten recipe lines above plus `uv run pre-commit install` in
`init-dev`. Nothing else in the Makefile uses `uv run`: `env` uses `uv sync`,
`lock` uses `uv lock`, `check-deps` uses `uv --version`, and `VERSION` uses
`uv version`. If the count differs, inspect with `grep -n "uv run" Makefile`.

- [ ] **Step 7: Verify no conda references survive**

```bash
grep -n -i "conda\|requirements" Makefile; echo "exit=$?"
```

Expected: no output, `exit=1`.

- [ ] **Step 8: Delete the conda and requirements files**

```bash
git rm -q environment.yaml requirements.txt requirements-dev.txt
```

- [ ] **Step 9: Exercise the rewired targets**

```bash
make version
make test
make test-unit
make test-integration
```

Expected: `make version` prints `🏷️  Project version: 1.1.0`. `make test` prints `350 passed, 2 skipped`. `make test-unit` and `make test-integration` both pass, and their counts sum to 350 plus the 2 skipped.

- [ ] **Step 10: Exercise coverage and the migration tool**

```bash
make test-cov
make migrate-help
```

Expected: `make test-cov` passes and writes `htmlcov/index.html` (it also opens a browser — that is pre-existing behaviour). `make migrate-help` prints the migration tool's argument help.

- [ ] **Step 11: Smoke-test a real boot**

```bash
make debug
```

Expected: the bot starts, connects to Telegram, and logs normally. Interrupt with Ctrl-C after confirming startup. Requires the local, git-ignored `config/settings.local.yml` and `config/.secrets.local.yml` to be present.

This gate exists because dynaconf drives configuration loading at startup and the test suite exercises that path far less than a real boot does.

- [ ] **Step 12: Commit**

```bash
git add Makefile
git add -u
git commit -m "chore: drive the Makefile through uv instead of conda

Removes check-conda and the CONDA variable, derives VERSION from
pyproject.toml, and prefixes every interpreter invocation with
uv run so no environment activation is needed.

Adds a lock target wrapping uv lock --upgrade.

Deletes environment.yaml, requirements.txt and requirements-dev.txt,
now superseded by pyproject.toml and uv.lock."
```

---

### Task 3: Pre-commit hooks and documentation

**Files:**
- Modify: `.pre-commit-config.yaml`
- Modify: `README.md`
- Modify: `CLAUDE.md`

**Interfaces:**
- Consumes: `uv.lock` and `pyproject.toml` from Task 1; the `make` target names from Task 2.
- Produces: nothing consumed by later tasks. Completes Phase 1.

- [ ] **Step 1: Remove the dead hook**

In `.pre-commit-config.yaml`, find and delete this line:

```yaml
      - id: requirements-txt-fixer
```

`requirements.txt` no longer exists, so the hook can never fire.

- [ ] **Step 2: Rewire the local pytest hook**

Find:

```yaml
        entry: pytest -q
```

Replace with:

```yaml
        entry: uv run pytest -q
```

The hook uses `language: system`, so without `uv run` it depends on an activated environment that no longer exists.

- [ ] **Step 3: Add the lock-drift guard**

Append to the `repos:` list, after the `local` repo block:

```yaml
  - repo: https://github.com/astral-sh/uv-pre-commit
    rev: 0.11.18
    hooks:
      - id: uv-lock
```

This fails the commit if `pyproject.toml` changed without `uv.lock` being regenerated.

Do **not** touch the `black` or `isort` `rev:` values in this task. They stay at 25.1.0 and 6.0.1 through Phase 2 so no reformat happens before Phase 3.

- [ ] **Step 4: Run all hooks**

```bash
uv run pre-commit run --all-files
```

Expected: every hook passes. `check-toml` now validates `pyproject.toml`. If `uv-lock` fails, run `uv lock` and re-run.

- [ ] **Step 5: Update `README.md` prerequisites**

Find:

```markdown
- Conda (Miniconda or Anaconda)
```

Replace with:

```markdown
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
```

- [ ] **Step 6: Remove the activation step from `README.md`**

Find and delete this entire numbered step, including its code fence:

```markdown
7. Activate the environment:

   ```bash
   conda activate telegram-bot
   ```

```

Renumber the following step ("Run the bot:") from 8 to 7.

This step was already broken — it names `telegram-bot`, an environment the project never created. With `uv run` no activation is needed at all.

- [ ] **Step 7: Update the `README.md` Makefile reference table**

Find:

```markdown
| `make env` | 📦 Create conda environment and install dependencies |
```

Replace with:

```markdown
| `make env` | 📦 Create virtual environment and install dependencies |
```

Find and delete:

```markdown
| `make check-conda` | 🐍 Check if conda is installed |
```

Find:

```markdown
| `make docs` | 📚 Generate project documentation |
```

Insert immediately after it:

```markdown
| `make lock` | 🔒 Upgrade and relock dependencies |
```

- [ ] **Step 8: Update `CLAUDE.md`**

Find:

```markdown
make setup        # First-time setup (conda env + config generation)
```

Replace with:

```markdown
make setup        # First-time setup (uv sync + config generation)
make lock         # Upgrade and relock dependencies (uv lock --upgrade)
```

Then find the end of the `## Commands` fenced block and add this paragraph immediately after it:

```markdown
Dependencies are managed with [uv](https://docs.astral.sh/uv/). `pyproject.toml`
is the single source of truth (deps, pytest, coverage, black, isort) and
`uv.lock` pins exact versions. No environment activation is needed — every
Makefile target runs through `uv run`.

Each git worktree gets its own `.venv`. A newly created worktree needs its own
`uv sync` before tests will run.
```

- [ ] **Step 9: Verify no conda references survive in tracked files**

```bash
git grep -n -i "conda" -- . ':!docs'; echo "exit=$?"
```

Expected: no output, `exit=1`. `git grep` is used rather than plain `grep` so the
search covers tracked files only — `backup/`, `data/`, `logs/` and `htmlcov/` are
gitignored and would otherwise produce noise. The `docs/` exclusion is deliberate:
the spec and this plan legitimately discuss conda in describing the migration.

- [ ] **Step 10: Re-run the suite**

```bash
uv run pytest
```

Expected: `350 passed, 2 skipped`.

- [ ] **Step 11: Commit**

```bash
git add .pre-commit-config.yaml README.md CLAUDE.md
git commit -m "chore: rewire pre-commit and docs for uv

Drops requirements-txt-fixer, points the local pytest hook at uv run,
and adds the uv-lock hook to catch lockfile drift.

Updates README and CLAUDE.md: uv replaces conda as the prerequisite,
and the broken 'conda activate telegram-bot' step is removed entirely
since uv run needs no activation."
```

**Phase 1 is complete.** The project now runs entirely on uv with dependency versions untouched.

---

## Phase 2 — Dependency bump

### Task 4: Bump every dependency to latest

**Files:**
- Modify: `pyproject.toml`
- Regenerated: `uv.lock`

**Interfaces:**
- Consumes: everything from Phase 1.
- Produces: an environment on pytest 9.x and pytest-asyncio 1.x, which Task 5 formats against.

- [ ] **Step 1: Capture the pre-bump resolution for later comparison**

```bash
uv pip list > /tmp/uv-versions-before.txt
"${CONDA_EXE:-conda}" list -n sobornyi-bot > /tmp/conda-versions-before.txt
wc -l /tmp/uv-versions-before.txt /tmp/conda-versions-before.txt
```

Both files must be non-empty. These are scratch files outside the repository — never commit them.

- [ ] **Step 2: Replace the pins with ranges**

In `pyproject.toml`, replace the `dependencies` and `[dependency-groups]` tables with:

```toml
dependencies = [
    "dynaconf>=3.3.4,<4",
    "python-telegram-bot[callback-data,job-queue]>=22.8,<23",
]

[dependency-groups]
dev = [
    "black>=26.5.1,<27",
    "isort>=8.0.1,<9",
    "pre-commit>=4.6.1,<5",
    "pyright>=1.1.411,<2",
    "pytest>=9.1.1,<10",
    "pytest-asyncio>=1.4,<2",
    "pytest-cov>=7.1,<8",
    "pytest-env>=1.7,<2",
    "pytest-testmon>=2.2,<3",
    "pytest-watcher>=0.6.3,<0.7",
]
```

`python-telegram-bot` stays inside major 22, so no bot-code API change is expected.

- [ ] **Step 3: Apply the pytest-asyncio 1.x configuration changes**

In `[tool.pytest.ini_options]`, replace:

```toml
markers = [
    "asyncio: marks a test as an asyncio coroutine",
    "integration: marks a test as an integration test (deselect with '-m \"not integration\"')",
]
env = ["DYNACONF_ENV=dev"]
asyncio_mode = "auto"
```

with:

```toml
markers = [
    "integration: marks a test as an integration test (deselect with '-m \"not integration\"')",
]
env = ["DYNACONF_ENV=dev"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

The `asyncio` marker declaration is removed because pytest-asyncio registers that marker itself. `asyncio_default_fixture_loop_scope` is added because pytest-asyncio 1.x emits a deprecation warning when it is unset.

- [ ] **Step 4: Relock and sync**

```bash
uv lock --upgrade && uv sync
```

Expected: resolution succeeds. If it fails with a conflict, the message names the incompatible pair — report it rather than widening a range unilaterally, since the ranges above were resolved together and verified on 2026-08-03.

- [ ] **Step 5: Confirm the intended versions landed**

```bash
uv pip list | grep -Ei "^(dynaconf|python-telegram-bot|pytest|pytest-asyncio|pytest-cov|black|isort) "
```

Expected: `dynaconf 3.3.4`, `python-telegram-bot 22.8`, `pytest 9.1.1`, `pytest-asyncio 1.4.0`, `pytest-cov 7.1.0`, `black 26.5.1`, `isort 8.0.1` (or newer within the same declared range).

- [ ] **Step 6: Run the suite**

```bash
uv run pytest
```

Expected: `350 passed, 2 skipped`, with no `PytestDeprecationWarning` from pytest-asyncio.

If this fails, the three known-plausible causes, in order of likelihood:

1. *`fixture 'event_loop' not found`* — pytest-asyncio 1.0 removed that fixture. A grep of `tests/` and `src/` on 2026-08-03 found no references, so this should not occur; if it does, the fixture must be replaced with `asyncio_default_fixture_loop_scope` configuration rather than reinstated.
2. *`Unknown config option`* warnings — a key in `[tool.pytest.ini_options]` was renamed in pytest 9. Check the exact key named in the warning against the pytest changelog.
3. *Coverage table empty or missing under `make test-cov`* — pytest-cov 7 changed how `--cov=src` interacts with `[tool.coverage.run] source`. Confirm `source = ["src"]` is still present and correct.

- [ ] **Step 7: Verify coverage still works**

```bash
make test-cov
```

Expected: passes, coverage table lists only `src/` modules, `htmlcov/index.html` written.

- [ ] **Step 8: Verify the watcher still works**

```bash
make test-watch
```

Expected: pytest-watcher starts and reports it is watching. Interrupt with Ctrl-C once confirmed. This exercises `pytest-testmon` 2.2 and `pytest-watcher` together, which nothing else covers.

- [ ] **Step 9: Smoke-test a real boot on the new dynaconf**

```bash
make debug
```

Expected: bot starts, connects, logs normally. Ctrl-C to stop. This is the gate that matters for the dynaconf 3.2 to 3.3 jump.

- [ ] **Step 10: Review transitive drift**

```bash
uv pip list > /tmp/uv-versions-after.txt
diff /tmp/uv-versions-before.txt /tmp/uv-versions-after.txt
```

Read the diff. Direct dependencies changing is expected. Flag for review any transitive package that jumped a major version — particularly `httpx`, `httpcore`, `anyio`, and `apscheduler`, which sit under `python-telegram-bot` and affect network and scheduling behaviour at runtime.

- [ ] **Step 11: Confirm pre-commit still passes without reformatting**

```bash
uv run pre-commit run --all-files
```

Expected: all hooks pass and **no file is modified**. The `black` and `isort` hooks still pin 25.1.0 and 6.0.1 through pre-commit's own isolated environments, so they must not reformat anything here. If a file changes, Step 3 of Task 3 was not followed and formatter revs were bumped early — revert the reformat and fix the revs.

- [ ] **Step 12: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: bump all dependencies to latest

Runtime: dynaconf 3.2.10 -> 3.3.4, python-telegram-bot 22.0 -> 22.8
(same major, no API change).

Dev: pytest 8 -> 9, pytest-asyncio 0.23 -> 1.4, pytest-cov 4 -> 7,
black 25 -> 26, isort 6 -> 8, plus minor bumps.

Manifest now declares compatible ranges; uv.lock holds exact versions.

Drops the redundant asyncio marker declaration (pytest-asyncio
registers it) and sets asyncio_default_fixture_loop_scope, both
required by pytest-asyncio 1.x.

Formatter reformat is deliberately deferred to its own commit."
```

**Phase 2 is complete.** Versions are current; no source file has been touched.

---

## Phase 3 — Formatter reformat

### Task 5: Bump formatter hooks and reformat

**Files:**
- Modify: `.pre-commit-config.yaml`
- Modify: files under `src/`, `tests/`, `tools/` — formatting only

**Interfaces:**
- Consumes: black 26.5.1 and isort 8.0.1 from Task 4's environment.
- Produces: nothing. Final code task.

- [ ] **Step 1: Bump the formatter revs**

In `.pre-commit-config.yaml`, find:

```yaml
  - repo: https://github.com/psf/black
    rev: 25.1.0
```

Replace `rev: 25.1.0` with `rev: 26.5.1`.

Find:

```yaml
  - repo: https://github.com/pycqa/isort
    rev: 6.0.1
```

Replace `rev: 6.0.1` with `rev: 8.0.1`.

These must match the versions resolved in `uv.lock`, or pre-commit and `make`-driven runs will disagree about formatting.

- [ ] **Step 2: Reformat**

```bash
uv run black . && uv run isort .
```

- [ ] **Step 3: Confirm the diff is formatting only**

```bash
git diff --stat
git diff -w --stat
```

The second command ignores whitespace. Every file listed in the first output that is *absent* from the second changed by whitespace alone. Any file still showing substantive changes in the `-w` output must be inspected line by line — black reflowing a string or an expression is acceptable, but no logic may change.

- [ ] **Step 4: Run the suite**

```bash
uv run pytest
```

Expected: `350 passed, 2 skipped`. Formatting must not alter behaviour; a failure here means black or isort changed semantics, which warrants stopping and inspecting rather than fixing forward.

- [ ] **Step 5: Confirm the formatters are now idempotent**

```bash
uv run pre-commit run --all-files
```

Expected: all hooks pass and no file is modified. A modification here means the pre-commit `rev`s and the locked versions still disagree.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "style: reformat for black 26 and isort 8

Formatting only. No logic changes.

Bumps the black and isort pre-commit revs to match the versions
locked in uv.lock, then applies the resulting reformat as an
isolated commit so it can be skipped wholesale during review."
```

---

## Task 6: Final verification and handoff notes

**Files:**
- No tracked files. Operator deployment notes live outside the repository.

**Interfaces:**
- Consumes: the completed migration.
- Produces: nothing.

- [ ] **Step 1: Full gate sweep from a clean state**

```bash
rm -rf .venv
uv sync
uv run pytest
make version
make test-unit
make test-integration
make test-cov
uv run pre-commit run --all-files
```

Expected: `.venv` rebuilt from `uv.lock` alone, `350 passed, 2 skipped`, `make version` prints `1.1.0`, every other command passes. This proves a fresh clone works.

- [ ] **Step 2: Confirm the committed file set is correct**

```bash
git status --short
git ls-files | grep -E "pyproject.toml|uv.lock|.python-version|environment.yaml|requirements|pytest.ini|coveragerc"
```

Expected: `git status` clean. The `ls-files` output lists exactly `.python-version`, `pyproject.toml`, and `uv.lock` — and none of `environment.yaml`, `requirements.txt`, `requirements-dev.txt`, `pytest.ini`, `.coveragerc`.

- [ ] **Step 3: Record the deployment procedure in the operator's out-of-repo notes**

Replace the conda placeholder with:

1. One-time on the host: install uv via the standalone installer from `https://astral.sh/uv/install.sh`. It needs no pre-existing Python.
2. Deploy: pull the target revision, run `uv sync --no-dev --frozen`, restart the process.

`--frozen` forbids re-resolution so the host installs exactly what `uv.lock` records. `--no-dev` omits the development group. uv provisions CPython 3.13 itself from `.python-version`.

- [ ] **Step 4: Record the follow-ups in the operator's out-of-repo task list**

- Replace black and isort with ruff.
- Reconcile the version seeded in `src/init.py` with `pyproject.toml`, completing the single-source-of-truth work.
- Decide whether to reinstate Dependabot via `.github/dependabot.yml` declaring the `uv` ecosystem — deleting `requirements.txt` ends the existing pip-based dependabot branches.

- [ ] **Step 5: Confirm the rollback path is intact**

```bash
"${CONDA_EXE:-conda}" env list | grep sobornyi-bot
```

Expected: the environment still exists. **Do not remove it.** It is removed only after production has been verified on uv, which is outside this plan.

- [ ] **Step 6: Stop for merge approval**

Do not merge into `develop`. Report completion and wait for explicit approval.

---

## Rollback

At any point before merge: `git checkout develop` and `conda activate sobornyi-bot` restores the previous working setup. The conda environment is untouched by this plan.
