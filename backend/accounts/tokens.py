import base64
import binascii
import hashlib
import hmac
import json
import time

from django.conf import settings


TOKEN_LIFETIME_SECONDS = 60 * 60 * 24


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def create_access_token(user_id: int | str) -> str:
    payload = _b64encode(
        json.dumps(
            {"sub": str(user_id), "exp": int(time.time()) + TOKEN_LIFETIME_SECONDS},
            separators=(",", ":"),
        ).encode("utf-8")
    )
    signature = _b64encode(
        hmac.new(settings.TOKEN_SIGNING_KEY.encode("utf-8"), payload.encode("ascii"), hashlib.sha256).digest()
    )
    return f"{payload}.{signature}"


def decode_access_token(token: str) -> str | None:
    try:
        payload_part, signature = token.split(".", maxsplit=1)
        expected = _b64encode(
            hmac.new(
                settings.TOKEN_SIGNING_KEY.encode("utf-8"),
                payload_part.encode("ascii"),
                hashlib.sha256,
            ).digest()
        )
        if not hmac.compare_digest(signature, expected):
            return None
        padded_payload = payload_part + "=" * (-len(payload_part) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded_payload.encode("ascii")))
        if int(payload["exp"]) <= int(time.time()):
            return None
        return str(payload["sub"])
    except (ValueError, KeyError, TypeError, UnicodeError, json.JSONDecodeError, binascii.Error):
        return None
