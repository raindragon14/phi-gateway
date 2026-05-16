"""CLI entry point for PhiGateway.

Usage:
    python -m phi_gateway          # Start server (default)
    python -m phi_gateway serve    # Start server explicitly
    python -m phi_gateway --help   # Show help
"""

import argparse
import sys

import uvicorn


def serve(args: argparse.Namespace) -> None:
    """Start the PhiGateway server."""
    uvicorn.run(
        "phi_gateway.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level.lower(),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="phi-gateway",
        description="Self-hosted AI gateway — LLM proxy, MCP tool registry, RAG, agent memory.",
    )
    sub = parser.add_subparsers(dest="command")

    serve_parser = sub.add_parser("serve", help="Start the PhiGateway server")
    serve_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Bind address (default: 0.0.0.0)",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Listen port (default: 8000)",
    )
    serve_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    serve_parser.add_argument(
        "--log-level",
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging level (default: info)",
    )

    args = parser.parse_args()

    if args.command == "serve" or args.command is None:
        serve(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
