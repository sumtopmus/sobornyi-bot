# Migrate package management from conda to uv

- **Date:** 2026-08-03
- **Branch:** `refactor/uv-migration` (off `develop`)
- **Status:** Approved, pending implementation plan

## Context

The project pins Python and pip through conda (`environment.yaml`), then delegates
every actual dependency to pip via `-r requirements.txt`. Conda therefore earns
nothing: both runtime dependencies are pure Python wheels with no binary or
non-Python components. What conda does cost is a heavyweight prerequisite for
anyone setting the project up, a mandatory `conda activate` step before any
command works, and one environment shared across every git worktree.

Configuration is spread across five files with no lockfile anywhere, so
reproducibility rests entirely on hand-maintained `==` pins.

## Goals

1. Remove conda as a prerequisite. Replace it with uv, which manages the Python
   interpreter, the virtual environment, resolution, and a real lockfile.
2. Collapse packaging and tool configuration into a single `pyproject.toml`.
3. Bring every dependency to its current release and prove the suite still passes.
4. Keep the Makefile as the developer interface; no workflow the operator already
   knows should disappear.

## Non-goals

- No change to application code, bot behaviour, or the config layering scheme.
- No swap of black/isort for ruff. Recorded as a follow-up, not done here.
- No fix for the stale version seed in `src/init.py` (tracked separately). This
  change makes that fix easier but does not perform it.
- No CI pipeline. The repository has none today and gains none here.

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Tool | uv | Only candidate that also replaces conda's interpreter management. Poetry and PDM would still require pyenv for Python 3.13. |
| Config consolidation | Full | `pyproject.toml` absorbs deps, pytest, coverage, black, isort. Five files become one. |
| Pinning | Ranges in `pyproject.toml`, exact in `uv.lock` | The lockfile provides reproducibility, freeing the manifest to express intent. Upgrades become `uv lock --upgrade`. |
| Lockfile | Committed | Reproducible installs on the production host. |
| Makefile | Retained, internals rewired | 19 of its 25 targets are unrelated to packaging. It stays the documented front door. |
| Dependency bump | To latest, as its own commit | Requested. Isolated from the tooling change so failures are attributable. |
| Formatter bump | To latest, reformat as its own commit | black 26 and isort 8 rewrite source files; that diff must not be tangled with logic or tooling. |
| Production host | uv installed there | Standalone installer needs no system Python. Enables `uv sync --frozen`. |

## Target state

### Files

```
added     pyproject.toml       single source of truth
added     uv.lock              committed; exact, hashed
added     .python-version      3.13

removed   environment.yaml
removed   requirements.txt
removed   requirements-dev.txt
removed   pytest.ini
removed   .coveragerc

modified  Makefile
modified  .pre-commit-config.yaml
modified  README.md
modified  CLAUDE.md
modified  .gitignore
```

`.gitignore` requires one deletion, and it is not optional. Line 104 ignores
`.python-version`, inherited from the pyenv section of the standard Python
template. Left in place, the interpreter pin is silently never committed: a fresh
clone and the production host would each resolve to whatever Python uv defaults
to, defeating the pin and undermining `uv sync --frozen`. Remove that line and the
now-empty `# pyenv` heading above it.

`.venv` is already ignored (line 124) and stays ignored. `uv.lock` is not matched
by any existing rule and must be committed — verified with `git check-ignore`.

### `pyproject.toml`

Final state after the dependency bump:

```toml
[project]
name = "sobornyi-bot"
version = "1.1.0"
description = "Telegram bot to control the Sobornyi group"
readme = "README.md"
requires-python = ">=3.13,<3.14"
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
    "integration: marks a test as an integration test (deselect with '-m \"not integration\"')",
]
env = ["DYNACONF_ENV=dev"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
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

`package = false` is required. `src/` is not an installable package — tests reach
it through `pythonpath`, and there is no build backend. Without this setting uv
treats the project as a distribution and fails for lack of one.

The `asyncio` marker declared in today's `pytest.ini` is dropped: pytest-asyncio
registers that marker itself, so the local declaration is redundant.
`asyncio_default_fixture_loop_scope` is added because pytest-asyncio 1.x emits a
deprecation warning when it is unset. Both changes belong to the bump commit, not
the migration commit — see Sequencing.

### Makefile

Deletions: the `CONDA` variable and the `check-conda` target, plus its use as a
`setup` prerequisite.

```make
VERSION := $(shell uv version --short)

