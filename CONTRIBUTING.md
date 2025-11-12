# Contributing to ytnoti

:+1::tada: First off, thanks for taking the time to contribute! :tada::+1:

We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## How to Contribute to the codebase

Pull requests are the best way to propose changes to the codebase (we use [Github Flow](https://guides.github.com/introduction/flow/index.html)). We actively welcome your pull requests:

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/), a modern Python package and project manager.  
2. Install Python `3.11`.

```bash
uv python install 3.11
```

3. Pin the installed python version to the project.

```bash
uv python pin 3.11
```

4. Install and lock the development dependencies.

```bash
uv sync --extra dev --extra docs
```

5. Write your code.
6. Run the linter.

```bash
uv run ruff check .
```

1. Write tests for your code at `tests/` folder.
2. Run tests with coverage. Check if the code coverage is 100%.

```bash
uv run pytest --cov --cov-report=term-missing
```

9. Check if the minimum required version of Python with the updated code is `3.11`.
```bash
uv run vermin ytnoti
```

10. Update the documentation at `docs/` folder if needed.
11. Build the documentation to preview.

```bash
uv run sphinx-build -M html docs docs/build/
```

11. Open `docs/build/html/index.html` in your browser to preview the docs.
12. Make a pull request and wait for the code review!

## Report bugs using Github's issues

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/SeoulSKY/SoruSora/issues); it's that easy!

## Write bug reports with detail, background, and sample code

[This is an example](http://stackoverflow.com/q/12488905/180626) of a bug report that I think is not a bad model.

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give a sample code if you can. [This stackoverflow question](http://stackoverflow.com/q/12488905/180626) includes sample code that _anyone_ with a base R setup can run to reproduce.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

People _love_ thorough bug reports. I'm not even kidding.

## Use a Consistent Coding Style

Follow [PEP 8 Guidelines](https://peps.python.org/pep-0008/), which are standard coding style guidelines for Python

- You can try running `ruff` for style unification

If you have any questions, please don't hesitate to ask. You can contact me via [Discord](https://discord.gg/qvCdWEtqgB) or email: contact@seoulsky.dev.

## License

By contributing, you agree that your contributions will be licensed under its MIT License.

## Code of Conduct

Consider reading [Code of Conduct](https://github.com/SeoulSKY/ytnoti/blob/master/docs/CODE_OF_CONDUCT.md).
