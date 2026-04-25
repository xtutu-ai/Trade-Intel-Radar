from __future__ import annotations

from app.pipeline import run_daily


if __name__ == "__main__":
    run_daily(send_mail=True)