check-deps:
	@uv --version >/dev/null 2>&1 || (echo "uv is not installed. See https://docs.astral.sh/uv/" && exit 1)

setup: env config
env:
	uv sync
init-dev: env
	uv run pre-commit install
lock:
	uv lock --upgrade
```

Every target invoking the interpreter gains a `uv run` prefix: `run`, `debug`,
`migrate`, `migrate-help`, `config`, `test`, `test-unit`, `test-integration`,
`test-cov`, `test-watch`. `uv run` creates and syncs `.venv` on demand, so no
activation step is needed anywhere.

`uv sync` installs the `dev` dependency group by default, so `env` alone yields a
complete development environment and `init-dev` only has to install the hooks.

`lock` is new. It makes the next dependency bump a single command.

Help text and the `.PHONY` list are updated: `check-conda` removed, `lock` added.

If `uv version --short` proves unavailable for a non-package project, fall back to
`VERSION := $(shell awk -F'"' '/^version = /{print $$2; exit}' pyproject.toml)`,
which has no tooling dependency at all.

### Pre-commit

- Remove `requirements-txt-fixer` — dead once `requirements.txt` is gone.
- Change the local `pytest` hook entry to `uv run pytest -q`. It uses
  `language: system` and would otherwise depend on an activated environment.
- Add the lock-drift guard:

  ```yaml
  - repo: https://github.com/astral-sh/uv-pre-commit
    rev: 0.11.18
    hooks:
      - id: uv-lock
  ```

- Bump the `black` and `isort` hook `rev`s to match the versions resolved in
  `pyproject.toml`.

The existing `check-toml` hook begins validating `pyproject.toml`, which is a free
gain.

Accepted duplication: hook `rev`s and `[dependency-groups]` pins now record the
same versions in two places, and `uv-lock` does not police the pair. The
alternative — running the formatters as local hooks through `uv run` — sacrifices
pre-commit's environment isolation, which is a worse trade.

### Documentation

`README.md`: replace the conda prerequisite with uv, drop the `conda activate`
step entirely (it names a nonexistent environment, `telegram-bot`), and update the
Makefile reference table — `check-conda` out, `lock` in.

`CLAUDE.md`: update the `make setup` description, and note that each git worktree
carries its own `.venv` and needs its own `uv sync`.

Operator deployment notes are maintained outside the repository and are updated
separately; see Deployment below for the content.

## Dependency bump

Resolved against the index on 2026-08-03:

| Package | From | To | Notes |
|---|---|---|---|
| dynaconf | 3.2.10 | 3.3.4 | Minor. Touches config loading — verify by booting the bot, not only by running tests. |
| python-telegram-bot | 22.0 | 22.8 | Minor within the same major. No API churn expected. |
| pytest | 8.3.4 | 9.1.1 | Major. |
| pytest-asyncio | 0.23.5 | 1.4.0 | Major. Largest jump; see Risks. |
| pytest-cov | 4.1.0 | 7.1.0 | Three majors. |
| pytest-env | 1.1.5 | 1.7.0 | Minor. |
| pytest-testmon | 2.1.3 | 2.2.0 | Minor. |
| pytest-watcher | 0.6.3 | 0.6.3 | Unchanged. |
| pre-commit | 4.1.0 | 4.6.1 | Minor. |
| pyright | 1.1.408 | 1.1.411 | Patch. |
| black | 25.1.0 | 26.5.1 | Major. Reformats source. |
| isort | 6.0.1 | 8.0.1 | Two majors. May reorder imports. |

## Sequencing

Three commits. The split exists so that any failure is attributable to exactly one
kind of change.

**Commit 1 — `chore: migrate conda to uv`**

`pyproject.toml` carries today's exact `==` pins, unchanged. `pytest.ini` and
`.coveragerc` are ported verbatim, including the redundant `asyncio` marker. Only
the tooling moves. A failure here is a porting error.

**Commit 2 — `chore: bump dependencies to latest`**

Replace the `==` pins with the ranges above, `uv lock --upgrade`, then fix
fallout. The redundant `asyncio` marker is dropped and
`asyncio_default_fixture_loop_scope` added here, since both are consequences of
pytest-asyncio 1.x. A failure here is a genuine incompatibility.

**Commit 3 — `style: reformat for black 26 / isort 8`**

Output of `uv run black .` and `uv run isort .`. Formatting only. Must contain no
logic change.

## Verification

Every commit independently satisfies all of:

| Check | Expected |
|---|---|
| `uv sync` | `.venv` created, no resolution errors |
| `git status --porcelain` after commit 1 | `.python-version` and `uv.lock` are tracked, not ignored |
| `uv run pytest` | **350 passed, 2 skipped** — the pre-migration baseline |
| `make test-unit` | passes |
| `make test-integration` | passes |
| `make test-cov` | passes, writes `htmlcov/index.html` |
| `make debug` | bot starts, reaches Telegram, exits cleanly on interrupt |
| `make version` | prints `1.1.0` |
| `make migrate-help` | prints migration tool help |
| `uv run pre-commit run --all-files` | passes |

Commit 3 additionally requires `git diff` to show only whitespace and import
reordering.

`make debug` is a required gate, not a convenience: dynaconf drives configuration
loading at startup, and the test suite exercises that path far less than a real
boot does.

## Risks

**pytest-asyncio 0.23 to 1.4.** The `event_loop` fixture was removed in 1.0. Grep
confirms no test or fixture in the repository references it, and the suite relies
on `@pytest.mark.asyncio` with `asyncio_mode = auto`, which survives. Residual
risk is low but this is the jump most likely to produce fallout.

**pytest 8 to 9.** Removed deprecated APIs. The suite uses no plugins beyond those
listed. Mitigated by the baseline count.

**pytest-cov 4 to 7.** The `--cov` and `--cov-report` arguments used by `test-cov`
are unchanged across these majors. The `.coveragerc` to `[tool.coverage.*]` move
is a straight key-for-key port.

**Transitive drift.** Loosening to ranges lets transitive dependencies resolve
newer than the current environment. Before removing the conda environment, diff
the versions resolved in `uv.lock` against `conda list` from that environment and
review anything unexpected.

**Worktree environments.** Conda provided one environment shared by every
worktree; uv gives each worktree its own `.venv`. This is better isolation, but
each worktree now requires its own `uv sync`. Documented in `CLAUDE.md`.

**Dependabot.** The remote carries dependabot branches for pip, opened without a
config file in the repository. Removing `requirements.txt` will end that
behaviour. Restoring it would require a `.github/dependabot.yml` declaring the
`uv` ecosystem. Out of scope; noted as a follow-up.

## Deployment

The production host runs the bot by polling and currently activates a conda
environment. New procedure:

1. One-time on the host: install uv via the standalone installer from
   `https://astral.sh/uv/install.sh`. It requires no pre-existing Python.
2. Deploy: pull the target revision, then `uv sync --no-dev --frozen`, then
   restart the process.

`--frozen` forbids re-resolution, so the host installs exactly what `uv.lock`
records. `--no-dev` omits the development group. uv provisions CPython 3.13 itself
according to `.python-version`, so no system interpreter is required.

Operator deployment notes are updated with these steps, replacing the conda
placeholder currently recorded there.

## Rollback

The conda environment is left intact until production is verified. Reverting is
activating it again and checking out `develop`. Removing the environment is a
separate, deliberate step taken only after production runs on uv successfully.

## Follow-ups

Recorded, not done here:

- Replace black and isort with ruff.
- Reconcile the version seeded in `src/init.py` with `pyproject.toml`, completing
  the single-source-of-truth work this change begins.
- Decide whether to reinstate Dependabot via `.github/dependabot.yml` for the uv
  ecosystem.
