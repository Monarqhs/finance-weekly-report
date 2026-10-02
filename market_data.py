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

# Simbol Yahoo untuk tiap instrumen. '=' perlu di-URL-encode jadi '%3D'.
_YAHOO_MAP = {
    "SMH": "SMH",
    "MU": "MU",
    "AMD": "AMD",
    "VOO": "VOO",
    "GC=F": "GC%3DF",   # emas (Gold futures)
    "SKHY": "SKHY",   # SK Hynix ADR di Nasdaq GS (USD) — listing 10 Jul 2026, ~$193
    "000660.KS": "000660.KS",  # SK Hynix (Bursa Korea, KRW) — cadangan
    "IDR=X": "IDR%3DX",
}


def _yahoo_closes(symbol: str, timeout: int = 15) -> list[float]:
    """Deret harga penutupan harian ~1 tahun (terbaru di akhir). [] kalau semua host gagal.

    Range 1 tahun diperlukan agar SMA200 (rata-rata 200 hari) bisa dihitung untuk
    sinyal dinamis. Perubahan 1 hari/1 minggu tetap diambil dari ujung deret.
    """
    for host in _HOSTS:
        url = f"https://{host}/v8/finance/chart/{symbol}?range=1y&interval=1d"
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


def _sma(closes: list[float], n: int) -> float | None:
    """Rata-rata bergerak sederhana n-hari. None kalau data kurang dari n."""
    if len(closes) < n:
        return None
    return sum(closes[-n:]) / n


def _rsi(closes: list[float], period: int = 14) -> float | None:
    """Relative Strength Index (Wilder's smoothing). None kalau data kurang.

    RSI < 30 = oversold (sering peluang beli); RSI > 70 = overbought (euforia,
    hati-hati). Rentang 40-65 dianggap momentum sehat.
    """
    if len(closes) < period + 1:
        return None
    gains, losses = 0.0, 0.0
    # Rata-rata awal dari `period` perubahan pertama.
    for i in range(1, period + 1):
        delta = closes[i] - closes[i - 1]
        if delta >= 0:
            gains += delta
        else:
            losses -= delta
    avg_gain = gains / period
    avg_loss = losses / period
    # Smoothing Wilder untuk sisa deret.
    for i in range(period + 1, len(closes)):
        delta = closes[i] - closes[i - 1]
        gain = delta if delta > 0 else 0.0
        loss = -delta if delta < 0 else 0.0
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _drawdown_from_high(closes: list[float], lookback: int = 252) -> float | None:
    """Jarak harga sekarang dari puncak tertinggi `lookback` hari terakhir, dalam %.

    Negatif = di bawah puncak. Turun >10% saat tren masih utuh = kandidat
    "beli saat koreksi" (strategi amunisi RDPU).
    """
    if not closes:
        return None
    window = closes[-lookback:] if len(closes) >= lookback else closes
    puncak = max(window)
    if puncak <= 0:
        return None
    return (closes[-1] / puncak - 1) * 100


def _from_series(closes: list[float]) -> dict | None:
    """Bangun metrik harga + indikator teknikal dari deret penutupan (min. 2 titik)."""
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
        # Indikator untuk sinyal dinamis (None kalau data historis kurang).
        "sma50": _sma(closes, 50),
        "sma200": _sma(closes, 200),
        "rsi": _rsi(closes, 14),
        "drawdown": _drawdown_from_high(closes, 252),
        "n_points": len(closes),
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
    """Label sinyal ringkas (kompatibel lama). Pakai signal_detail() untuk saran dinamis."""
    return signal_detail(ticker, m)["label"]


