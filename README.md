# 📊 Digest Portofolio Mingguan (via Gmail API)

Sistem otomatis yang mengirim ringkasan portofolio (lihat `PORTFOLIO` di `config.py`)
ke email kamu tiap minggu — lengkap dengan harga, perubahan 1 hari/1 minggu, dan
sinyal dinamis (BELI/TAHAN/HATI-HATI) dari indikator teknikal (SMA50/SMA200, RSI-14,
jarak dari puncak 52 minggu).

## Isi folder
| File | Fungsi |
|------|--------|
| `config.py` | Semua pengaturan (email tujuan, portofolio, aturan sinyal) |
| `market_data.py` | Ambil harga + indikator dari Yahoo Finance (urllib bawaan, tanpa dependensi) |
| `digest_builder.py` | Bangun isi email (HTML) |
| `gmail_sender.py` | OAuth + kirim email lewat Gmail API |
| `main.py` | Entry point (dipanggil cron / GitHub Actions) |
| `requirements.txt` | Dependensi Python (hanya library Google untuk Gmail API) |

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

## Jadwal otomatis (GitHub Actions)
Pengiriman mingguan dijalankan oleh GitHub Actions (`.github/workflows/digest.yml`),
bukan cron di laptop. Jadwalnya tiap Senin 07:00 WIB (00:00 UTC). Dua secret wajib
diisi di `Settings → Secrets and variables → Actions`:

- `GMAIL_TOKEN_JSON` — seluruh isi `token.json` (hasil `python main.py --auth`).
- `EMAIL_TO` — email tujuan digest.

Jalankan manual kapan saja lewat tab **Actions → Digest Portofolio Mingguan →
Run workflow**.

---

## 🔧 Troubleshooting

### Error `invalid_grant: Token has been expired or revoked`
Refresh token Google sudah tidak berlaku. Penyebab paling umum: **OAuth consent
screen masih mode "Testing"**, di mana Google otomatis mencabut refresh token
**setiap 7 hari**.

- **Perbaikan permanen:** Google Cloud Console → **OAuth consent screen / Audience**
  → ubah Publishing status dari *Testing* ke **In production** (Publish app). Karena
  scope hanya `gmail.send` dan user cuma kamu, verifikasi Google umumnya tak perlu.
- **Buat ulang token:** di laptop, **hapus `token.json` lama dulu**, lalu
  `python main.py --auth` (kalau token lama tidak dihapus, alur login baru bisa
  terhalang). Browser terbuka → login → Allow → `token.json` baru dibuat.
- **Perbarui GitHub Secret:** copy seluruh isi `token.json` baru → `Settings →
  Secrets and variables → Actions → GMAIL_TOKEN_JSON → Update`.

### Error `missing fields client_secret, client_id, refresh_token`
Isi secret `GMAIL_TOKEN_JSON` salah file. Jangan tempel `credentials.json`
(yang berbentuk `{"installed":{...}}`) — itu identitas aplikasi untuk LOGIN.
Yang benar adalah **`token.json`** (hasil `--auth`), yang punya field
`"refresh_token"` di level teratas (tanpa pembungkus `"installed"`).

| File | Ciri isi | Dipakai untuk |
|------|----------|---------------|
| `credentials.json` | `{"installed":{...}}`, ada `client_secret`, `redirect_uris` | input LOGIN (jangan dimasukkan ke Secret) |
| `token.json` | ada `"refresh_token"` di level atas | isi Secret `GMAIL_TOKEN_JSON` ✅ |

## ⚠️ Keamanan
- `credentials.json` & `token.json` **rahasia** — sudah masuk `.gitignore`, jangan
  di-commit atau dibagikan.
- Scope OAuth dibatasi ke **`gmail.send`** saja: sistem ini **hanya bisa mengirim**
  email, **tidak bisa membaca** inbox kamu.
- Sinyal di digest berbasis momentum sederhana, **bukan nasihat investasi pasti**.
