"""
Entry point sistem Digest Portofolio Mingguan.

Pemakaian:
  python main.py            -> fetch data, bangun digest, KIRIM email
  python main.py --preview  -> fetch data, bangun digest, SIMPAN ke preview.html (tidak kirim)
  python main.py --auth     -> hanya lakukan alur OAuth (buat token.json), tidak kirim

Cocok dipanggil dari cron mingguan.
"""
from __future__ import annotations
import sys
from pathlib import Path

import config
from market_data import fetch_prices, fetch_usdidr
from digest_builder import build_digest


def _tickers() -> list[str]:
    return [i["ticker"] for i in config.PORTFOLIO.values() if i["ticker"]]


def run(preview: bool = False, auth_only: bool = False) -> int:
    if auth_only:
        from gmail_sender import get_service
        _, err = get_service()
        if err:
            print("❌", err)
            return 1
        print("✅ OAuth berhasil. token.json siap. Sekarang bisa kirim email.")
        return 0

    prices = fetch_prices(_tickers())
    usdidr = fetch_usdidr()
    subject, html = build_digest(prices, usdidr)

    if preview:
        out = Path(config.BASE_DIR) / "preview.html"
        out.write_text(html, encoding="utf-8")
        print(f"✅ Preview disimpan: {out}")
        print(f"   Subject: {subject}")
        return 0

    from gmail_sender import send_email
    ok, msg = send_email(subject, html)
    print(("✅ " if ok else "❌ ") + msg)
    return 0 if ok else 1


if __name__ == "__main__":
    args = set(sys.argv[1:])
    sys.exit(run(preview="--preview" in args, auth_only="--auth" in args))
