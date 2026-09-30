"""
Ambil data pasar terbaru untuk instrumen di portofolio.

Sumber data: endpoint JSON chart Yahoo Finance
  https://query1.finance.yahoo.com/v8/finance/chart/<symbol>
Ini endpoint JSON yang stabil dan sering lolos di tempat library scraping
(yfinance) atau Stooq diblokir "verify browser". Hanya pakai urllib bawaan
Python -- tanpa dependensi tambahan, tanpa API key.

Kalau host utama (query1) diblokir, otomatis coba query2 sebagai cadangan.
Semua kegagalan ditangani: ticker yang gagal diberi {"error": ...} dan digest
tetap terkirim dengan catatan (fail-safe).

Menghasilkan dict: {ticker: {"price", "change_pct_1d", "change_pct_1w"}}
"""
from __future__ import annotations
import datetime as dt
import json
import urllib.request

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
_HOSTS = ("query1.finance.yahoo.com", "query2.finance.yahoo.com")

# Simbol Yahoo untuk tiap instrumen. Kurs USD/IDR = "IDR=X" (perlu URL-encode '=').
_YAHOO_MAP = {
    "SMH": "SMH",
    "MU": "MU",
    "AMD": "AMD",
    "IDR=X": "IDR%3DX",
}


def _yahoo_closes(symbol: str, timeout: int = 15) -> list[float]:
    """Deret harga penutupan harian ~1 bulan (terbaru di akhir). [] kalau semua host gagal."""
    for host in _HOSTS:
        url = f"https://{host}/v8/finance/chart/{symbol}?range=1mo&interval=1d"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.load(resp)
            result = data.get("chart", {}).get("result")
            if not result:
                continue
            quote = result[0].get("indicators", {}).get("quote", [{}])[0]
            closes = [float(c) for c in quote.get("close", []) if c is not None]
            if closes:
                return closes
        except Exception:  # noqa: BLE001 - fetch eksternal, coba host berikutnya
            continue
    return []


def _from_series(closes: list[float]) -> dict | None:
    """Bangun metrik harga dari deret penutupan (butuh minimal 2 titik)."""
    if len(closes) < 2:
        return None
    harga_now = closes[-1]
    harga_1d = closes[-2]
    # ~1 minggu perdagangan = 5 hari bursa ke belakang (pakai yang tersedia).
    harga_1w = closes[-6] if len(closes) >= 6 else closes[0]
    return {
        "price": harga_now,
        "change_pct_1d": (harga_now / harga_1d - 1) * 100 if harga_1d else 0.0,
        "change_pct_1w": (harga_now / harga_1w - 1) * 100 if harga_1w else 0.0,
    }


def fetch_prices(tickers: list[str]) -> dict[str, dict]:
    """Ambil harga + perubahan 1 hari & 1 minggu untuk tiap ticker."""
    hasil: dict[str, dict] = {}
    for t in tickers:
        if not t:
            continue
        sym = _YAHOO_MAP.get(t, t)
        metrik = _from_series(_yahoo_closes(sym))
        hasil[t] = metrik if metrik else {"error": "tidak ada data"}
    return hasil


def fetch_usdidr() -> float | None:
    """Kurs USD/IDR terkini. None kalau gagal."""
    closes = _yahoo_closes(_YAHOO_MAP["IDR=X"])
    return closes[-1] if closes else None


def signal_for(ticker: str, m: dict) -> str:
    """Sinyal sederhana berbasis momentum mingguan. BUKAN nasihat pasti."""
    if "error" in m:
        return "DATA TIDAK TERSEDIA"
    chg = m.get("change_pct_1w", 0.0)
    if chg <= -8:
        return "⬇️ KOREKSI TAJAM — perhatikan (peluang beli bertahap / tunggu stabil)"
    if chg >= 8:
        return "⬆️ NAIK KUAT — jangan kejar (tunggu reaksi mereda)"
    return "➡️ STABIL — jalankan sesuai jadwal DCA"


if __name__ == "__main__":
    print("Tanggal:", dt.date.today())
    print(fetch_prices(["SMH", "MU", "AMD"]))
    print("USD/IDR:", fetch_usdidr())
