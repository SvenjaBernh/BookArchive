# Library Python

Library Python is a small book-library project with both a command-line interface and a browser-based web interface. Both use the same CSV archive to add and view books.

## Installation

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.10 or newer. From the project directory, install the project and its dependencies with:

```console
uv sync
```

## Archive location

By default, the archive is `books.csv` in your home directory (`~/books.csv` on macOS and Linux; `%USERPROFILE%\books.csv` on Windows). It is created when you first add a book. Both interfaces can use a different archive path.

## Web Interface

Start the web interface with:

```console
uv run library-python-gui
```

Then open `http://127.0.0.1:8080`. The web interface displays the archive and lets you add a book with an optional rating and comment. To select another archive or server address, use `uv run library-python-gui --help`.

## CLI

Start the CLI with `uv run library-python`. Its `--help` output explains the command syntax and includes usage examples. For a detailed guide to adding, listing, finding, and updating books, see the [CLI documentation](docs/cli.md).

Use `uv run library-python-gui --help` for web-interface options, including choosing a different archive with `--archive PATH`.

## Development

The project uses Python 3.10 or newer and [uv](https://docs.astral.sh/uv/) for environment and dependency management. Set up the development environment with:

```console
uv sync --group dev
```

### Standards and tools

- **Project layout:** backend models and archive persistence live under `src/library_python/backend/`; CLI entry points live under `src/library_python/utils/`; NiceGUI web-interface code lives under `src/library_python/frontend/`.
- **Formatting and linting:** [Ruff](https://docs.astral.sh/ruff/) is the project's formatter and linter. Run both checks with:

  ```console
  uv run ruff format --check src tests
  uv run ruff check src tests
  ```

- **Tests:** backend tests use pytest and temporary archive files. Run them with
  `uv run pytest`.
- **Documentation:** public APIs and non-obvious behavior use Google-style docstrings.
- **Typing:** functions and public APIs use Python type annotations.
