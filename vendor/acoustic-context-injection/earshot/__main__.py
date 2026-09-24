"""Command-line entry point.

    python -m earshot                 # default: stub adapter, offline
    python -m earshot --adapter cautious-stub
    python -m earshot --adapter openai-audio --out results.txt
"""
from __future__ import annotations

import argparse
import sys

from .adapters import ADAPTERS
from .runner import format_report, run


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="earshot")
    p.add_argument("--adapter", default="stub", choices=sorted(ADAPTERS),
                   help="which model adapter to score (default: stub, offline)")
    p.add_argument("--out", default=None, help="also write the report to this file")
    args = p.parse_args(argv)

    adapter = ADAPTERS[args.adapter]()
    report = run(adapter)
    text = format_report(report, adapter.name)
    print(text)
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
