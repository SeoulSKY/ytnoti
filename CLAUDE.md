# CLAUDE.md

## The project

`ytnoti` is a published PyPI library that delivers YouTube push notifications
over [WebSub/PubSubHubbub](https://pubsubhubbub.appspot.com). The user
registers listeners, and the library runs a FastAPI/uvicorn server that
subscribes to channels with Google's hub and receives the hub's callbacks.

| Path | What lives there |
| --- | --- |
| `ytnoti/__init__.py` | `AsyncYouTubeNotifier` (the whole implementation) and `YouTubeNotifier`, a thin sync subclass that drives it through `_run_coroutine` |
| `ytnoti/models/video.py` | the `Channel`, `Timestamp`, `Video` and `DeletedVideo` dataclasses handed to listeners |
| `ytnoti/models/history.py` | the `VideoHistory` ABC and its in-memory and file backends, used to tell an upload from an edit |
| `ytnoti/types.py` | the listener callable aliases |
| `ytnoti/errors.py` | `HTTPError` |
| `ytnoti/__main__.py` | a manual end-to-end script — needs `NGROK_TOKEN` in `.env` and talks to the real hub |
| `tests/` | mirrors the package; `respx` mocks every outbound httpx call |
| `docs/` | the Sphinx site published to Read the Docs |
| `docs/changelog.rst` | the user-facing history of every release — see below |

## Commands

Dependencies are managed with `uv`; run everything through `uv run`.

```bash
uv sync --all-groups                              # set up
uv run pytest --cov --cov-report=term-missing     # CONTRIBUTING expects 100% coverage
uv run ruff check .                               # what CI enforces
uv run ty check                                   # what CI enforces
uv run vermin -t=3.11 --violations ytnoti         # the 3.11 floor is real
uv run sphinx-build -M html docs docs/build/      # preview the docs
```

`ruff format` is not enforced by CI, and two files are not formatter-clean
today. Format only the files you touched, never the tree.

## Conventions

- Ruff runs with `select = ["ALL"]` (see `ruff.toml`). Every module, class and
  function needs a docstring in the existing reST style — `:param x:`,
  `:return:`, `:raises X:`. Reach for a narrow `# noqa: <code>` only when the
  rule is genuinely wrong here, as the existing ones are.
- Python 3.11 is the floor. `override` comes from `typing_extensions` below
  3.12, and `vermin` will catch newer syntax.
- Everything is annotated and `ty` must pass. Targeted `# ty: ignore[...]`
  comments carry the sync subclass's deliberately narrowed signatures.
- `YouTubeNotifier` mirrors `AsyncYouTubeNotifier`. When you change a public
  async method, check whether the sync class overrides it and keep the two
  signatures and docstrings in step.
- Log through `self._logger` with lazy `%s` formatting, never f-strings.
- Tests mock the network with `respx` and mark coroutines with
  `@pytest.mark.asyncio`. Nothing in `tests/` may touch the real internet.

## Things to know before changing the notifier

- **Subscriptions are leases.** The hub grants roughly five days, and
  `_on_startup` renews every channel once a day through `_repeat_task`. If a
  renewal path can fail silently or be skipped, notifications stop days later
  with nothing in the log — treat that loop as load-bearing.
- **`hub.verify=sync` makes subscribing slow.** The hub calls back into this
  very server to verify the callback *before* it answers the subscribe POST,
  so a request takes seconds and requires the event loop to stay free. Never
  block the loop, and never assume a default HTTP timeout is generous enough.
- **Notifications are authenticated**, not trusted: `_is_authorized` checks an
  HMAC of the raw body against `self._password` via `X-Hub-Signature`.
- **The hub re-sends and lies about "new".** `_classify` decides upload vs
  edit from `VideoHistory` plus a 20-second published/updated delta, which is
  why the history is consulted under `self._lock`.
- **The callback endpoint is derived from the callback URL's path**
  (`_get_endpoint`) and is reserved on the user's own FastAPI app: HEAD/GET
  answers the WebSub challenge, POST receives notifications.

## The changelog

`docs/changelog.rst` is the release history the docs site publishes, so it is
written for someone using the library, not for someone reading the diff. Add
to it whenever a change alters behaviour a user can observe; skip it for
refactors, tests and tooling.

- Newest version first. A version heading is `vX.Y.Z` underlined with `-`,
  and the optional `Features` / `Fixes` / `Breaking Changes` subsections under
  it are underlined with `~`.
- One bullet per change, on a single unwrapped line, starting with a verb in
  the same tense as its neighbours — usually "Fix that ...". Say what a user
  saw go wrong and what happens now, never which function changed. Wrap code
  in RST double-backtick literals, and name both classes at once the way the
  existing entries do, as (Async)YouTubeNotifier.
- Close the entry with a blank line and
  `**Full Changelog**: https://github.com/SeoulSKY/ytnoti/compare/vPREV...vNEW`.
- A release that needs migration steps ends with a `:doc:` link to `migration`
  and gets a matching section in `docs/migration.rst`.

Add the entry under the version the work will ship as, creating that heading
when this is the first change since the last release.

## Releasing

The version lives in `pyproject.toml`, and `docs/conf.py` carries its own
`release` string that has drifted before — update both, and check that the
top of `docs/changelog.rst` already names that version. Creating a GitHub
release triggers `.github/workflows/pypi.yml`, which builds and publishes to
PyPI.

## Commit messages

Follow [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).
Do not derive the style from `git log` — commits made before this file exists
use past-tense descriptions and do not follow the rules below.

```text
<type>[(scope)][!]: <description>

[body]

[footers]
```

### Type

Required, lowercase, one of:

| Type | Use for |
| --- | --- |
| `feat` | a new capability for a user of the app or API |
| `fix` | a bug fix in behaviour shipped by an earlier `feat` |
| `refactor` | restructuring that does not change behaviour |
| `perf` | a change made specifically to improve performance |
| `test` | adding or correcting tests only |
| `docs` | documentation only, including this file and the README |
| `build` | build system, Docker images, dev tooling, dependencies |
| `ci` | GitHub Actions workflows and anything else CI-only |
| `chore` | maintenance that fits nothing above (`.gitignore`, cleanup) |

Append `!` before the colon for a breaking change (`feat(notifier)!: ...`) and
explain it in the description, or add a `BREAKING CHANGE: <what breaks>`
footer. `BREAKING CHANGE` is the one part of the message that is uppercase.

### Scope

Optional. A noun naming the section of the codebase the change is confined
to. Omit it when the change spans several areas or fits none — an omitted
scope is better than a vague one. Never use an issue number as a scope.

Scopes for this repo:

| Scope | Area |
| --- | --- |
| `notifier` | the notifier classes in `ytnoti/__init__.py` — subscription, the callback endpoints, listener dispatch |
| `history` | `VideoHistory` and its backends in `ytnoti/models/history.py` |
| `models` | the video dataclasses in `ytnoti/models/video.py` and the listener aliases in `ytnoti/types.py` |
| `errors` | `ytnoti/errors.py` |
| `examples` | `examples/` |
| `deps` | dependency bumps, usually `build(deps):` |

The core is a single module, so most changes to it are either `notifier` or
unscoped. A `docs:` or `test:` type already says where the change is and
rarely needs a scope on top.

### Description

- Imperative present tense: "add", not "added" or "adds".
- Lowercase first word — no capital, no trailing period.
- Say what the change does, not which files it touches.
- Keep the whole header at 50 characters or fewer where it reads naturally,
  and never past 72.

### Body

Optional but expected for anything whose reason is not obvious from the
header — a subtle fix, a non-obvious design decision, a structural change.
Skip it when the header genuinely says everything.

- Begins one blank line after the description, wrapped at 72 characters.
- Same imperative present tense as the description.
- Explains *why* the change is needed and how the behaviour differs from
  before. Never a bullet list of the diff — the diff is already in the
  commit.

### Footers

One blank line after the body. Each footer is `Token: value`, with `-` in
place of spaces in the token (`Reviewed-by:`, `Refs:`). Use them for issue
references (`Closes: #123`) and breaking changes.

### Example

```text
fix(notifier): keep renewing after a failed request

A subscribe request that timed out aborted the whole daily renewal, so
every channel after the failing one silently lost its lease days later.
Request every channel and raise the first failure once the batch is
done.
```

Keep one logical change per commit; split a mixed diff rather than writing a
message that has to explain two unrelated things.

### When to commit

Only when asked. Finishing a change is not a request to commit one — leave the
work in the tree and say what is in it. Committing, pushing and opening a
branch are three separate requests, and none of them implies the others.

### Which branch

This section says *where* a commit goes once one has been asked for; it is not
licence to make one. Commit on the branch that is checked out, `main` included.
Do not open a branch for the work unless asked for one, and do not push —
pushing is a separate request every time.