"""
Bangun isi email digest (HTML + teks) dari data pasar.
Dipisah dari pengiriman supaya mudah dites tanpa kirim email beneran.
"""
from __future__ import annotations
import datetime as dt

import config
from market_data import signal_for


def _fmt_usd(x: float) -> str:
    return f"${x:,.2f}"


def _fmt_pct(x: float) -> str:
    return f"{x:+.2f}%"


def build_digest(prices: dict[str, dict], usdidr: float | None) -> tuple[str, str]:
    """Kembalikan (subject, html_body)."""
    today = dt.date.today()
    subject = f"{config.EMAIL_SUBJECT_PREFIX} — Minggu {today:%d %b %Y}"

    kurs = usdidr or config.USDIDR_FALLBACK
    kurs_note = "" if usdidr else " (fallback, fetch gagal)"

    rows = []
    for nama, info in config.PORTFOLIO.items():
        tkr = info["ticker"]
        bobot = info["bobot"]
        rupiah = config.MODAL_TRANCHE * bobot
        if tkr and tkr in prices and "error" not in prices[tkr]:
            m = prices[tkr]
            harga = _fmt_usd(m["price"])
            chg1d = _fmt_pct(m["change_pct_1d"])
            chg1w = _fmt_pct(m["change_pct_1w"])
            sinyal = signal_for(tkr, m)
            catatan = config.SINYAL_RULES.get(tkr, {}).get("catatan", "")
        elif tkr:
            harga = chg1d = chg1w = "—"
            sinyal = "DATA TIDAK TERSEDIA"
            catatan = prices.get(tkr, {}).get("error", "")
        else:
            harga = chg1d = chg1w = "—"
            sinyal = "Kas — likuid, tanpa risiko harga"
            catatan = "RDPU: cair 1-2 hari, bantalan + titipan MU/AMD."

        rupiah_str = f"Rp {rupiah:,.0f}".replace(",", ".")
        rows.append(f"""
        <tr>
          <td style="padding:8px 10px;border-bottom:1px solid #e5e7eb"><b>{nama}</b><br>
            <span style="color:#6b7280;font-size:12px">{bobot*100:.1f}% · {rupiah_str}</span></td>
          <td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;text-align:right">{harga}</td>
          <td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;text-align:right">{chg1d}</td>
          <td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;text-align:right">{chg1w}</td>
          <td style="padding:8px 10px;border-bottom:1px solid #e5e7eb;font-size:12px">{sinyal}<br>
            <span style="color:#6b7280">{catatan}</span></td>
        </tr>""")

    html = f"""<!DOCTYPE html><html><body style="font-family:system-ui,Arial,sans-serif;color:#111;max-width:720px;margin:auto">
    <h2 style="margin-bottom:2px">📊 Digest Portofolio Mingguan</h2>
    <div style="color:#6b7280;font-size:13px;margin-bottom:16px">{today:%A, %d %B %Y} · Kurs USD/IDR ≈ {kurs:,.0f}{kurs_note}</div>

    <table style="width:100%;border-collapse:collapse;font-size:13px">
      <thead>
        <tr style="text-align:left;color:#6b7280;border-bottom:2px solid #e5e7eb">
          <th style="padding:8px 10px">Instrumen</th>
          <th style="padding:8px 10px;text-align:right">Harga</th>
          <th style="padding:8px 10px;text-align:right">1 Hari</th>
          <th style="padding:8px 10px;text-align:right">1 Minggu</th>
          <th style="padding:8px 10px">Sinyal & Catatan</th>
        </tr>
      </thead>
      <tbody>{''.join(rows)}</tbody>
    </table>

    <div style="background:#f9fafb;border-radius:8px;padding:12px 16px;margin-top:18px;font-size:12px;color:#6b7280">
      ⚠️ <b>Disclaimer:</b> Sinyal berbasis momentum harga sederhana, BUKAN nasihat investasi pasti.
      Politik/kebijakan (FOMC, BI, kontrol ekspor chip) adalah lapisan risiko tambahan.
      Keputusan akhir tetap di kamu. Data harga via yfinance, bisa terlambat/tidak lengkap.
    </div>
    <div style="color:#9ca3af;font-size:11px;margin-top:10px">Dikirim otomatis oleh sistem Digest-Weekly (KiroCrew).</div>
    </body></html>"""

    return subject, html


if __name__ == "__main__":
    from market_data import fetch_prices, fetch_usdidr
    tickers = [i["ticker"] for i in config.PORTFOLIO.values() if i["ticker"]]
    p = fetch_prices(tickers)
    subj, body = build_digest(p, fetch_usdidr())
    print(subj)
    print(body[:500], "...")