def signal_detail(ticker: str, m: dict) -> dict:
    """Mesin skor berbasis aturan -> {label, color, saran}.

    Menggabungkan 3 dimensi (BUKAN ramalan, hanya penanda KONDISI):
      • tren    : harga vs SMA50 & SMA200 (arah struktural)
      • momentum: RSI 14 (murah / sehat / euforia jangka pendek)
      • diskon  : jarak dari puncak 52 minggu (peluang beli saat koreksi)

    Keputusan:
      🟢 BELI       -> tren naik + RSI sehat/oversold (bonus kalau sedang diskon)
      🟡 TAHAN/DCA  -> tren naik tapi RSI overbought (jangan kejar euforia)
      🔴 HATI-HATI  -> harga di bawah SMA200 (tren struktural rusak)
      ⚪ NETRAL     -> data historis kurang / sinyal campur -> DCA sesuai jadwal

    `saran` adalah kalimat DINAMIS yang berubah mengikuti kondisi terkini —
    inilah teks yang tampil di bawah tabel digest.
    """
    if "error" in m:
        return {"label": "DATA TIDAK TERSEDIA", "color": "merah", "saran": "Data harga gagal diambil minggu ini; jalankan DCA sesuai jadwal, verifikasi harga manual."}

    harga = m.get("price")
    sma50 = m.get("sma50")
    sma200 = m.get("sma200")
    rsi = m.get("rsi")
    dd = m.get("drawdown")

    # Data historis belum cukup (mis. emiten baru listing / fetch pendek).
    if harga is None or sma200 is None or rsi is None:
        chg = m.get("change_pct_1w", 0.0)
        if chg <= -8:
            return {"label": "⬇️ KOREKSI TAJAM", "color": "merah", "saran": f"Turun {chg:+.1f}% minggu ini; data tren penuh belum tersedia. Beli bertahap / tunggu stabil."}
        if chg >= 8:
            return {"label": "⬆️ NAIK KUAT", "color": "hijau", "saran": f"Naik {chg:+.1f}% minggu ini; data tren penuh belum tersedia. Jangan kejar, tunggu reda."}
        return {"label": "⚪ DATA TERBATAS", "color": "abu", "saran": "Riwayat harga belum cukup untuk hitung tren penuh; jalankan DCA sesuai jadwal."}

    tren_naik = harga > sma200 and (sma50 is None or harga > sma50)
    tren_rusak = harga < sma200
    diskon = dd is not None and dd <= -10

    # Prioritas 1: tren struktural rusak = hati-hati, apa pun momentumnya.
    if tren_rusak:
        return {
            "label": "🔴 HATI-HATI",
            "color": "merah",
            "saran": f"Harga di BAWAH SMA200 (tren jangka panjang melemah; RSI {rsi:.0f}). "
                     f"Perkecil ukuran beli / tunggu harga balik di atas SMA200 sebelum menambah agresif.",
        }

    # Prioritas 2: tren naik — bedakan berdasarkan RSI.
    if tren_naik:
        if rsi >= 70:
            return {
                "label": "🟡 TAHAN / DCA TIPIS",
                "color": "kuning",
                "saran": f"Tren naik tapi RSI {rsi:.0f} (overbought/euforia). Sudah lari kencang — "
                         f"jangan kejar; DCA tipis saja atau tunggu RSI mereda ke bawah 65.",
            }
        if rsi <= 30:
            return {
                "label": "🟢 BELI (OVERSOLD)",
                "color": "hijau",
                "saran": f"Tren utuh di atas SMA200 DAN RSI {rsi:.0f} (oversold) — "
                         f"kombinasi menarik untuk menambah posisi{' , apalagi harga ' + f'{dd:.0f}% di bawah puncak 52mg.' if diskon else '.'}",
            }
        # RSI sehat (31–69).
        bonus = f" Harga {dd:.0f}% di bawah puncak 52mg (diskon) — porsi boleh ditambah." if diskon else ""
        return {
            "label": "🟢 BELI (MOMENTUM SEHAT)",
            "color": "hijau",
            "saran": f"Tren naik di atas SMA50 & SMA200, RSI {rsi:.0f} (sehat, belum euforia). "
                     f"Boleh tambah posisi sesuai jadwal.{bonus}",
        }

    # Sisanya: di atas SMA200 tapi di bawah SMA50 (konsolidasi) = netral.
    return {
        "label": "⚪ NETRAL / DCA",
        "color": "abu",
        "saran": f"Di atas SMA200 tapi di bawah SMA50 (konsolidasi; RSI {rsi:.0f}). "
                 f"Jalankan DCA normal sesuai jadwal, tanpa menambah agresif.",
    }


if __name__ == "__main__":
    print("Tanggal:", dt.date.today())
    print(fetch_prices(["SMH", "MU", "AMD"]))
    print("USD/IDR:", fetch_usdidr())
