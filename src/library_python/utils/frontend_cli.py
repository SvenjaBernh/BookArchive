import argparse
from collections.abc import Sequence
from pathlib import Path

from library_python.frontend.app import run_frontend


def _create_parser() -> argparse.ArgumentParser:
    """Create the frontend command-line argument parser.

    Returns:
        Parser for the archive path, host interface, and server port.
    """
    parser = argparse.ArgumentParser(description="View your book library in a browser.")
    parser.add_argument(
        "--archive",
        type=Path,
        help="CSV archive path (defaults to ~/books.csv)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="host interface to bind to (defaults to 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="port to serve on (defaults to 8080)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Parse frontend options and start the browser application.

    Args:
        argv: Argument strings to parse, or None to use ``sys.argv``.

    Raises:
        SystemExit: If argument parsing fails or help is requested.
    """
    args = _create_parser().parse_args(argv)
    run_frontend(args.archive, host=args.host, port=args.port)
