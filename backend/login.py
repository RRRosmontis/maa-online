#!/usr/bin/env python3
"""Bootstrap a NetEase Cloud Game token without blocking the API server."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent
TOKEN_FILE = Path(os.getenv("MAA_ONLINE_TOKEN_FILE", str(BASE_DIR / "token")))
PENDING_FILE = Path(os.getenv("MAA_ONLINE_PENDING_LOGIN_FILE", str(BASE_DIR / ".pending-login")))
API_BASE = "https://n.cg.163.com/api/v1"


def write_private(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(path, flags, 0o600)
    try:
        os.write(fd, value.encode("utf-8"))
    finally:
        os.close(fd)
    os.chmod(path, 0o600)


def normalize_phone(phone: str, country_code: str) -> tuple[str, str]:
    phone = phone.strip().replace(" ", "")
    country_code = country_code.strip().lstrip("+")
    if not phone.isdigit() or not country_code.isdigit():
        raise ValueError("phone and country code must contain digits only")
    return country_code, phone


def request_code(phone: str, country_code: str) -> None:
    country_code, phone = normalize_phone(phone, country_code)
    response = requests.post(
        f"{API_BASE}/phone-captchas/{country_code}-{phone}",
        timeout=15,
    )
    response.raise_for_status()
    write_private(PENDING_FILE, json.dumps({"country_code": country_code, "phone": phone}))
    print("SMS code requested. Run: python login.py verify <code>")


def verify_code(code: str) -> None:
    if not PENDING_FILE.is_file():
        raise RuntimeError("no pending login; run the request command first")
    pending = json.loads(PENDING_FILE.read_text(encoding="utf-8"))
    code = code.strip()
    if not code:
        raise ValueError("verification code must not be empty")

    payload = {
        "auth_method": "phone-captcha",
        "ctcode": pending["country_code"],
        "phone": pending["phone"],
        "captcha": code,
        "device_info": {
            "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36",
            "appVersion": "5.0 (X11)",
            "codecs": ["h264", "vp8", "vp9"],
        },
    }
    response = requests.post(f"{API_BASE}/tokens", json=payload, timeout=15)
    response.raise_for_status()
    token = response.json().get("token")
    if not token:
        raise RuntimeError("login response did not contain a token")

    write_private(TOKEN_FILE, token)
    PENDING_FILE.unlink(missing_ok=True)
    print(f"Login token saved securely to {TOKEN_FILE}")


def status() -> None:
    if TOKEN_FILE.is_file() and TOKEN_FILE.stat().st_size:
        print(f"token: present ({oct(TOKEN_FILE.stat().st_mode & 0o777)})")
    else:
        print("token: missing")
    print(f"pending login: {'yes' if PENDING_FILE.is_file() else 'no'}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    request_parser = sub.add_parser("request", help="request an SMS verification code")
    request_parser.add_argument("phone")
    request_parser.add_argument("--country-code", default="86")
    verify_parser = sub.add_parser("verify", help="exchange an SMS code for a token")
    verify_parser.add_argument("code")
    sub.add_parser("status", help="show credential state without revealing secrets")
    args = parser.parse_args()

    if args.command == "request":
        request_code(args.phone, args.country_code)
    elif args.command == "verify":
        verify_code(args.code)
    else:
        status()


if __name__ == "__main__":
    main()
