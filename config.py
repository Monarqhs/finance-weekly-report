"""
Konfigurasi sistem Digest Portofolio Mingguan.
Semua pengaturan yang bisa diubah user ada di sini.

CATATAN KEAMANAN:
- File kredensial (credentials.json, token.json) TIDAK boleh di-commit ke git.
- Lihat .gitignore di folder ini.
"""
from pathlib import Path
import os

# --- Folder & file ---
BASE_DIR = Path(__file__).parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"   # dari Google Cloud (kamu unduh)
TOKEN_FILE = BASE_DIR / "token.json"               # dibuat otomatis setelah login pertama

# --- Tujuan email ---
# Email penerima digest. Ganti dengan email kamu (atau set env EMAIL_TO di Actions).
EMAIL_TO = os.environ.get("EMAIL_TO", "ghalihyulio12@gmail.com")
EMAIL_SUBJECT_PREFIX = "📊 Digest Portofolio"

# --- Portofolio (alokasi OKTOBER 2026 — "opsi B" yang dikunci bersama user) ---
# Catatan: RDPU 20% khusus Oktober (amunisi koreksi), diuji ulang November.
# VOO dikurangi (penyeimbang), MU dipangkas & sebagian dialihkan ke SK Hynix (ADR)
# karena valuasi SK Hynix lebih murah (~4,8x fwd P/E vs MU ~6,6x) & pemimpin HBM.
# "grup" dipakai digest untuk mengelompokkan baris: inti-semi / penyeimbang / kas.
PORTFOLIO = {
    "ETF SMH":            {"bobot": 0.35,  "ticker": "SMH",   "grup": "Semikonduktor (inti)"},
    "Micron (MU)":        {"bobot": 0.10,  "ticker": "MU",    "grup": "Semikonduktor (inti)"},
    "SK Hynix (ADR)":     {"bobot": 0.10,  "ticker": "SKHHY", "grup": "Semikonduktor (inti)"},
    "AMD":                {"bobot": 0.075, "ticker": "AMD",   "grup": "Semikonduktor (inti)"},
    "ETF S&P 500 (VOO)":  {"bobot": 0.075, "ticker": "VOO",   "grup": "Penyeimbang"},
    "Emas":               {"bobot": 0.10,  "ticker": "GC=F",  "grup": "Penyeimbang"},
    "Kas Aman (RDPU)":    {"bobot": 0.20,  "ticker": None,    "grup": "Kas"},
}

# Modal per tranche (untuk konteks di digest)
MODAL_TRANCHE = 10_000_000
USDIDR_FALLBACK = 17_735  # dipakai kalau fetch kurs gagal

# --- Aturan sinyal (dari kalender strategi kita) ---
# Catatan statis per instrumen (konteks tesis). Sinyal BELI/TAHAN/HATI-HATI
# dihitung DINAMIS oleh market_data.signal_detail() dari SMA50/SMA200/RSI/drawdown.
SINYAL_RULES = {
    "MU":    {"catatan": "Dipangkas 15%→10% Okt; sebagian dialihkan ke SK Hynix (valuasi lebih murah). RAM langka, margin tinggi; pantau CXMT (China) — kalau ramp HBM, harga RAM bisa turun."},
    "SKHHY": {"catatan": "Posisi BARU (ADR Nasdaq USD). Pemimpin HBM (56–58%), valuasi ~4,8x fwd P/E (lebih murah dari MU). Risiko: 'Korea discount' bisa bertahan lama; siklus memori sama dengan MU."},
    "AMD":   {"catatan": "Momentum AI. Tahan sampai jadwal tranche; hindari kejar di euforia pasca-earnings."},
    "SMH":   {"catatan": "ETF inti semikonduktor (~25 emiten, kemungkinan sudah memegang SK Hynix). Eksekusi sesuai jadwal DCA."},
    "VOO":   {"catatan": "Penyeimbang (dikurangi 15%→7,5% Okt). Mahal secara valuasi tapi tren naik — beli 2 TERMIN (mgg-2 & mgg-4) untuk harga rata lebih baik."},
    "GC=F":  {"catatan": "Lindung nilai geopolitik. Sedang di rekor (mahal, bukan diskon) — beli 2 TERMIN (mgg-2 & mgg-4), simpan amunisi RDPU untuk koreksi FOMC."},
}

# --- Watchlist pantauan (DIPANTAU harganya, TANPA alokasi/bobot) ---
# SK Hynix sudah DIPROMOSIKAN jadi posisi (lihat PORTFOLIO) sejak Okt 2026,
# jadi watchlist sekarang kosong. Tambahkan emiten tema serupa di sini kalau mau.
WATCHLIST: dict = {}

# --- Pantauan Geopolitik (tesis inti: perang semikonduktor) ---
# Ditampilkan sebagai checklist di email agar monitoring mingguan tetap sadar-risiko.
GEOPOLITIK_WATCH = [
    "CXMT / YMTC (produsen memori China): tanda ramp produksi DRAM/HBM volume besar jadi sinyal harga RAM turun, waspada margin MU.",
    "ASML & kontrol ekspor EUV/DUV: pengetatan AS-Belanda menjaga kelangkaan (positif chip); pelonggaran negatif.",
    "Kebijakan AS-China: sanksi/tarif chip baru bisa menggerakkan seluruh posisi semi sekaligus.",
    "The Fed (FOMC) & BI: arah suku bunga, pelonggaran umumnya suportif saham growth/semi.",
    "Kurs USD/IDR: rupiah melemah menaikkan biaya entry aset USD (efek ke timing DCA).",
]

# --- Gmail API scope: hanya kirim (paling minim, aman) ---
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
