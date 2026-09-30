"""
Ambil data pasar terbaru untuk instrumen di portofolio.
Pakai yfinance (sudah dipakai di script lain di project ini).

Menghasilkan dict: {ticker: {"price": float, "change_pct_1w": float, "change_pct_1d": float}}
Kalau fetch gagal untuk satu ticker, dia dilewati (digest tetap terkirim dengan catatan).
"""
from __future__ import annotations
import datetime as dt

try:
    import yfinance as yf
except ImportError:  # pragma: no cover
    yf = None


def fetch_prices(tickers: list[str]) -> dict[str, dict]:
    """Ambil harga + perubahan 1 hari & 1 minggu untuk tiap ticker."""
    hasil: dict[str, dict] = {}
    if yf is None:
        return {t: {"error": "yfinance belum terpasang (pip install yfinance)"} for t in tickers}

    for t in tickers:
        if not t:
            continue
        try:
            data = yf.Ticker(t).history(period="7d")
            if data.empty:
                hasil[t] = {"error": "tidak ada data"}
                continue
            harga_now = float(data["Close"].iloc[-1])
            harga_1d = float(data["Close"].iloc[-2]) if len(data) >= 2 else harga_now
            harga_1w = float(data["Close"].iloc[0])
            hasil[t] = {
                "price": harga_now,
                "change_pct_1d": (harga_now / harga_1d - 1) * 100 if harga_1d else 0.0,
                "change_pct_1w": (harga_now / harga_1w - 1) * 100 if harga_1w else 0.0,
            }
        except Exception as e:  # noqa: BLE001 - fetch eksternal, jangan gagalkan seluruh digest
            hasil[t] = {"error": str(e)}
    return hasil


def fetch_usdidr() -> float | None:
    """Kurs USD/IDR terkini. None kalau gagal."""
    if yf is None:
        return None
    try:
        data = yf.Ticker("IDR=X").history(period="2d")
        if not data.empty:
            return float(data["Close"].iloc[-1])
    except Exception:  # noqa: BLE001
        pass
    return None


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
