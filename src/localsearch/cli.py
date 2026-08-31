from __future__ import annotations

import argparse
from pathlib import Path

from localsearch.config import LocalSearchConfig
from localsearch.scanner.discovery import scan_paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="localsearch", description="Local-first AI search engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="initialize the local search configuration")
    init_parser.set_defaults(handler=handle_init)

    index_parser = subparsers.add_parser("index", help="index a directory")
    index_parser.add_argument("path", nargs="+", help="Directory paths to scan")
    index_parser.set_defaults(handler=handle_index)

    search_parser = subparsers.add_parser("search", help="search indexed content")
    search_parser.add_argument("query", help="Query string")
    search_parser.add_argument("--path", action="append", default=[], help="Restrict search to a path")
    search_parser.add_argument("--type", dest="file_type", help="Restrict to an extension or file type")
    search_parser.set_defaults(handler=handle_search)

    stats_parser = subparsers.add_parser("stats", help="show index statistics")
    stats_parser.set_defaults(handler=handle_stats)

    return parser


def handle_init(_: argparse.Namespace) -> int:
    config = LocalSearchConfig()
    print("LocalAI Search initialized")
    print(f"Default roots: {', '.join(config.root_paths)}")
    print(f"Supported extensions: {', '.join(sorted(config.supported_extensions))}")
    return 0


def handle_index(args: argparse.Namespace) -> int:
    config = LocalSearchConfig()
    files = scan_paths(args.path, config=config)
    print(f"Files discovered: {len(files)}")
    for record in files:
        print(record.path)
    return 0


def handle_search(args: argparse.Namespace) -> int:
    print(f"Search query: {args.query}")
    if args.file_type:
        print(f"Type filter: {args.file_type}")
    if args.path:
        print(f"Path filters: {', '.join(args.path)}")
    return 0


def handle_stats(_: argparse.Namespace) -> int:
    print("LocalAI Search stats")
    print("Files: 0")
    print("Chunks: 0")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
