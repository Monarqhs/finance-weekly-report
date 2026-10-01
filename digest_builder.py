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


def _pct_color(x: float) -> str:
    if x > 0:
        return "#16a34a"   # hijau
    if x < 0:
        return "#dc2626"   # merah
    return "#6b7280"       # abu


def _rupiah(x: float) -> str:
    return f"Rp {x:,.0f}".replace(",", ".")


# Palet
INK = "#111827"
SUBTLE = "#6b7280"
FAINT = "#9ca3af"
LINE = "#eceff3"
CARD = "#f7f8fa"


def _watchlist_rows() -> str:
    """Baris untuk Watchlist (pantauan, tanpa posisi). Fetch harga sendiri."""
    wl = getattr(config, "WATCHLIST", {})
    if not wl:
        return ""
    from market_data import fetch_prices
    tickers = [v["ticker"] for v in wl.values() if v.get("ticker")]
    prices = fetch_prices(tickers)
    out = []
    for nama, info in wl.items():
        tkr = info.get("ticker")
        catatan = info.get("catatan", "")
        m = prices.get(tkr, {})
        simbol = info.get("mata_uang", "$")
        if m and "error" not in m:
            harga = f'<span style="font-weight:600">{simbol}{m["price"]:,.0f}</span>'
            c1d, c1w = m.get("change_pct_1d", 0.0), m.get("change_pct_1w", 0.0)
            chg1d = f'<span style="color:{_pct_color(c1d)}">{_fmt_pct(c1d)}</span>'
            chg1w = f'<span style="color:{_pct_color(c1w)}">{_fmt_pct(c1w)}</span>'
        else:
            harga = f'<span style="color:{FAINT}">n/a</span>'
            chg1d = chg1w = f'<span style="color:{FAINT}">—</span>'
        badge = (
            '<span style="display:inline-block;background:#f5f3ff;color:#6d28d9;'
            'font-weight:600;font-size:11px;padding:2px 8px;border-radius:20px">PANTAUAN</span>'
        )
        out.append(f"""
        <tr>
          <td style="padding:14px 12px;border-bottom:1px solid {LINE};vertical-align:top">
            <div style="font-weight:600;color:{INK}">{nama}</div>
            <div style="color:{SUBTLE};font-size:12px;margin-top:2px">— (tanpa posisi)</div>
          </td>
          <td style="padding:14px 12px;border-bottom:1px solid {LINE};text-align:right;white-space:nowrap;vertical-align:top">{harga}</td>
          <td style="padding:14px 12px;border-bottom:1px solid {LINE};text-align:right;white-space:nowrap;vertical-align:top">{chg1d}</td>
          <td style="padding:14px 12px;border-bottom:1px solid {LINE};text-align:right;white-space:nowrap;vertical-align:top">{chg1w}</td>
          <td style="padding:14px 12px;border-bottom:1px solid {LINE};font-size:12px;vertical-align:top">
            <div style="margin-bottom:3px">{badge}</div>
            <div style="color:{SUBTLE};line-height:1.45">{catatan}</div>
          </td>
        </tr>""")
    return "".join(out)


