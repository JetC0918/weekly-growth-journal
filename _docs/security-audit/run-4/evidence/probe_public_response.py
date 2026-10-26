"""Classify bounded unauthenticated public responses without retaining arbitrary body content."""
import hashlib
import json
import subprocess
from pathlib import Path

base = Path(__file__).parent
snapshot = json.loads((base / "github-admin.json").read_text(encoding="utf-8"))
variables = {v["name"]: v.get("value") for v in snapshot["environment_variables"]["data"]}
results = []
for name, paths in (("CLOUDFLARE_API_ORIGIN", ("/api/health/", "/api/reviews")), ("CLOUDFLARE_FRONTEND_ORIGIN", ("/",))):
    for path in paths:
        url = variables[name].rstrip("/") + path
        response = subprocess.run(["curl.exe", "--silent", "--show-error", "--max-filesize", "4096", "--max-time", "15", "--write-out", "\nAUDITSTATUS:%{http_code}", url], capture_output=True)
        body, _, status = response.stdout.rpartition(b"\nAUDITSTATUS:")
        result = {"url": url, "method": "GET", "exit": response.returncode, "status": status.decode("ascii", "replace"), "body_length": len(body), "body_sha256": hashlib.sha256(body).hexdigest(), "tls_verification_disabled": False, "arbitrary_response_content_retained": False, "error": response.stderr.decode("utf-8", "replace").strip()}
        if body.strip() in (b"Hello World!", b"Hello world!", b"Hello World", b"Hello world"):
            result["known_public_placeholder"] = body.strip().decode("ascii")
        else:
            try:
                value = json.loads(body)
                result["expected_health_json"] = value == {"status": "ok"}
                result["json_top_level_type"] = type(value).__name__
            except (ValueError, UnicodeError):
                result["expected_health_json"] = False
        results.append(result)
(base / "public-response-classification.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
print(json.dumps(results, indent=2))
