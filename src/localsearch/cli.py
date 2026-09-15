from __future__ import annotations

import argparse
import json

from localsearch.config import LocalSearchConfig
from localsearch.database.connection import DatabaseManager
from localsearch.indexing.indexer import index_directory
from localsearch.retrieval.bm25 import lexical_search
from localsearch.retrieval.hybrid import hybrid_search
from localsearch.retrieval.semantic import semantic_search


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="localsearch", description="Local-first AI search engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="initialize the local search configuration")
    init_parser.set_defaults(handler=handle_init)

    index_parser = subparsers.add_parser("index", help="index a directory")
    index_parser.add_argument("path", nargs="+", help="Directory paths to scan")
    index_parser.add_argument("--db", default="localsearch.db", help="SQLite database path")
    index_parser.set_defaults(handler=handle_index)

    search_parser = subparsers.add_parser("search", help="search indexed content")
    search_parser.add_argument("query", help="Query string")
    search_parser.add_argument("--path", action="append", default=[], help="Restrict search to a path")
    search_parser.add_argument("--type", dest="file_type", help="Restrict to an extension or file type")
    search_parser.add_argument("--mode", choices=("lexical", "semantic", "hybrid"), default="hybrid")
    search_parser.add_argument("--limit", type=int, default=10)
    search_parser.add_argument("--db", default="localsearch.db", help="SQLite database path")
    search_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    search_parser.add_argument("--no-rerank", action="store_true", help="Disable hybrid reranking")
    search_parser.set_defaults(handler=handle_search)

    stats_parser = subparsers.add_parser("stats", help="show index statistics")
    stats_parser.add_argument("--db", default="localsearch.db", help="SQLite database path")
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
    summary = index_directory(args.path, db_path=args.db, config=config)
    print(f"New: {summary['new']}")
    print(f"Updated: {summary['updated']}")
    print(f"Unchanged: {summary['unchanged']}")
    print(f"Deleted: {summary['deleted']}")
    print(f"Indexed files: {summary['indexed_files']}")
    return 0


def handle_search(args: argparse.Namespace) -> int:
    path_filter = args.path[0] if args.path else None
    common = {
        "db_path": args.db,
        "limit": args.limit,
        "file_type": args.file_type,
        "path_filter": path_filter,
    }
    if args.mode == "lexical":
        results = lexical_search(args.query, **common)
    elif args.mode == "semantic":
        results = semantic_search(args.query, **common)
    else:
        results = hybrid_search(args.query, **common, rerank=not args.no_rerank)

    if args.json:
        print(json.dumps({"query": args.query, "mode": args.mode, "results": results}, indent=2))
        return 0

    print(f"Search: {args.query}")
    print(f"Mode: {args.mode}")
    for rank, result in enumerate(results, start=1):
        print(f"\n{rank}. {result['filename']}")
        print(f"   {result['path']}")
        print(f"   Score: {result['score']:.4f}")
        print(f"   {result['snippet']}")
    return 0


def handle_stats(args: argparse.Namespace) -> int:
    database = DatabaseManager(args.db)
    print("LocalAI Search stats")
    print(f"Files: {database.get_file_count()}")
    print(f"Chunks: {database.get_chunk_count()}")
    print(f"Database: {args.db}")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
