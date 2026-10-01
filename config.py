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

# --- Portofolio (alokasi target — strategi Rp60jt overweight-semi + penyeimbang) ---
# Komposisi AKHIR target (akumulasi Okt–Jan): semi ~60% · penyeimbang ~25% · kas ~15%.
# "grup" dipakai digest untuk mengelompokkan baris: inti-semi / penyeimbang / kas.
PORTFOLIO = {
    "ETF SMH":            {"bobot": 0.35,  "ticker": "SMH", "grup": "Semikonduktor (inti)"},
    "Micron (MU)":        {"bobot": 0.15,  "ticker": "MU",  "grup": "Semikonduktor (inti)"},
    "AMD":                {"bobot": 0.10,  "ticker": "AMD", "grup": "Semikonduktor (inti)"},
    "ETF S&P 500 (VOO)":  {"bobot": 0.15,  "ticker": "VOO", "grup": "Penyeimbang"},
    "Emas":               {"bobot": 0.10,  "ticker": "GC=F","grup": "Penyeimbang"},
    "Kas Aman (RDPU)":    {"bobot": 0.15,  "ticker": None,  "grup": "Kas"},
}

# Modal per tranche (untuk konteks di digest)
MODAL_TRANCHE = 10_000_000
USDIDR_FALLBACK = 17_735  # dipakai kalau fetch kurs gagal

# --- Aturan sinyal (dari kalender strategi kita) ---
# ambang sederhana untuk sinyal beli/tahan pada tiap instrumen
SINYAL_RULES = {
    "MU":   {"catatan": "RAM lagi langka, margin tinggi. Pantau produsen memori China (CXMT): kalau ramp HBM, harga RAM bisa turun dan menekan margin MU."},
    "AMD":  {"catatan": "Momentum AI. Tahan sampai jadwal tranche; hindari kejar di euforia pasca-earnings."},
    "SMH":  {"catatan": "ETF inti semikonduktor (~25 emiten). Eksekusi sesuai jadwal DCA, tak perlu tunggu event tunggal."},
    "VOO":  {"catatan": "Penyeimbang: 500 perusahaan AS, meredam risiko konsentrasi sektor chip."},
    "GC=F": {"catatan": "Lindung nilai: cenderung naik saat tensi geopolitik AS–China memanas."},
}

# --- Watchlist pantauan (DIPANTAU harganya, TANPA alokasi/bobot) ---
# Perusahaan tema serupa yang ingin kita awasi tanpa wajib beli.
WATCHLIST = {
    "SK Hynix": {"ticker": "000660.KS", "mata_uang": "₩", "catatan": "Pesaing langsung MU di DRAM/HBM — ikut siklus memori yang sama. Listing di Bursa Korea, harga dalam Won (KRW)."},
}

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
