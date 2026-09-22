"""One bounded direct HTTPS request per worker; no SDK retries or redirects.

The parent kills this worker on its wall-clock deadline. A timed-out request
may still be processed/billed by the provider. Request body enters via stdin.
"""
from __future__ import annotations
import http.client
import json
import os
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

HOST = "api.typesafe.ai"
PATH = "/v1/systemone"
MAX_RESPONSE = 65536

def retry_delay(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            return max(0.0, (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds())
        except (ValueError, TypeError, OverflowError):
            return None

def main() -> None:
    result = {"ok": False, "reason": "network_error"}
    conn = None
    try:
        body = sys.stdin.buffer.read(64001)
        key = os.environ.get("TYPESAFE_API_KEY", "")
        if len(body) > 64000 or not key:
            result = {"ok": False, "reason": "invalid_transport_input"}
        else:
            conn = http.client.HTTPSConnection(HOST, timeout=8)
            conn.request("POST", PATH, body=body, headers={"Authorization": "Bearer " + key,
                         "Content-Type": "application/json", "Accept": "application/json",
                         "User-Agent": "codex-jev-workflow/0.1.0"})
            response = conn.getresponse()
            if response.status != 200:
                delay = retry_delay(response.getheader("Retry-After"))
                # Do not log/return provider error bodies or follow redirects.
                result = {"ok": False, "reason": "http_error", "http_status": response.status,
                          "retry_after_seconds": delay if delay is None or delay < 86400 else 86400}
            else:
                data = response.read(MAX_RESPONSE + 1)
                if len(data) > MAX_RESPONSE:
                    result = {"ok": False, "reason": "response_too_large"}
                else:
                    try:
                        raw = json.loads(data, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
                        result = {"ok": True, "response": raw}
                    except (ValueError, UnicodeError):
                        result = {"ok": False, "reason": "invalid_response_json"}
    except Exception:
        # Exception text can contain credentials, content, or remote-controlled text.
        result = {"ok": False, "reason": "network_error"}
    finally:
        if conn is not None:
            conn.close()
    print(json.dumps(result, ensure_ascii=True, allow_nan=False))

if __name__ == "__main__":
    main()