def build_digest(prices: dict[str, dict], usdidr: float | None) -> tuple[str, str]:
    """Kembalikan (subject, html_body)."""
    today = dt.date.today()
    subject = f"{config.EMAIL_SUBJECT_PREFIX} — Minggu {today:%d %b %Y}"

    kurs = usdidr or config.USDIDR_FALLBACK
    kurs_note = "" if usdidr else " (perkiraan)"

    rows = []
    grup_terakhir = None
    for nama, info in config.PORTFOLIO.items():
        tkr = info["ticker"]
        bobot = info["bobot"]
        grup = info.get("grup", "")
        rupiah = config.MODAL_TRANCHE * bobot
        alokasi = f"{bobot*100:.1f}% · {_rupiah(rupiah)}"

        # Sub-header grup (Semikonduktor / Penyeimbang / Kas) — hanya saat grup berganti.
        if grup and grup != grup_terakhir:
            rows.append(f"""
        <tr><td colspan="5" style="padding:16px 12px 6px;border-bottom:1px solid {LINE}">
          <span style="font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:{FAINT}">{grup}</span>
        </td></tr>""")
            grup_terakhir = grup

        if tkr and tkr in prices and "error" not in prices[tkr]:
            m = prices[tkr]
            harga_html = f'<span style="font-weight:600">{_fmt_usd(m["price"])}</span>'
            c1d, c1w = m["change_pct_1d"], m["change_pct_1w"]
            chg1d = f'<span style="color:{_pct_color(c1d)}">{_fmt_pct(c1d)}</span>'
            chg1w = f'<span style="color:{_pct_color(c1w)}">{_fmt_pct(c1w)}</span>'
            sinyal = signal_for(tkr, m)
            catatan = config.SINYAL_RULES.get(tkr, {}).get("catatan", "")
            sinyal_html = (
                f'<span style="display:inline-block;background:#eef2ff;color:#4338ca;'
                f'font-weight:600;font-size:11px;padding:2px 8px;border-radius:20px">'
                f'{sinyal}</span>'
            )
        elif tkr:
            harga_html = chg1d = chg1w = f'<span style="color:{FAINT}">—</span>'
            sinyal_html = (
                '<span style="display:inline-block;background:#fef2f2;color:#dc2626;'
                'font-weight:600;font-size:11px;padding:2px 8px;border-radius:20px">'
                'DATA TIDAK TERSEDIA</span>'
            )
            catatan = prices.get(tkr, {}).get("error", "")
        else:
            # RDPU / instrumen kas — memang tidak punya harga pasar harian.
            harga_html = f'<span style="color:{FAINT}">n/a</span>'
            chg1d = chg1w = f'<span style="color:{FAINT}">—</span>'
            sinyal_html = (
                '<span style="display:inline-block;background:#f0f9ff;color:#0369a1;'
                'font-weight:600;font-size:11px;padding:2px 8px;border-radius:20px">'
                'KAS · LIKUID</span>'
            )
            catatan = "Instrumen kas (BRI Seruni Pasar Uang III): nilai stabil, likuid. Amunisi untuk menambah posisi saat koreksi."

        rows.append(f"""
        <tr>
          <td style="padding:14px 12px;border-bottom:1px solid {LINE};vertical-align:top">
            <div style="font-weight:600;color:{INK}">{nama}</div>
            <div style="color:{SUBTLE};font-size:12px;margin-top:2px">{alokasi}</div>
          </td>
          <td style="padding:14px 12px;border-bottom:1px solid {LINE};text-align:right;white-space:nowrap;vertical-align:top">{harga_html}</td>
          <td style="padding:14px 12px;border-bottom:1px solid {LINE};text-align:right;white-space:nowrap;vertical-align:top">{chg1d}</td>
          <td style="padding:14px 12px;border-bottom:1px solid {LINE};text-align:right;white-space:nowrap;vertical-align:top">{chg1w}</td>
          <td style="padding:14px 12px;border-bottom:1px solid {LINE};font-size:12px;vertical-align:top">
            <div style="margin-bottom:3px">{sinyal_html}</div>
            <div style="color:{SUBTLE};line-height:1.45">{catatan}</div>
          </td>
        </tr>""")

    html = f"""<!DOCTYPE html><html><body style="margin:0;padding:24px 16px;background:#ffffff;font-family:system-ui,-apple-system,Segoe UI,Arial,sans-serif;color:{INK}">
  <div style="max-width:760px;margin:auto">

    <div style="margin-bottom:6px;font-size:22px;font-weight:700">📊 Digest Portofolio Mingguan</div>
    <div style="color:{SUBTLE};font-size:13px;margin-bottom:20px">
      {today:%A, %d %B %Y} &nbsp;·&nbsp; Kurs USD/IDR ≈ {kurs:,.0f}{kurs_note}
    </div>

    <table style="width:100%;border-collapse:collapse;font-size:13px">
      <thead>
        <tr style="text-align:left;color:{SUBTLE};font-size:11px;letter-spacing:.03em;text-transform:uppercase">
          <th style="padding:0 12px 8px">Instrumen</th>
          <th style="padding:0 12px 8px;text-align:right">Harga</th>
          <th style="padding:0 12px 8px;text-align:right">1 Hari</th>
          <th style="padding:0 12px 8px;text-align:right">1 Minggu</th>
          <th style="padding:0 12px 8px">Sinyal &amp; Catatan</th>
        </tr>
      </thead>
      <tbody>{''.join(rows)}</tbody>
    </table>

    <div style="margin-top:26px;margin-bottom:8px;font-size:13px;font-weight:700;color:{INK}">🔭 Watchlist Semikonduktor — Pantauan (belum ada posisi)</div>
    <table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:4px">
      <thead>
        <tr style="text-align:left;color:{SUBTLE};font-size:11px;letter-spacing:.03em;text-transform:uppercase">
          <th style="padding:0 12px 8px">Instrumen</th>
          <th style="padding:0 12px 8px;text-align:right">Harga</th>
          <th style="padding:0 12px 8px;text-align:right">1 Hari</th>
          <th style="padding:0 12px 8px;text-align:right">1 Minggu</th>
          <th style="padding:0 12px 8px">Status &amp; Catatan</th>
        </tr>
      </thead>
      <tbody>{_watchlist_rows()}</tbody>
    </table>

    <div style="margin-top:26px;margin-bottom:8px;font-size:13px;font-weight:700;color:{INK}">🌏 Pantauan Geopolitik — Perang Semikonduktor</div>
    <div style="background:{CARD};border-radius:10px;padding:6px 4px">
      <ul style="margin:0;padding:12px 18px 12px 30px;font-size:12px;color:{SUBTLE};line-height:1.6">
        {''.join(f'<li style="margin-bottom:6px">{item}</li>' for item in config.GEOPOLITIK_WATCH)}
      </ul>
    </div>

    <div style="background:{CARD};border-radius:10px;padding:14px 18px;margin-top:22px;font-size:12px;color:{SUBTLE};line-height:1.5">
      ⚠️ <b style="color:{INK}">Disclaimer:</b> Sinyal berbasis momentum harga sederhana, BUKAN nasihat investasi pasti.
      Politik/kebijakan (FOMC, BI, kontrol ekspor chip) adalah lapisan risiko tambahan.
      Keputusan akhir tetap di kamu.
    </div>

    <div style="color:{FAINT};font-size:11px;margin-top:12px;line-height:1.5">
      Data harga: Yahoo Finance (real-time, bisa terlambat beberapa menit).<br>
      Dikirim otomatis oleh sistem Digest-Weekly (KiroCrew).
    </div>

  </div>
  </body></html>"""

    return subject, html


if __name__ == "__main__":
    from market_data import fetch_prices, fetch_usdidr
    tickers = [i["ticker"] for i in config.PORTFOLIO.values() if i["ticker"]]
    p = fetch_prices(tickers)
    subj, body = build_digest(p, fetch_usdidr())
    print(subj)
    print(body[:500], "...")
