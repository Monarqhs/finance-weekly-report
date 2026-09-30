"""
Kirim email via Gmail API dengan OAuth2.

Alur OAuth (sekali saja):
  1. Kamu unduh credentials.json dari Google Cloud (OAuth Client ID, tipe Desktop).
  2. Jalankan pertama kali -> browser terbuka -> login & izinkan.
  3. token.json dibuat otomatis & dipakai ulang. Refresh otomatis kalau kadaluarsa.

Scope: gmail.send saja (paling minim — cuma bisa KIRIM, tidak baca inbox kamu).
"""
from __future__ import annotations
import base64
import json
import os
from email.mime.text import MIMEText

import config

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    _GOOGLE_OK = True
except ImportError:  # pragma: no cover
    _GOOGLE_OK = False


def _missing_deps_msg() -> str:
    return (
        "Library Google belum terpasang. Jalankan:\n"
        "  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
    )


def _load_token_creds():
    """Ambil kredensial token dari env var (GitHub Secrets) atau file lokal."""
    env_token = os.environ.get("GMAIL_TOKEN_JSON")
    if env_token:
        return Credentials.from_authorized_user_info(
            json.loads(env_token), config.GMAIL_SCOPES
        )
    if config.TOKEN_FILE.exists():
        return Credentials.from_authorized_user_file(
            str(config.TOKEN_FILE), config.GMAIL_SCOPES
        )
    return None


def get_service():
    """Bangun service Gmail API terautentikasi. Return None + pesan kalau belum siap.

    Mode:
    - HEADLESS (server/GitHub Actions): baca token dari env GMAIL_TOKEN_JSON.
      Tidak pernah membuka browser; kalau token invalid -> error jelas.
    - LOKAL (laptop): baca token.json; kalau belum ada -> alur browser sekali
      pakai credentials.json.
    """
    if not _GOOGLE_OK:
        return None, _missing_deps_msg()

    headless = bool(os.environ.get("GMAIL_TOKEN_JSON"))
    creds = _load_token_creds()

    if creds and creds.valid:
        return build("gmail", "v1", credentials=creds), None

    # perlu refresh atau login baru
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif headless:
        return None, (
            "Token headless (GMAIL_TOKEN_JSON) tidak valid & tak bisa di-refresh. "
            "Perbarui secret GMAIL_TOKEN_JSON dengan token.json yang baru dari laptop."
        )
    else:
        if not config.CREDENTIALS_FILE.exists():
            return None, (
                f"credentials.json belum ada di {config.CREDENTIALS_FILE}.\n"
                "Unduh dari Google Cloud Console (OAuth Client ID -> Desktop app)."
            )
        flow = InstalledAppFlow.from_client_secrets_file(
            str(config.CREDENTIALS_FILE), config.GMAIL_SCOPES
        )
        creds = flow.run_local_server(port=0)

    # simpan token yang diperbarui HANYA di mode lokal (server itu read-only)
    if not headless:
        config.TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds), None


def send_email(subject: str, html_body: str, to: str | None = None) -> tuple[bool, str]:
    """Kirim satu email HTML. Return (sukses, pesan)."""
    to = to or config.EMAIL_TO
    if "GANTI_DENGAN_EMAIL" in to:
        return False, "EMAIL_TO belum diisi di config.py."

    service, err = get_service()
    if err:
        return False, err

    msg = MIMEText(html_body, "html", "utf-8")
    msg["To"] = to
    msg["Subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    try:
        sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return True, f"Terkirim ke {to} (id: {sent.get('id')})"
    except Exception as e:  # noqa: BLE001
        return False, f"Gagal kirim: {e}"
