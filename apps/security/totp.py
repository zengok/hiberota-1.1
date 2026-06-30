from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

TOTP_DIGITS = 6
TOTP_PERIOD_SECONDS = 30
TOTP_SECRET_BYTES = 20
TOTP_VALID_WINDOW = 1


def generate_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(TOTP_SECRET_BYTES)).decode("ascii").rstrip("=")


def build_totp_uri(*, issuer: str, account_name: str, secret: str) -> str:
    label = f"{issuer}:{account_name}"
    return (
        f"otpauth://totp/{quote(label)}"
        f"?secret={secret}&issuer={quote(issuer)}&algorithm=SHA1&digits={TOTP_DIGITS}&period={TOTP_PERIOD_SECONDS}"
    )


def verify_totp_token(
    secret: str,
    token: str,
    *,
    at_time: int | None = None,
    last_counter: int | None = None,
) -> tuple[bool, int | None]:
    normalized = "".join(token.split())
    if not normalized.isdigit() or len(normalized) != TOTP_DIGITS:
        return False, None

    timestamp = int(time.time() if at_time is None else at_time)
    current_counter = timestamp // TOTP_PERIOD_SECONDS
    for offset in range(-TOTP_VALID_WINDOW, TOTP_VALID_WINDOW + 1):
        counter = current_counter + offset
        if counter < 0 or (last_counter is not None and counter <= last_counter):
            continue
        expected = totp_token(secret, counter=counter)
        if hmac.compare_digest(expected, normalized):
            return True, counter
    return False, None


def totp_token(secret: str, *, counter: int) -> str:
    key = _decode_base32(secret)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(code % (10**TOTP_DIGITS)).zfill(TOTP_DIGITS)


def _decode_base32(secret: str) -> bytes:
    normalized = "".join(secret.upper().split())
    padding = "=" * ((8 - len(normalized) % 8) % 8)
    return base64.b32decode(normalized + padding, casefold=True)
