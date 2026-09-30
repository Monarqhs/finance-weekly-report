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

# --- Portofolio (alokasi target sesuai plan DCA Okt-Feb) ---
# bobot mengikuti aturan kita: 40% aman / 35% ETF / 12.5% MU / 12.5% AMD
PORTFOLIO = {
    "Kas Aman (RDPU)": {"bobot": 0.40,  "ticker": None},
    "ETF SMH":         {"bobot": 0.35,  "ticker": "SMH"},
    "Micron (MU)":     {"bobot": 0.125, "ticker": "MU"},
    "AMD":             {"bobot": 0.125, "ticker": "AMD"},
}

# Modal per tranche (untuk konteks di digest)
MODAL_TRANCHE = 10_000_000
USDIDR_FALLBACK = 17_735  # dipakai kalau fetch kurs gagal

# --- Aturan sinyal (dari kalender strategi kita) ---
# ambang sederhana untuk sinyal beli/tahan pada saham satelit
SINYAL_RULES = {
    "MU":  {"catatan": "Tunggu reaksi pasca-earnings 1-2 hari sebelum beli. Tranche ~30 Okt (setelah FOMC)."},
    "AMD": {"catatan": "Event earnings akhir Okt. Tahan sampai jadwal tranche."},
    "SMH": {"catatan": "ETF inti - eksekusi sesuai jadwal DCA, tidak perlu tunggu event tunggal."},
}

# --- Gmail API scope: hanya kirim (paling minim, aman) ---
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
