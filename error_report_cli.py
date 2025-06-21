#!/usr/bin/env python3
"""Display aggregated recent errors."""
import json

from src.core.error_reporter import generate_report


def main() -> None:
    report = generate_report()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
