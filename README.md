# 📊 Digest Portofolio Mingguan (via Gmail API)

Sistem otomatis yang mengirim ringkasan portofolio (SMH, MU, AMD, kas) ke email kamu
tiap minggu — lengkap dengan harga, perubahan 1 hari/1 minggu, dan sinyal beli/tahan.

## Isi folder
| File | Fungsi |
|------|--------|
| `config.py` | Semua pengaturan (email tujuan, portofolio, aturan sinyal) |
| `market_data.py` | Ambil harga terbaru via yfinance |
| `digest_builder.py` | Bangun isi email (HTML) |
| `gmail_sender.py` | OAuth + kirim email lewat Gmail API |
| `main.py` | Entry point (dipanggil cron) |
| `requirements.txt` | Dependensi Python |

---

## Langkah setup (sekali saja)

### 1. Pasang dependensi
```
cd C:\2026\Finance\Digest-Weekly
pip install -r requirements.txt
```

### 2. Buat kredensial Google (BAGIAN YANG BUTUH KAMU)
1. Buka [Google Cloud Console](https://console.cloud.google.com/).
2. Buat **Project baru** (atau pakai yang ada) — misal "Digest Portofolio".
3. Menu **APIs & Services → Library** → cari **Gmail API** → klik **Enable**.
4. Menu **APIs & Services → OAuth consent screen**:
   - Pilih **External**, isi nama app & email kamu, **Save**.
   - Di bagian **Test users**, tambahkan email Gmail kamu (yang akan mengirim).
5. Menu **APIs & Services → Credentials → Create Credentials → OAuth client ID**:
   - Application type: **Desktop app**.
   - Klik **Create** → **Download JSON**.
6. Ganti nama file itu jadi **`credentials.json`** dan taruh di folder ini
   (`C:\2026\Finance\Digest-Weekly\credentials.json`).

### 3. Isi email tujuan
Buka `config.py`, ganti:
```python
EMAIL_TO = "GANTI_DENGAN_EMAIL_KAMU@gmail.com"
```

### 4. Login pertama (buat token)
```
python main.py --auth
```
Browser terbuka → login → izinkan. File `token.json` dibuat otomatis.
Setelah ini, tidak perlu login lagi (refresh otomatis).

---

## Pemakaian
```
python main.py --preview   # lihat hasil tanpa kirim (buka preview.html)
python main.py             # kirim email digest sekarang
```

## Jadwal otomatis (cron mingguan)
Setelah setup selesai & `python main.py --preview` menghasilkan output yang benar,
minta Kiro (di KiroCrew) untuk memasang cron mingguan yang menjalankan
`python C:\2026\Finance\Digest-Weekly\main.py`.

---

## ⚠️ Keamanan
- `credentials.json` & `token.json` **rahasia** — sudah masuk `.gitignore`, jangan
  di-commit atau dibagikan.
- Scope OAuth dibatasi ke **`gmail.send`** saja: sistem ini **hanya bisa mengirim**
  email, **tidak bisa membaca** inbox kamu.
- Sinyal di digest berbasis momentum sederhana, **bukan nasihat investasi pasti**.
