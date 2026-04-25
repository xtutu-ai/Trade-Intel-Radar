from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.pipeline import run_daily


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Trade-Intel-Radar daily pipeline")
    parser.add_argument("--no-mail", action="store_true", help="Generate report but do not send email")
    parser.add_argument("--dry-run", action="store_true", help="Alias for --no-mail")
    args = parser.parse_args()
    html_path = run_daily(send_mail=not (args.no_mail or args.dry_run), dry_run=args.dry_run)
    print(f"report generated: {html_path}")


if __name__ == "__main__":
    main()
