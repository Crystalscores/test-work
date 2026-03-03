from __future__ import annotations

import argparse
import asyncio
import json

from rich.console import Console
from rich.table import Table

from .config import load_config
from .runner import run_funnels

console = Console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Quiz Funnel Runner")
    parser.add_argument("urls", nargs="*", help="3-5 funnel URLs")
    parser.add_argument("--config", help="Path to JSON config")
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--concurrency", type=int, default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--device", default=None)
    parser.add_argument("--llm-enabled", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(
        args.config,
        urls=args.urls or None,
        max_steps=args.max_steps,
        headless=True if args.headless else None,
        concurrency=args.concurrency,
        output_dir=args.output_dir,
        device=args.device,
        llm_enabled=True if args.llm_enabled else None,
    )

    console.print(f"[cyan]Running {len(config.urls)} funnel(s) with max_steps={config.max_steps}[/cyan]")
    summaries = asyncio.run(run_funnels(config))

    table = Table(title="Execution Summary")
    for col in ["domain", "steps", "paywall_detected", "price_detected"]:
        table.add_column(col)
    for item in summaries:
        table.add_row(item["domain"], str(item["steps"]), str(item["paywall_detected"]), item["price_detected"] or "-")
    console.print(table)
    console.print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
